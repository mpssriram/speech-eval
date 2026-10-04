"""Transcript normalization and ASR comparison."""

from __future__ import annotations

import csv
import difflib
import json
import logging
import re
from pathlib import Path
from typing import Any

import yaml
from num2words import num2words

LOGGER = logging.getLogger(__name__)


def _number_to_words(match: re.Match[str]) -> str:
    # Keep digits adjacent to a hyphen (C-1, 48-story) as separate words.
    return " " + str(num2words(int(match.group(0)))).replace("-", " ") + " "


def normalize_tokens(text: str) -> list[str]:
    """Normalize transcript text into lowercase comparison tokens."""
    text = text.lower().replace("&", " and ")
    text = re.sub(r"(?<=\d),(?=\d{3}(?:\D|$))", "", text)
    text = re.sub(r"\d+", _number_to_words, text)
    text = text.replace("’", "'").replace("‘", "'")
    text = re.sub(r"['-]", "", text)
    text = re.sub(r"[^a-z]+", " ", text)
    return text.split()


def _tokens_with_spans(text: str) -> tuple[list[str], list[tuple[int, int]]]:
    tokens: list[str] = []
    spans: list[tuple[int, int]] = []
    for match in re.finditer(r"\d+(?:,\d{3})*|[A-Za-z]+(?:['’\-][A-Za-z]+)*|&", text):
        normalized = normalize_tokens(match.group(0))
        tokens.extend(normalized)
        spans.extend([match.span()] * len(normalized))
    return tokens, spans


def _asr_tokens(
    words: list[dict[str, Any]],
    cut_start_s: float = 0.0,
    cut_end_s: float | None = None,
) -> tuple[list[str], list[float], list[int]]:
    tokens: list[str] = []
    starts: list[float] = []
    source_indices: list[int] = []
    for index, word in enumerate(words):
        start = float(word["start"])
        end = float(word["end"])
        if end < cut_start_s or (cut_end_s is not None and start > cut_end_s):
            continue
        normalized = normalize_tokens(str(word.get("word", "")))
        tokens.extend(normalized)
        starts.extend([round(max(0.0, start - cut_start_s), 3)] * len(normalized))
        source_indices.extend([index] * len(normalized))
    return tokens, starts, source_indices


def compare_transcript(
    transcript_text: str,
    asr_words: list[dict[str, Any]],
    cut_start_s: float = 0.0,
    cut_end_s: float | None = None,
) -> list[dict[str, Any]]:
    """Return normalized transcript/ASR edit operations with clip-relative times."""
    transcript_tokens = normalize_tokens(transcript_text)
    asr_tokens, starts, _ = _asr_tokens(asr_words, cut_start_s, cut_end_s)
    matcher = difflib.SequenceMatcher(None, transcript_tokens, asr_tokens, autojunk=False)
    differences: list[dict[str, Any]] = []
    for kind, i1, i2, j1, j2 in matcher.get_opcodes():
        if kind == "equal":
            continue
        if j1 < len(starts):
            start_s = starts[j1]
        elif starts:
            start_s = starts[-1]
        else:
            start_s = 0.0
        differences.append(
            {
                "kind": kind,
                "transcript": " ".join(transcript_tokens[i1:i2]),
                "asr": " ".join(asr_tokens[j1:j2]),
                "start_s": round(start_s, 3),
            }
        )
    return differences


