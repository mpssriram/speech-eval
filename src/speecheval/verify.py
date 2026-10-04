"""CPU acoustic verification of the frozen Day 1 listening candidates."""

from __future__ import annotations

import csv
import difflib
import hashlib
import json
import logging
import math
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
import torch
import yaml

from speecheval.transcripts import (
    _asr_tokens, _body_text, _escape_table, _tokens_with_spans,
    build_transcript_diffs, normalize_tokens,
)
from speecheval.triage import edit_groups, write_review_html

LOGGER = logging.getLogger(__name__)


def _hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def sentence_units(text: str, poem: bool) -> list[dict[str, Any]]:
    """Return sentence (or poem-line) text with original character offsets."""
    ends = [match.end() for match in re.finditer(r"\n", text)] if poem else [
        match.end() for match in re.finditer(r"[.!?;][\"']*|:(?=\s+[A-Z])", text)
    ]
    ends.append(len(text))
    units: list[dict[str, Any]] = []
    start = 0
    for end in ends:
        raw = text[start:end]
        stripped = raw.strip()
        if stripped:
            char_start = start + len(raw) - len(raw.lstrip())
            units.append({"i": len(units), "text": stripped, "char_start": char_start,
                          "char_end": char_start + len(stripped)})
        start = end
    return units


def build_sentence_windows(
    text: str, words: list[dict[str, Any]], cut_start: float, cut_end: float,
    padding: float, poem: bool,
) -> list[dict[str, Any]]:
    """Map sentence boundaries onto full-source ASR, then return prepared-clip seconds."""
    tokens, spans = _tokens_with_spans(text)
    asr, _, source_indices = _asr_tokens(words, cut_start, cut_end)
    mapping: dict[int, int] = {}
    for i, j, length in difflib.SequenceMatcher(None, tokens, asr, autojunk=False).get_matching_blocks():
        mapping.update({i + offset: source_indices[j + offset] for offset in range(length)})
    windows = sentence_units(text, poem)
    for unit in windows:
        included = [i for i, span in enumerate(spans) if unit["char_start"] <= span[0] < unit["char_end"]]
        if not included or not mapping:
            unit.update(start=0.0, end=0.0, valid=False, interpolated_boundary=True)
            continue
        first, last = included[0], included[-1]
        first_match = first if first in mapping else min(mapping, key=lambda i: (abs(i - first), i))
        last_match = last if last in mapping else min(mapping, key=lambda i: (abs(i - last), i))
        start = max(0.0, float(words[mapping[first_match]]["start"]) - cut_start - padding)
        end = min(cut_end - cut_start, float(words[mapping[last_match]]["end"]) - cut_start + padding)
        unit.update(start=round(start, 3), end=round(end, 3), valid=end > start,
                    interpolated_boundary=first_match != first or last_match != last)
    for previous, current in zip(windows, windows[1:]):
        if previous["end"] - current["start"] > padding:
            midpoint = (previous["end"] + current["start"]) / 2
            previous["end"] = round(midpoint + padding / 2, 3)
            current["start"] = round(midpoint - padding / 2, 3)
    for unit in windows:
        unit["valid"] = unit["valid"] and unit["end"] > unit["start"]
    return windows


def substitute_candidate(text: str, start: int, end: int, variant: str) -> str:
    """Substitute a known character span, preserving all surrounding text."""
    replacement = variant.strip().strip(".,;:!?")
    if start == end and replacement:
        if start > 0 and not text[start - 1].isspace():
            replacement = " " + replacement
        if start < len(text) and not text[start].isspace():
            replacement += " "
    return text[:start] + replacement + text[end:]


def ctc_score(log_probs: torch.Tensor, target: list[int], blank: int = 0) -> float | None:
    """Return total CTC log-likelihood in nats/frame; impossible paths return None."""
    frames = log_probs.shape[0]
    if frames == 0:
        return None
    labels = torch.tensor(target, dtype=torch.int64)
    loss = torch.nn.functional.ctc_loss(
        log_probs.to(dtype=torch.float64, device="cpu").unsqueeze(1), labels,
        torch.tensor([frames], dtype=torch.int64), torch.tensor([len(target)], dtype=torch.int64),
        blank=blank, reduction="sum", zero_infinity=False,
    )
    value = -float(loss) / frames
    return value if math.isfinite(value) else None


def ctc_total(log_probs: torch.Tensor, target: list[int], blank: int = 0) -> float | None:
    """Total CTC log-likelihood in nats over identical candidate audio."""
    score = ctc_score(log_probs, target, blank)
    return None if score is None else score * log_probs.shape[0]


