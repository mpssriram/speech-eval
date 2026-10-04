"""Deterministic transcript triage and independent CPU ASR corroboration."""

from __future__ import annotations

import csv
import difflib
import hashlib
import html
import json
import logging
import os
import re
import subprocess
import tempfile
import urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import cmudict
import yaml
from rapidfuzz import fuzz
from rapidfuzz.distance import Levenshtein

from speecheval.transcripts import (
    _asr_tokens, _body_text, _escape_table, _tokens_with_spans,
    build_transcript_diffs, normalize_tokens,
)

LOGGER = logging.getLogger(__name__)
VERSIONS = ("bliss", "nicolay", "hay", "everett", "bancroft")
GETTYSBURG_URL = "https://www.abrahamlincolnonline.org/lincoln/speeches/gettysburg.htm"


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"p", "br"}:
            self.parts.append("\n\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def parse_gettysburg_versions(page: str) -> dict[str, str]:
    """Extract the five public-domain speech texts, excluding page commentary."""
    headings = list(re.finditer(
        r"<b\b[^>]*>\s*(?:<font\b[^>]*>\s*)?(Bliss|Nicolay|Hay|Everett|Bancroft) Copy\s*</b>",
        page, re.IGNORECASE,
    ))
    result: dict[str, str] = {}
    for index, heading in enumerate(headings):
        stop = headings[index + 1].start() if index + 1 < len(headings) else len(page)
        section = page[heading.end():stop]
        speech = re.search(
            r"<b\b[^>]*>\s*(?:<font\b[^>]*>\s*)?Four score.*?</b>",
            section, re.IGNORECASE | re.DOTALL,
        )
        if speech is None:
            raise ValueError(f"Speech block missing for {heading.group(1)}")
        parser = _TextParser()
        parser.feed(speech.group(0))
        paragraphs = [" ".join(p.split()) for p in "".join(parser.parts).split("\n\n")]
        text = "\n\n".join(p for p in paragraphs if p)
        end = re.search(r"shall not\s+perish from the earth\.", text, re.IGNORECASE)
        if end is None:
            raise ValueError("Manuscript ending is missing")
        result[heading.group(1).lower()] = text[:end.end()]
    if set(result) != set(VERSIONS):
        raise ValueError("Expected all five Gettysburg manuscripts")
    return result


def fetch_versions(root: Path) -> dict[str, str]:
    """Fetch and freeze the five manuscripts once, with source attribution."""
    directory = root / "data/transcripts/canonical/gettysburg_versions"
    directory.mkdir(parents=True, exist_ok=True)
    if not all((directory / f"{name}.txt").exists() for name in VERSIONS):
        request = urllib.request.Request(GETTYSBURG_URL, headers={"User-Agent": "speech-eval/0.1"})
        with urllib.request.urlopen(request, timeout=60) as response:
            page = response.read().decode("utf-8", errors="replace")
        versions = parse_gettysburg_versions(page)
        for name, text in versions.items():
            (directory / f"{name}.txt").write_text(
                f"# source: {GETTYSBURG_URL}\n{text}\n", encoding="utf-8", newline="\n"
            )
    return {name: (directory / f"{name}.txt").read_text(encoding="utf-8") for name in VERSIONS}


def select_version(scores: dict[str, int]) -> str:
    """Choose minimum token edit distance, retaining Bliss below a three-token gain."""
    best = min(scores, key=lambda name: (scores[name], VERSIONS.index(name)))
    return best if scores["bliss"] - scores[best] >= 3 else "bliss"


def equivalent_text(text: str, config: dict[str, Any]) -> str:
    """Canonicalize only configured spelling, punctuation and numeric equivalences."""
    text = text.lower()
    for apostrophe in config.get("apostrophes", []):
        text = text.replace(apostrophe, "'")
    # Commas within a numeral are grouping separators, not word boundaries.
    text = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", text)
    replacements = {**config.get("aliases", {}), **config.get("contractions", {})}
    for source in sorted(replacements, key=lambda word: (-len(word), word)):
        text = re.sub(r"(?<![a-z'])" + re.escape(source) + r"(?![a-z'])", replacements[source], text)
    if config.get("numbers_to_words", True):
        tokens = normalize_tokens(text)
    else:
        tokens = re.findall(r"[a-z0-9]+", text)
    return "".join(tokens) if config.get("compound_splits", False) else " ".join(tokens)


def classify_edit(
    kind: str,
    transcript: str,
    asr: str,
    equivalents: dict[str, Any],
    pronunciations: dict[str, list[list[str]]],
) -> str:
    """Classify an edit as IGNORE, LIKELY_ASR or LISTEN before corroboration."""
    if equivalent_text(transcript, equivalents) == equivalent_text(asr, equivalents):
        return "IGNORE"
    left, right = normalize_tokens(transcript), normalize_tokens(asr)
    if kind == "replace" and len(left) == len(right) == 1:
        if fuzz.ratio(left[0], right[0]) >= 80:
            return "LIKELY_ASR"
        for lp in pronunciations.get(left[0], []):
            for rp in pronunciations.get(right[0], []):
                if Levenshtein.distance(lp, rp) <= 1:
                    return "LIKELY_ASR"
    return "LISTEN"


def edit_groups(text: str, words: list[dict[str, Any]], start: float, end: float) -> list[dict[str, Any]]:
    """Build edits retaining original orthography and full span times in clip seconds."""
    tokens, spans = _tokens_with_spans(text)
    asr, starts, indices = _asr_tokens(words, start, end)
    result: list[dict[str, Any]] = []
    for kind, i1, i2, j1, j2 in difflib.SequenceMatcher(None, tokens, asr, autojunk=False).get_opcodes():
        if kind == "equal":
            continue
        transcript = text[spans[i1][0]:spans[i2 - 1][1]] if i2 > i1 else ""
        asr_text = " ".join(str(words[index]["word"]) for index in dict.fromkeys(indices[j1:j2]))
        point = starts[min(j1, len(starts) - 1)] if starts else 0.0
        last = float(words[indices[j2 - 1]]["end"]) - start if j2 > j1 else point
        result.append({
            "kind": kind, "transcript": transcript, "asr": asr_text,
            "start_s": round(point, 3), "end_s": round(max(point, min(end - start, last)), 3),
            "token_start": j1, "token_end": j2,
            "transcript_start": spans[i1][0] if i1 < len(spans) else len(text),
            "transcript_end": spans[i2 - 1][1] if i2 > i1 else (spans[i1][0] if i1 < len(spans) else len(text)),
        })
    return result


def _primary_context(words: list[dict[str, Any]], cut_start: float, start: float, end: float) -> str:
    return " ".join(str(word["word"]) for word in words
                    if start <= (float(word["start"]) + float(word["end"])) / 2 - cut_start < end)


class SecondaryASR:
    """Lazy, independently decoded WhisperX medium.en CPU model, beam size five."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.model: Any = None

    def transcribe(self, audio: Path, start: float, end: float) -> str:
        from speecheval.prepare import _import_whisperx

        if self.model is None:
            cache = self.root / "data/.cache"
            os.environ.setdefault("HF_HOME", str(cache / "huggingface"))
            os.environ.setdefault("TORCH_HOME", str(cache / "torch"))
            whisperx = _import_whisperx()
            self.model = whisperx.load_model(
                "medium.en", "cpu", compute_type="int8", language="en",
                asr_options={"beam_size": 5, "temperatures": [0.0]},
                vad_method="silero", download_root=str(cache / "whisperx"),
                threads=4,
            )
        with tempfile.TemporaryDirectory(prefix="triage-", dir=self.root / "data/review") as temporary:
            clip = Path(temporary) / "clip.wav"
            subprocess.run([
                "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                "-ss", f"{start:.3f}", "-i", str(audio), "-t", f"{end - start:.3f}",
                "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(clip),
            ], check=True)
            result = self.model.transcribe(str(clip), batch_size=1, language="en")
        return " ".join(segment["text"].strip() for segment in result.get("segments", []))


def write_review_html(path: Path, items: list[dict[str, Any]]) -> None:
    """Write a static local audio review table; playback times are in seconds."""
    rows: list[str] = []
    for item in items:
        rid = html.escape(item["recording_id"], quote=True)
        start = max(0.0, item["start_s"] - 1.5)
        end = item["start_s"] + 2.5
        decision = html.escape(str(item.get("decision", "")))
        decision_cell = (
            decision if decision else '<input aria-label="Review decision" placeholder="Record decision in the Markdown report">'
        )
        rows.append(
            f'<tr><td>{rid}<br>{item["start_s"]:.3f}s</td>'
            f'<td><audio controls preload="none" data-start="{start:.3f}" data-end="{end:.3f}" '
            f'src="../audio/hq/{rid}.wav#t={start:.3f},{end:.3f}"></audio>'
            '<button type="button" class="replay">Play review window</button></td>'
            f'<td>{html.escape(item["transcript"]) or "&mdash;"}</td>'
            f'<td>{html.escape(item["asr"]) or "&mdash;"}</td><td>{item["class"]}</td>'
            f'<td>{decision_cell}</td></tr>'
        )
    verification_notice = (
        '<p><strong>Automatic acoustic verification; no human review.</strong> Decisions are CTC model preferences. UNSURE remains unresolved. See reports/day01_acoustic_verification.md for both scores and the threshold distribution.</p>'
        if any("decision" in item for item in items) else ""
    )
    page = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Day 1 transcript review</title>
<style>body{font:16px system-ui;margin:24px;color:#18212b}table{border-collapse:collapse;width:100%}td,th{padding:12px;border:1px solid #ccd3da;text-align:left}audio{width:250px}button{display:block;margin-top:8px}input{min-width:180px}thead{background:#edf2f6}</style>
</head><body><h1>Day 1 transcript review</h1>
''' + verification_notice + '''
<p>Review windows play from the listed time minus 1.5 seconds to plus 2.5 seconds. Times refer to prepared WAVs. LIKELY_REAL means two ASRs agree; it still needs your decision. Input notes here are temporary: save decisions in reports/day01_listen_list.md, edit the as-spoken transcript only for real differences, then add # reviewed: yes.</p>
<table><thead><tr><th>Recording / time</th><th>Audio</th><th>Transcript says</th><th>ASR says</th><th>Class</th><th>Decision</th></tr></thead><tbody>
''' + "\n".join(rows) + '''
</tbody></table><script>
for (const audio of document.querySelectorAll('audio')) {
  const start = Number(audio.dataset.start), end = Number(audio.dataset.end);
  const stop = () => { if (audio.currentTime >= end) audio.pause(); };
  audio.addEventListener('play', () => {
    for (const other of document.querySelectorAll('audio')) if (other !== audio) other.pause();
    if (audio.currentTime < start || audio.currentTime >= end) audio.currentTime = start;
  });
  audio.addEventListener('timeupdate', stop);
  audio.addEventListener('seeking', () => {
    if (audio.currentTime < start) audio.currentTime = start;
    if (audio.currentTime > end) audio.currentTime = end;
  });
  audio.closest('td').querySelector('button').addEventListener('click', () => {
    audio.currentTime = start;
    audio.play().catch(() => {});
  });
}
</script></body></html>
'''
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(page, encoding="utf-8", newline="\n")


def triage_transcripts(root: Path | None = None) -> dict[str, Any]:
    """Select Gettysburg versions, triage edits and freeze human-review artefacts."""
    root = (root or Path.cwd()).resolve()
    config = yaml.safe_load((root / "configs/default.yaml").read_text(encoding="utf-8"))
    equivalents = yaml.safe_load((root / "configs/text_equiv.yaml").read_text(encoding="utf-8"))
    versions = fetch_versions(root)
    pronunciations = cmudict.dict()
    with (root / "data/manifest/recordings.csv").open(encoding="utf-8", newline="") as handle:
        recordings = list(csv.DictReader(handle))
    version_path = root / "data/manifest/transcript_versions.yaml"
    previous_choices = yaml.safe_load(version_path.read_text(encoding="utf-8")) if version_path.exists() else {}
    choices: dict[str, Any] = {}
    review_dir = root / "data/review"
    review_dir.mkdir(parents=True, exist_ok=True)
    secondary = SecondaryASR(root)
    cache_path = review_dir / "secondary_asr.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    items: list[dict[str, Any]] = []

    # Build missing drafts without overwriting existing human edits.
    build_transcript_diffs(root)
    for row in recordings:
        rid = row["recording_id"]
        words = json.loads((root / config["paths"]["alignment"] / "asr" / f"{rid}.json").read_text(encoding="utf-8"))["words"]
        start, end = float(row["cut_start_s"]), float(row["cut_end_s"])
        spoken_path = root / config["paths"]["transcripts_as_spoken"] / f"{rid}.txt"
        spoken = spoken_path.read_text(encoding="utf-8")
        reviewed = bool(re.search(r"^#\s*reviewed:\s*yes\s*$", spoken, re.IGNORECASE | re.MULTILINE))
        if row["text_id"] == "gettysburg":
            asr_tokens, _, _ = _asr_tokens(words, start, end)
            scores = {name: Levenshtein.distance(normalize_tokens(_body_text(text)), asr_tokens) for name, text in versions.items()}
            chosen = select_version(scores)
            if not reviewed and chosen != "bliss":
                spoken_path.write_text(versions[chosen], encoding="utf-8", newline="\n")
                spoken = versions[chosen]
            previous = (previous_choices or {}).get(rid, {})
            applied = previous.get("applied_version", "bliss")
            if not reviewed and chosen != "bliss":
                applied = chosen
            choices[rid] = {
                "selected_version": chosen, "applied_version": applied,
                "token_edit_distances": scores, "improvement_over_bliss": scores["bliss"] - scores[chosen],
                "reviewed_preserved": reviewed,
            }
            LOGGER.info("%s: %s (Bliss %d, selected %d)", rid, chosen, scores["bliss"], scores[chosen])
        audio = root / config["paths"]["hq"] / f"{rid}.wav"
        audio_hash: str | None = None
        groups = edit_groups(_body_text(spoken), words, start, end)
        for group in groups:
            group.update(recording_id=rid, reviewed=reviewed)
            group["class"] = classify_edit(group["kind"], group["transcript"], group["asr"], equivalents, pronunciations)
            if group["class"] == "LISTEN":
                clip_start = round(max(0.0, group["start_s"] - 1.0), 3)
                clip_end = round(min(float(row["duration_s"]), group["end_s"] + 1.0), 3)
                if audio_hash is None:
                    audio_hash = hashlib.sha256(audio.read_bytes()).hexdigest()
                identity = {"audio_sha256": audio_hash, "start_s": clip_start, "end_s": clip_end,
                            "model": "medium.en", "device": "cpu", "compute_type": "int8", "beam_size": 5, "temperature": 0.0}
                key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
                if key not in cache:
                    LOGGER.info("Second ASR: %s %.3f-%.3fs", rid, clip_start, clip_end)
                    second_text = secondary.transcribe(audio, clip_start, clip_end)
                    cache[key] = {**identity, "recording_id": rid, "text": second_text}
                    cache_path.write_text(json.dumps(cache, sort_keys=True, indent=2) + "\n", encoding="utf-8")
                primary = _primary_context(words, start, clip_start, clip_end)
                second = cache[key]["text"]
                group["second_asr"] = second
                group["primary_context"] = primary
                group["second_asr_window"] = [clip_start, clip_end]
                # Conservative corroboration: require identical normalized context,
                # including neighbours, rather than matching a common word anywhere.
                if primary and equivalent_text(primary, equivalents) == equivalent_text(second, equivalents):
                    group["class"] = "LIKELY_REAL"
            items.append(group)
    version_path.write_text(yaml.safe_dump(choices, sort_keys=True), encoding="utf-8")
    build_transcript_diffs(root)
    counts = {name: sum(item["class"] == name for item in items) for name in ("IGNORE", "LIKELY_ASR", "LISTEN", "LIKELY_REAL")}
    active = [item for item in items if item["class"] in {"LISTEN", "LIKELY_REAL"} and not item["reviewed"]]
    per_recording = Counter(item["recording_id"] for item in active)
    active.sort(key=lambda item: (-per_recording[item["recording_id"]], item["recording_id"], item["start_s"]))
    audit = {"schema": "transcript_triage/v1", "counts": counts, "listen_items": len(active),
             "secondary_asr": {"model": "medium.en", "device": "cpu", "beam_size": 5, "compute_type": "int8"},
             "items": items}
    (review_dir / "triage.json").write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = ["# Day 1 listen list", "", f"Items needing review: {len(active)}", "",
             "Times are relative to prepared audio. IGNORE and LIKELY_ASR remain in data/review/triage.json.",
             "LIKELY_REAL requires matching normalized primary/secondary ASR context; it is still a suggestion for human review.", "",
             "| Recording | Time | Transcript says | ASR says | Class | Decision |",
             "|---|---:|---|---|---|---|"]
    for item in active:
        lines.append(f"| {item['recording_id']} | {item['start_s']:.3f}s | {_escape_table(item['transcript'])} | {_escape_table(item['asr'])} | {item['class']} | |")
    (root / "reports/day01_listen_list.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_review_html(review_dir / "index.html", active)
    LOGGER.info("Triage counts: %s; listen list: %d", counts, len(active))
    return audit