def canonical_excerpt(
    canonical_text: str,
    asr_words: list[dict[str, Any]],
    cut_start_s: float,
    cut_end_s: float,
) -> str:
    """Extract the canonical sentence span corresponding to an audio excerpt."""
    canonical_tokens, spans = _tokens_with_spans(canonical_text)
    asr_tokens, _, source_indices = _asr_tokens(asr_words)
    selected_asr = {
        index
        for index, word_index in enumerate(source_indices)
        if float(asr_words[word_index]["end"]) >= cut_start_s
        and float(asr_words[word_index]["start"]) <= cut_end_s
    }
    matched_canonical: list[int] = []
    matcher = difflib.SequenceMatcher(None, canonical_tokens, asr_tokens, autojunk=False)
    for canonical_start, asr_start, length in matcher.get_matching_blocks():
        for offset in range(length):
            if asr_start + offset in selected_asr:
                matched_canonical.append(canonical_start + offset)
    if not matched_canonical:
        raise ValueError("excerpt has no canonical/ASR token matches")

    first_char = spans[min(matched_canonical)][0]
    last_char = spans[max(matched_canonical)][1]
    previous_boundaries = [
        canonical_text.rfind(mark, 0, first_char) for mark in (".", "!", "?", "\n")
    ]
    start_char = max(previous_boundaries) + 1
    sentence_end = re.search(r"[.!?](?:[\"']|\s|$)", canonical_text[last_char:])
    end_char = last_char + sentence_end.end() if sentence_end else last_char
    return canonical_text[start_char:end_char].strip()


def _body_text(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith("#")).strip()


def _escape_table(text: str) -> str:
    return (text or "—").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def build_transcript_diffs(root: Path | None = None) -> list[dict[str, Any]]:
    """Create missing as-spoken drafts and the Day 1 transcript-difference report."""
    root = (root or Path.cwd()).resolve()
    with (root / "data/manifest/recordings.csv").open(encoding="utf-8", newline="") as handle:
        recordings = list(csv.DictReader(handle))
    excerpts = yaml.safe_load(
        (root / "data/manifest/excerpts.yaml").read_text(encoding="utf-8")
    ) or {}
    as_spoken_dir = root / "data/transcripts/as_spoken"
    as_spoken_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for row in recordings:
        recording_id = row["recording_id"]
        canonical_path = root / "data/transcripts/canonical" / f"{row['text_id']}.txt"
        canonical_file = canonical_path.read_text(encoding="utf-8")
        asr = json.loads(
            (root / "data/alignment/asr" / f"{recording_id}.json").read_text(
                encoding="utf-8"
            )
        )
        cut_start = float(row["cut_start_s"])
        cut_end = float(row["cut_end_s"])
        as_spoken_path = as_spoken_dir / f"{recording_id}.txt"
        if not as_spoken_path.exists():
            if str(excerpts[recording_id].get("notes", "")).startswith("sentence-bounded"):
                initial_text = canonical_excerpt(
                    _body_text(canonical_file), asr["words"], cut_start, cut_end
                )
                as_spoken_path.write_text(initial_text + "\n", encoding="utf-8")
            else:
                as_spoken_path.write_text(canonical_file, encoding="utf-8")

        as_spoken = as_spoken_path.read_text(encoding="utf-8")
        results.append(
            {
                "recording_id": recording_id,
                "reviewed": bool(
                    re.search(r"^#\s*reviewed:\s*yes\s*$", as_spoken, re.IGNORECASE | re.MULTILINE)
                ),
                "differences": compare_transcript(
                    _body_text(as_spoken), asr["words"], cut_start, cut_end
                ),
            }
        )

    results.sort(key=lambda item: (-len(item["differences"]), item["recording_id"]))
    total = sum(len(item["differences"]) for item in results)
    lines = [
        "# Day 1 transcript differences",
        "",
        f"Recordings: {len(results)} · edit groups: {total}",
        "",
        "Times are relative to the prepared audio clip.",
        "",
    ]
    for result in results:
        differences = result["differences"]
        status = "reviewed" if result["reviewed"] else "unreviewed"
        lines.extend(
            [
                f"## {result['recording_id']} — {len(differences)} differences — {status}",
                "",
            ]
        )
        if differences:
            lines.extend(
                [
                    "| Time | Type | Transcript | ASR |",
                    "|---:|---|---|---|",
                    *[
                        f"| {difference['start_s']:.3f}s | {difference['kind']} | "
                        f"{_escape_table(difference['transcript'])} | "
                        f"{_escape_table(difference['asr'])} |"
                        for difference in differences
                    ],
                    "",
                ]
            )
        else:
            lines.extend(["No differences.", ""])

    report_path = root / "reports/day01_transcript_diffs.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    LOGGER.info("Wrote %d edit groups across %d recordings", total, len(results))
    return results