def acoustic_decision(a: float | None, b: float | None, margin: float) -> str:
    """Decide from unrounded normalized likelihoods with a positive nats/frame margin."""
    if margin <= 0:
        raise ValueError("verification margin must be positive")
    if a is None or b is None:
        return "UNSURE"
    if b - a >= margin:
        return "APPLY_B"
    if a - b >= margin:
        return "KEEP_A"
    return "UNSURE"


class AcousticScorer:
    """Cached wav2vec2 CPU emissions and full CTC sequence likelihoods."""

    def __init__(self, root: Path, settings: dict[str, Any]) -> None:
        if settings["device"] != "cpu" or settings["model"] != "WAV2VEC2_ASR_BASE_960H":
            raise ValueError("This verifier requires the pinned CPU wav2vec2 model")
        self.root = root
        self.settings = settings
        self.directory = root / "data/.cache/acoustic_verification"
        self.directory.mkdir(parents=True, exist_ok=True)
        checkpoint = root / "data/.cache/torch/wav2vec2_fairseq_base_ls960_asr_ls960.pth"
        if not checkpoint.exists():
            raise FileNotFoundError("Cached WhisperX wav2vec2 checkpoint is missing")
        self.model_hash = _hash_bytes(checkpoint.read_bytes())
        self.model: Any = None
        import torchaudio

        self.bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
        self.labels = {label: index for index, label in enumerate(self.bundle.get_labels())}

    def _load(self) -> None:
        if self.model is None:
            torch.manual_seed(0)
            torch.set_num_threads(int(self.settings["threads"]))
            torch.use_deterministic_algorithms(True)
            self.model = self.bundle.get_model(dl_kwargs={"model_dir": str(self.root / "data/.cache/torch")}).cpu().eval()

    def emissions(self, audio: Path, start: float, end: float) -> tuple[torch.Tensor, str]:
        identity = {"audio_sha256": _hash_bytes(audio.read_bytes()), "start_s": start, "end_s": end,
                    "model_sha256": self.model_hash, "torch": torch.__version__, "settings": self.settings}
        key = _hash_bytes(json.dumps(identity, sort_keys=True).encode())
        path = self.directory / f"{key}.npy"
        if path.exists():
            return torch.from_numpy(np.load(path, allow_pickle=False)), key
        self._load()
        with sf.SoundFile(audio) as handle:
            if handle.samplerate != self.bundle.sample_rate or handle.channels != 1:
                raise ValueError("Expected prepared mono 16 kHz PCM audio")
            begin, stop = round(start * handle.samplerate), round(end * handle.samplerate)
            handle.seek(begin)
            waveform = torch.from_numpy(handle.read(stop - begin, dtype="float32")).unsqueeze(0)
        with torch.inference_mode():
            logits, _ = self.model(waveform)
            log_probs = logits[0].to(torch.float64).log_softmax(-1).cpu()
        np.save(path, log_probs.numpy(), allow_pickle=False)
        return log_probs, key

    def score(self, emission: torch.Tensor, text: str) -> float | None:
        # Spoken numbers are expanded consistently; punctuation is not a CTC target.
        normalized = "|".join(normalize_tokens(text)).upper()
        if any(character not in self.labels for character in normalized):
            return None
        return ctc_score(emission, [self.labels[character] for character in normalized], self.labels["-"])


def _item_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return item["recording_id"], item["start_s"], item["transcript"], item["asr"]


def _freeze_inputs(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    path = root / "data/review/verification_input.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    triage = json.loads((root / "data/review/triage.json").read_text(encoding="utf-8"))
    wanted: set[tuple[Any, ...]] = set()
    for line in (root / "reports/day01_listen_list.md").read_text(encoding="utf-8").splitlines():
        if not line.startswith("| ") or line.startswith("| Recording"):
            continue
        cells = [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", line)[1:-1]]
        if len(cells) != 6:
            raise ValueError("Malformed listen-list row")
        wanted.add((cells[0], float(cells[1].rstrip("s")), cells[4]))
    items = [item.copy() for item in triage["items"] if (item["recording_id"], item["start_s"], item["class"]) in wanted]
    if len(items) != len(wanted):
        raise ValueError("Listen list does not match the frozen triage audit")
    recordings = list(csv.DictReader((root / "data/manifest/recordings.csv").open(encoding="utf-8", newline="")))
    transcripts: dict[str, str] = {}
    for row in recordings:
        rid = row["recording_id"]
        text = (root / config["paths"]["transcripts_as_spoken"] / f"{rid}.txt").read_text(encoding="utf-8")
        transcripts[rid] = text
        words = json.loads((root / config["paths"]["alignment"] / "asr" / f"{rid}.json").read_text())["words"]
        groups = {_item_key({**group, "recording_id": rid}): group for group in edit_groups(
            _body_text(text), words, float(row["cut_start_s"]), float(row["cut_end_s"]))}
        for item in items:
            if item["recording_id"] == rid:
                group = groups.get(_item_key(item))
                if group is None:
                    raise ValueError("Transcript was edited after triage; rerun triage before verification")
                item.update(transcript_start=group["transcript_start"], transcript_end=group["transcript_end"])
    payload = {"schema": "verification_input/v1", "items": items, "transcripts": transcripts,
               "listen_list_sha256": _hash_bytes((root / "reports/day01_listen_list.md").read_bytes())}
    _write_json(path, payload)
    return payload


def repair_source_bounds(root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    """Repair repeated final-anchor trims using full-source ASR without modifying raw audio."""
    from speecheval.prepare import compute_trim_bounds, prepare_recordings

    excerpts_path = root / "data/manifest/excerpts.yaml"
    excerpts = yaml.safe_load(excerpts_path.read_text(encoding="utf-8"))
    raw = list(csv.DictReader((root / "data/manifest/raw_files.csv").open(encoding="utf-8", newline="")))
    repairs: list[dict[str, Any]] = []
    for row in raw:
        rid = row["recording_id"]
        if not rid.startswith("o_captain__"):
            continue
        words = json.loads((root / config["paths"]["alignment"] / "asr" / f"{rid}.json").read_text())["words"]
        text = _body_text((root / config["paths"]["transcripts_canonical"] / "o_captain.txt").read_text())
        start, end = compute_trim_bounds(text, words, float(row["duration_s"]), float(config["audio"]["trim_padding_s"]))
        old = excerpts[rid]
        if old["cut_start_s"] != start or old["cut_end_s"] != end:
            repairs.append({"recording_id": rid, "old_start_s": old["cut_start_s"], "old_end_s": old["cut_end_s"],
                            "new_start_s": start, "new_end_s": end})
            old.update(cut_start_s=start, cut_end_s=end, notes="canonical anchors; last occurrence for repeated final phrase")
    if repairs:
        excerpts_path.write_text(yaml.safe_dump(excerpts, sort_keys=True), encoding="utf-8")
        prepare_recordings(force=True)
    return repairs


def _candidate_window(body: str, item: dict[str, Any], windows: list[dict[str, Any]]) -> dict[str, Any]:
    a, b = item["transcript_start"], item["transcript_end"]
    selected = [unit for unit in windows if unit["char_start"] < b and unit["char_end"] > a]
    if not selected and a == b:
        selected = [unit for unit in windows if unit["char_start"] <= a <= unit["char_end"]]
        if not selected:
            selected = [min(windows, key=lambda unit: abs(unit["char_start"] - a))]
    if not selected or not all(unit["valid"] for unit in selected):
        return {"valid": False, "reason": "No valid sentence window"}
    lo, hi = selected[0]["char_start"], selected[-1]["char_end"]
    lo, hi = min(lo, a), max(hi, b)
    text_a = body[lo:hi]
    text_b = substitute_candidate(text_a, a - lo, b - lo, item["asr"])
    return {"valid": True, "start_s": selected[0]["start"], "end_s": selected[-1]["end"],
            "sentence_indices": [unit["i"] for unit in selected], "candidate_a": text_a, "candidate_b": text_b,
            "interpolated_boundary": any(unit["interpolated_boundary"] for unit in selected)}


def _render_report(root: Path, audit: dict[str, Any]) -> None:
    deltas = [item["delta_nats_per_frame"] for item in audit["items"] if item.get("delta_nats_per_frame") is not None]
    lines = ["# Day 1 automatic acoustic verification", "",
             "This replaces unavailable human listening review; it is not human-verified ground truth.",
             "CTC sums all valid monotonic alignment paths for each candidate, then divides the total log-likelihood by the same audio frame count. CPU wav2vec2, evaluation mode, fixed seed and one thread.",
             "Method references: [PyTorch CTCLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CTCLoss.html) and [torchaudio wav2vec2 forced alignment](https://docs.pytorch.org/audio/stable/tutorials/forced_alignment_tutorial.html).",
             "", f"Margin: {audit['margin_nats_per_frame']:.3f} nats/frame. Positive delta favors candidate B.",
             f"Decisions: {audit['counts']}", "",
             "Both ASRs agreeing is supporting evidence only; acoustic preference must still meet the margin. Non-finite alignments and small margins remain UNSURE; no text is deleted merely because a candidate cannot align.", "",
             "## Distribution of B minus A", "", "| Statistic | Nats/frame |", "|---|---:|"]
    if deltas:
        values = np.asarray(deltas)
        for label, value in [("min", values.min()), ("p10", np.quantile(values, .1)), ("p25", np.quantile(values, .25)),
                             ("median", np.median(values)), ("p75", np.quantile(values, .75)), ("p90", np.quantile(values, .9)), ("max", values.max())]:
            lines.append(f"| {label} | {value:.6f} |")
        lines.extend(["", "| Delta range | Items |", "|---|---:|"])
        for label, lower, upper in [("below -0.10", -math.inf, -.1), ("-0.10 to -0.05", -.1, -.05),
                                    ("-0.05 to 0", -.05, 0), ("0 to 0.05", 0, .05), ("0.05 to 0.10", .05, .1), ("at least 0.10", .1, math.inf)]:
            lines.append(f"| {label} | {sum(lower <= value < upper for value in deltas)} |")
    lines.extend(["", "| Original ASR class | APPLY_B | KEEP_A | UNSURE |", "|---|---:|---:|---:|"])
    for category in ("LISTEN", "LIKELY_REAL"):
        totals = [sum(item["class"] == category and item["decision"] == decision for item in audit["items"])
                  for decision in ("APPLY_B", "KEEP_A", "UNSURE")]
        lines.append(f"| {category} | {totals[0]} | {totals[1]} | {totals[2]} |")
    lines.extend(["", "The 0.05 margin is a provisional operating threshold, not a calibrated confidence level. This unlabeled score distribution shows its selectivity but cannot establish error rates or justify accuracy claims. Longer sentences dilute local differences; related acoustic models can share errors. UNSURE remains unresolved.", "",
                  "Verification covers the frozen original 85 listen-list items. Correcting the truncated poem audio exposes additional full-poem differences in day01_transcript_diffs.md; these are not silently claimed verified. Edge insertions such as year/readout words remain model preferences on retained boundary audio, not proof of complete spoken words.", "",
                  "## Prepared-audio corrections", ""])
    for repair in audit["audio_repairs"]:
        lines.append(f"- {repair['recording_id']}: end {repair['old_end_s']:.3f}s → {repair['new_end_s']:.3f}s in the source. Repeated poem ending was matched too early; raw files and full ASR were preserved.")
    lines.extend(["", "## Every input listen-list item", "",
                  "| Recording | Original time | Sentence window | Transcript says | ASR variant | ASR class | Score A | Score B | B − A | Decision |",
                  "|---|---:|---|---|---|---|---:|---:|---:|---|"])
    for item in audit["items"]:
        score_a = f"{item['score_a']:.6f}" if item.get("score_a") is not None else "unscorable"
        score_b = f"{item['score_b']:.6f}" if item.get("score_b") is not None else "unscorable"
        delta = f"{item['delta_nats_per_frame']:.6f}" if item.get("delta_nats_per_frame") is not None else "—"
        window = f"{item['window']['start_s']:.3f}–{item['window']['end_s']:.3f}s" if item["window"].get("valid") else "invalid"
        lines.append(f"| {item['recording_id']} | {item['start_s']:.3f}s | {window} | {_escape_table(item['transcript'])} | {_escape_table(item['asr'])} | {item['class']} | {score_a} | {score_b} | {delta} | {item['decision']} |")
    (root / "reports/day01_acoustic_verification.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    listen = ["# Day 1 listen list — automatically verified", "",
              "The original 85 candidates are retained below with automatic decisions. No human review is claimed. UNSURE remains unresolved.",
              "Details, sentence windows and score distribution: day01_acoustic_verification.md.", "",
              "| Recording | Time | Transcript says | ASR says | Class | Decision |", "|---|---:|---|---|---|---|"]
    for item in audit["items"]:
        listen.append(f"| {item['recording_id']} | {item['start_s']:.3f}s | {_escape_table(item['transcript'])} | {_escape_table(item['asr'])} | {item['class']} | {item['decision']} |")
    (root / "reports/day01_listen_list.md").write_text("\n".join(listen) + "\n", encoding="utf-8")
    write_review_html(root / "data/review/index.html", audit["items"])


def _refresh_output_windows(root: Path, config: dict[str, Any], inputs: dict[str, Any]) -> None:
    """Keep downstream sentence windows consistent with the edited transcripts."""
    rows = {row["recording_id"]: row for row in csv.DictReader(
        (root / "data/manifest/recordings.csv").open(encoding="utf-8", newline=""))}
    for rid in inputs["transcripts"]:
        current = (root / config["paths"]["transcripts_as_spoken"] / f"{rid}.txt").read_text(encoding="utf-8")
        row = rows[rid]
        words = json.loads((root / config["paths"]["alignment"] / "asr" / f"{rid}.json").read_text())["words"]
        windows = build_sentence_windows(_body_text(current), words, float(row["cut_start_s"]), float(row["cut_end_s"]),
                                         float(config["alignment"]["sentence_window_padding_s"]), row["text_id"] == "o_captain")
        _write_json(root / config["paths"]["alignment"] / "windows" / f"{rid}.json", {
            "schema": "sentence_windows/v1", "recording_id": rid, "transcript_sha256": _hash_bytes(current.encode()),
            "sentence_window_padding_s": float(config['alignment']['sentence_window_padding_s']),
            "time_basis": "prepared_clip", "sentences": windows,
            "source_asr_sha256": _hash_bytes((root / config["paths"]["alignment"] / "asr" / f"{rid}.json").read_bytes()),
            "cut_start_s": float(row['cut_start_s']), "cut_end_s": float(row['cut_end_s'])})


def verify_transcripts(root: Path | None = None) -> dict[str, Any]:
    """Verify every frozen listen item and apply only finite, margin-supported edits."""
    root = (root or Path.cwd()).resolve()
    config = yaml.safe_load((root / "configs/default.yaml").read_text(encoding="utf-8"))
    settings = config["transcript_verification"]
    margin = float(settings["margin_nats_per_frame"])
    inputs = _freeze_inputs(root, config)
    output_path = root / "data/review/acoustic_verification.json"
    if output_path.exists():
        existing = json.loads(output_path.read_text())
        if existing["settings"] != settings:
            raise ValueError("Verification settings changed; existing applied audit must not be overwritten")
        for rid, fingerprint in existing["output_transcript_sha256"].items():
            current = root / config["paths"]["transcripts_as_spoken"] / f"{rid}.txt"
            if _hash_bytes(current.read_bytes()) != fingerprint:
                raise ValueError("Transcript changed after verification; preserve the audit and rerun diff")
        scorer = AcousticScorer(root, settings)
        if scorer.model_hash != existing["model_sha256"]:
            raise ValueError("Acoustic model changed after verification")
        audio_hashes: dict[str, str] = {}
        for item in existing["items"]:
            if not item.get("emission_key"):
                continue
            rid = item["recording_id"]
            if rid not in audio_hashes:
                audio_hashes[rid] = _hash_bytes((root / config["paths"]["align16k"] / f"{rid}.wav").read_bytes())
            window = item["window"]
            identity = {"audio_sha256": audio_hashes[rid], "start_s": window["start_s"], "end_s": window["end_s"],
                        "model_sha256": scorer.model_hash, "torch": torch.__version__, "settings": settings}
            if _hash_bytes(json.dumps(identity, sort_keys=True).encode()) != item["emission_key"]:
                raise ValueError("Audio or inference environment changed after verification")
        _refresh_output_windows(root, config, inputs)
        _render_report(root, existing)
        build_transcript_diffs(root)
        LOGGER.info("Reusing acoustic verification: %s", existing["counts"])
        return existing
    repairs_path = root / "data/review/audio_repairs.json"
    repairs = repair_source_bounds(root, config)
    if repairs:
        _write_json(repairs_path, repairs)
    elif repairs_path.exists():
        repairs = json.loads(repairs_path.read_text())
    rows = list(csv.DictReader((root / "data/manifest/recordings.csv").open(encoding="utf-8", newline="")))
    row_map = {row["recording_id"]: row for row in rows}
    scorer = AcousticScorer(root, settings)
    windows_by_recording: dict[str, list[dict[str, Any]]] = {}
    window_dir = root / config["paths"]["alignment"] / "windows"
    for rid, original in inputs["transcripts"].items():
        row = row_map[rid]
        body = _body_text(original)
        words = json.loads((root / config["paths"]["alignment"] / "asr" / f"{rid}.json").read_text())["words"]
        windows = build_sentence_windows(body, words, float(row["cut_start_s"]), float(row["cut_end_s"]),
                                         float(config["alignment"]["sentence_window_padding_s"]), row["text_id"] == "o_captain")
        windows_by_recording[rid] = windows
        _write_json(window_dir / f"{rid}.json", {"schema": "sentence_windows/v1", "recording_id": rid,
                    "transcript_sha256": _hash_bytes(original.encode()), "time_basis": "prepared_clip", "sentences": windows})
    cache_path = root / "data/review/acoustic_scores.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    results: list[dict[str, Any]] = []
    for number, frozen in enumerate(inputs["items"], 1):
        item = frozen.copy()
        rid = item["recording_id"]
        body = _body_text(inputs["transcripts"][rid])
        window = _candidate_window(body, item, windows_by_recording[rid])
        item["window"] = window
        a: float | None = None
        b: float | None = None
        if window["valid"]:
            LOGGER.info("CTC %d/%d %s %.3f-%.3fs", number, len(inputs["items"]), rid, window["start_s"], window["end_s"])
            emission, emission_key = scorer.emissions(root / config["paths"]["align16k"] / f"{rid}.wav", window["start_s"], window["end_s"])
            key = _hash_bytes(json.dumps({"emission": emission_key, "a": window["candidate_a"], "b": window["candidate_b"]}, sort_keys=True).encode())
            if key not in cache:
                a, b = scorer.score(emission, window["candidate_a"]), scorer.score(emission, window["candidate_b"])
                cache[key] = {"score_a": a, "score_b": b, "frames": emission.shape[0], "emission_key": emission_key}
                _write_json(cache_path, cache)
            scored = cache[key]
            a, b = scored["score_a"], scored["score_b"]
            item.update(frames=scored["frames"], emission_key=scored["emission_key"])
        item.update(score_a=None if a is None else round(a, 8), score_b=None if b is None else round(b, 8),
                    delta_nats_per_frame=None if a is None or b is None else round(b - a, 8),
                    decision=acoustic_decision(a, b, margin))
        item["asr_agreement_and_acoustics"] = item["class"] == "LIKELY_REAL" and item["decision"] == "APPLY_B"
        results.append(item)
    # Apply all edits against a single frozen original, in reverse character order.
    # This avoids shifting offsets and never treats automatic verification as human review.
    output_hashes: dict[str, str] = {}
    for rid, original in inputs["transcripts"].items():
        spoken_path = root / config["paths"]["transcripts_as_spoken"] / f"{rid}.txt"
        if spoken_path.read_text(encoding="utf-8") != original:
            raise ValueError("Transcript changed while verification ran; aborting before edits")
    for rid, original in inputs["transcripts"].items():
        owned = [item for item in results if item["recording_id"] == rid]
        if not owned:
            continue
        reviewed = bool(re.search(r"^#\s*reviewed:\s*yes\s*$", original, re.IGNORECASE | re.MULTILINE))
        body = _body_text(original)
        applied = [item for item in owned if item["decision"] == "APPLY_B"]
        if reviewed:
            for item in applied:
                item["decision"] = "UNSURE"
                item["reason"] = "Human-reviewed transcript preserved"
            applied = []
        for item in sorted(applied, key=lambda value: (value["transcript_start"], value["transcript_end"]), reverse=True):
            body = substitute_candidate(body, item["transcript_start"], item["transcript_end"], item["asr"])
        if applied:
            headers = [line for line in original.splitlines() if line.startswith("#")]
            headers.append(f"# verification: automatic_ctc; margin={margin:g} nats/frame; applied={len(applied)}; human_review=no")
            (root / config["paths"]["transcripts_as_spoken"] / f"{rid}.txt").write_text("\n".join(headers) + "\n" + body + "\n", encoding="utf-8")
        path = root / config["paths"]["transcripts_as_spoken"] / f"{rid}.txt"
        output_hashes[rid] = _hash_bytes(path.read_bytes())
    counts = {name: sum(item["decision"] == name for item in results) for name in ("APPLY_B", "KEEP_A", "UNSURE")}
    audit = {"schema": "acoustic_verification/v1", "human_reviewed": False, "margin_nats_per_frame": margin,
             "settings": settings, "model_sha256": scorer.model_hash, "counts": counts, "audio_repairs": repairs,
             "items": results, "output_transcript_sha256": output_hashes}
    _write_json(output_path, audit)
    _render_report(root, audit)
    _refresh_output_windows(root, config, inputs)
    build_transcript_diffs(root)
    LOGGER.info("Acoustic verification complete: %s", counts)
    return audit
