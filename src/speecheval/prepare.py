"""Audio decoding, trimming, and preparation."""

from __future__ import annotations

import csv
import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
import torch
import yaml
from rapidfuzz import fuzz

from speecheval.sources import SourceSpec, load_manifest
from speecheval.transcripts import normalize_tokens

LOGGER = logging.getLogger(__name__)


def _import_whisperx() -> Any:
    """Import WhisperX across torchaudio 2.11's removed legacy API names."""
    import torchaudio

    # pyannote-audio 3.x still imports these names, but the Silero VAD path used
    # by this project does not call them.
    if not hasattr(torchaudio, "AudioMetaData"):
        torchaudio.AudioMetaData = object  # type: ignore[attr-defined]
    if not hasattr(torchaudio, "list_audio_backends"):
        torchaudio.list_audio_backends = lambda: ["ffmpeg"]  # type: ignore[attr-defined]

    import whisperx

    return whisperx


def _flatten_asr_words(words: list[dict[str, Any]]) -> tuple[list[str], list[int]]:
    tokens: list[str] = []
    word_indices: list[int] = []
    for index, word in enumerate(words):
        for token in normalize_tokens(str(word.get("word", ""))):
            tokens.append(token)
            word_indices.append(index)
    return tokens, word_indices


def _best_token_window(haystack: list[str], needle: list[str]) -> tuple[int, int]:
    if not haystack or not needle:
        raise ValueError("cannot match an empty token sequence")
    best_score = -1.0
    best = (0, min(len(haystack), len(needle)))
    minimum = max(1, len(needle) - 2)
    maximum = min(len(haystack), len(needle) + 2)
    target = " ".join(needle)
    for width in range(minimum, maximum + 1):
        for start in range(0, len(haystack) - width + 1):
            end = start + width
            score = fuzz.ratio(target, " ".join(haystack[start:end]))
            if score > best_score:
                best_score = score
                best = (start, end)
    if best_score < 60:
        raise ValueError(f"canonical anchor match score too low: {best_score:.1f}")
    return best


def compute_trim_bounds(
    canonical_text: str,
    asr_words: list[dict[str, Any]],
    duration_s: float,
    padding_s: float,
) -> tuple[float, float]:
    """Return trim start/end times in seconds from canonical ASR anchors."""
    canonical = normalize_tokens(canonical_text)
    if len(canonical) < 6:
        raise ValueError("canonical transcript needs at least six words")
    asr_tokens, token_word_indices = _flatten_asr_words(asr_words)
    first_start, _ = _best_token_window(asr_tokens, canonical[:6])
    _, last_end = _best_token_window(asr_tokens, canonical[-6:])
    first_word = token_word_indices[first_start]
    last_word = token_word_indices[last_end - 1]
    start = max(0.0, float(asr_words[first_word]["start"]) - padding_s)
    end = min(duration_s, float(asr_words[last_word]["end"]) + padding_s)
    if end <= start:
        raise ValueError("computed trim range is empty")
    return round(start, 3), round(end, 3)


def render_prepared_audio(
    raw_path: Path,
    hq_path: Path,
    align_path: Path,
    cut_start_s: float,
    cut_end_s: float,
    hq_sample_rate: int,
    align_sample_rate: int,
    edge_fade_ms: int,
) -> None:
    """Write mono PCM16 WAVs at the requested rates without loudness normalization."""
    duration = cut_end_s - cut_start_s
    if duration <= 0:
        raise ValueError("cut_end_s must be greater than cut_start_s")
    fade_s = edge_fade_ms / 1000.0
    fade_out_start = max(0.0, duration - fade_s)
    audio_filter = f"afade=t=in:st=0:d={fade_s},afade=t=out:st={fade_out_start}:d={fade_s}"
    for path, sample_rate in ((hq_path, hq_sample_rate), (align_path, align_sample_rate)):
        path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg",
                "-nostdin",
                "-hide_banner",
                "-loglevel",
                "error",
                "-y",
                "-ss",
                f"{cut_start_s:.3f}",
                "-i",
                str(raw_path),
                "-t",
                f"{duration:.3f}",
                "-vn",
                "-ac",
                "1",
                "-ar",
                str(sample_rate),
                "-af",
                audio_filter,
                "-c:a",
                "pcm_s16le",
                str(path),
            ],
            check=True,
        )


def _canonical_text(path: Path) -> str:
    return "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines() if not line.startswith("#")
    ).strip()


def _decode_for_asr(raw_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(raw_path),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(output_path),
        ],
        check=True,
    )


def _round_asr_result(result: dict[str, Any]) -> dict[str, Any]:
    segments: list[dict[str, Any]] = []
    words: list[dict[str, Any]] = []
    for segment in result.get("segments", []):
        clean_segment = {
            "start": round(float(segment["start"]), 3),
            "end": round(float(segment["end"]), 3),
            "text": str(segment.get("text", "")).strip(),
        }
        segment_words: list[dict[str, Any]] = []
        for word in segment.get("words", []):
            if "start" not in word or "end" not in word:
                continue
            clean_word = {
                "word": str(word.get("word", "")).strip(),
                "start": round(float(word["start"]), 3),
                "end": round(float(word["end"]), 3),
            }
            if "score" in word:
                clean_word["score"] = round(float(word["score"]), 4)
            segment_words.append(clean_word)
            words.append(clean_word)
        clean_segment["words"] = segment_words
        segments.append(clean_segment)
    return {"segments": segments, "words": words}


def _run_whisperx(
    audio_path: Path,
    model: Any,
    align_model: Any,
    align_metadata: dict[str, Any],
    device: str,
    language: str,
) -> dict[str, Any]:
    result = model.transcribe(str(audio_path), batch_size=8, language=language)
    whisperx = _import_whisperx()

    aligned = whisperx.align(
        result["segments"], align_model, align_metadata, str(audio_path), device
    )
    return _round_asr_result(aligned)


def _find_source(source_id: str, sources: list[SourceSpec]) -> SourceSpec:
    for source in sources:
        if source.id == source_id:
            return source
    raise KeyError(f"source {source_id!r} is absent from sources.yaml")


def _find_anchor_word(words: list[dict[str, Any]], anchor: str) -> int:
    tokens, indices = _flatten_asr_words(words)
    start, _ = _best_token_window(tokens, normalize_tokens(anchor))
    return indices[start]


def _excerpt_bounds(
    words: list[dict[str, Any]],
    segments: list[dict[str, Any]],
    anchor: str,
    target_length_s: list[float],
) -> tuple[float, float]:
    anchor_index = _find_anchor_word(words, anchor)
    anchor_time = float(words[anchor_index]["start"])
    anchor_sentence = next(
        (index for index, segment in enumerate(segments) if float(segment["end"]) >= anchor_time),
        len(segments) - 1,
    )
    start_index = max(0, anchor_sentence - 2)
    start = float(segments[start_index]["start"])
    minimum, maximum = map(float, target_length_s)
    desired = min(max(150.0, minimum), maximum)
    sentence_ends = [
        index
        for index in range(start_index, len(segments))
        if re.search(r"[.!?][\\\"']?$", str(segments[index].get("text", "")).strip())
        and not str(segments[index].get("text", "")).strip().endswith("...")
    ]
    end_index = next(
        (
            index
            for index in sentence_ends
            if float(segments[index]["end"]) - start >= desired
        ),
        sentence_ends[-1],
    )
    eligible_ends = [
        index
        for index in sentence_ends
        if minimum <= float(segments[index]["end"]) - start <= maximum
    ]
    if eligible_ends and float(segments[end_index]["end"]) - start > maximum:
        end_index = eligible_ends[-1]
    end = float(segments[end_index]["end"])
    if not minimum <= end - start <= maximum:
        raise ValueError(f"unable to make excerpt within {minimum:g}–{maximum:g} seconds")
    return round(start, 3), round(end, 3)


def _measure_audio(path: Path) -> tuple[float, float, float, float]:
    audio, sample_rate = sf.read(path, dtype="float64", always_2d=True)
    mono = audio[:, 0]
    duration = len(mono) / sample_rate
    loudness = float(pyln.Meter(sample_rate).integrated_loudness(mono))
    peak = float(np.max(np.abs(mono))) if mono.size else 0.0
    peak_dbfs = float(20.0 * np.log10(max(peak, np.finfo(float).tiny)))
    clipped = float(np.mean(np.abs(mono) >= (32767.0 / 32768.0))) if mono.size else 0.0
    return duration, loudness, peak_dbfs, clipped


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def prepare_recordings(force: bool = False) -> list[dict[str, Any]]:
    """Prepare all fetched source recordings and return their QA rows."""
    root = Path.cwd().resolve()
    config = _load_yaml(root / "configs" / "default.yaml")
    manifest = load_manifest(root / "data" / "manifest" / "sources.yaml")
    sources = manifest.day_one_sources
    with (root / "data" / "manifest" / "raw_files.csv").open(
        encoding="utf-8", newline=""
    ) as handle:
        raw_rows = list(csv.DictReader(handle))

    excerpts_path = root / "data" / "manifest" / "excerpts.yaml"
    excerpts = _load_yaml(excerpts_path)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = str(config["asr"]["compute_type"] if device == "cuda" else "float32")
    asr_model = None
    align_model = None
    align_metadata = None
    recording_rows: list[dict[str, Any]] = []

    cache_root = root / "data" / ".cache"
    os.environ.setdefault("HF_HOME", str(cache_root / "huggingface"))
    os.environ.setdefault("TORCH_HOME", str(cache_root / "torch"))

    with tempfile.TemporaryDirectory(prefix="prepare-", dir=root / "data") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        for raw_row in raw_rows:
            recording_id = raw_row["recording_id"]
            text_id = recording_id.split("__", 1)[0]
            source = _find_source(raw_row["source_id"], sources)
            raw_path = root / raw_row["raw_path"]
            hq_path = root / config["paths"]["hq"] / f"{recording_id}.wav"
            align_path = root / config["paths"]["align16k"] / f"{recording_id}.wav"
            asr_path = root / config["paths"]["alignment"] / "asr" / f"{recording_id}.json"

            asr_result: dict[str, Any] | None = None
            if asr_path.exists():
                asr_result = json.loads(asr_path.read_text(encoding="utf-8"))

            decision = excerpts.get(recording_id)
            if decision is None:
                full_wav = temp_dir / f"{recording_id}.wav"
                _decode_for_asr(raw_path, full_wav)
                if asr_result is None:
                    if asr_model is None:
                        whisperx = _import_whisperx()

                        asr_model = whisperx.load_model(
                            str(config["asr"]["model"]),
                            device,
                            compute_type=compute_type,
                            language=str(config["asr"]["language"]),
                            asr_options={
                                "beam_size": int(config["asr"]["beam_size"]),
                                "temperatures": [float(config["asr"]["temperature"])],
                            },
                            vad_method="silero",
                            download_root=str(cache_root / "whisperx"),
                        )
                        align_model, align_metadata = whisperx.load_align_model(
                            language_code=str(config["asr"]["language"]),
                            device=device,
                            model_dir=str(cache_root / "torch"),
                        )
                    assert align_model is not None and align_metadata is not None
                    asr_result = _run_whisperx(
                        full_wav,
                        asr_model,
                        align_model,
                        align_metadata,
                        device,
                        str(config["asr"]["language"]),
                    )
                    asr_payload = {
                        "model": str(config["asr"]["model"]),
                        "language": str(config["asr"]["language"]),
                        "device": device,
                        **asr_result,
                    }
                    asr_path.parent.mkdir(parents=True, exist_ok=True)
                    asr_path.write_text(
                        json.dumps(asr_payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                        encoding="utf-8",
                    )
                    asr_result = asr_payload

                assert asr_result is not None
                excerpt = getattr(source, "excerpt", None)
                if excerpt:
                    cut_start, cut_end = _excerpt_bounds(
                        asr_result["words"],
                        asr_result["segments"],
                        str(excerpt["start_anchor"]),
                        list(excerpt["target_length_s"]),
                    )
                    notes = "sentence-bounded excerpt around configured anchor"
                else:
                    canonical_path = root / config["paths"]["transcripts_canonical"] / f"{text_id}.txt"
                    cut_start, cut_end = compute_trim_bounds(
                        _canonical_text(canonical_path),
                        asr_result["words"],
                        float(raw_row["duration_s"]),
                        float(config["audio"]["trim_padding_s"]),
                    )
                    notes = "canonical first/last six-word anchors"
                decision = {
                    "cut_start_s": cut_start,
                    "cut_end_s": cut_end,
                    "method": "asr_anchor",
                    "asr_model": str(config["asr"]["model"]),
                    "notes": notes,
                }
                excerpts[recording_id] = decision

            if force or not hq_path.exists() or not align_path.exists():
                render_prepared_audio(
                    raw_path,
                    hq_path,
                    align_path,
                    float(decision["cut_start_s"]),
                    float(decision["cut_end_s"]),
                    int(config["audio"]["hq_sample_rate"]),
                    int(config["audio"]["align_sample_rate"]),
                    int(config["audio"]["edge_fade_ms"]),
                )

            duration, lufs, peak_dbfs, clipped_fraction = _measure_audio(hq_path)
            qa_flags: list[str] = []
            if clipped_fraction > 0.001:
                qa_flags.append("clipped")
            if lufs < -40:
                qa_flags.append("very_quiet")
            if int(raw_row["original_sample_rate"]) < 16_000:
                qa_flags.append("low_sr")
            recording_rows.append(
                {
                    "recording_id": recording_id,
                    "text_id": text_id,
                    "speaker_slug": raw_row["speaker_slug"],
                    "duration_s": round(duration, 3),
                    "integrated_lufs": round(lufs, 3),
                    "peak_dbfs": round(peak_dbfs, 3),
                    "clipped_fraction": round(clipped_fraction, 6),
                    "original_sample_rate": int(raw_row["original_sample_rate"]),
                    "cut_start_s": float(decision["cut_start_s"]),
                    "cut_end_s": float(decision["cut_end_s"]),
                    "qa_flags": ";".join(qa_flags),
                }
            )

    excerpts_path.write_text(
        yaml.safe_dump(excerpts, sort_keys=True, allow_unicode=True), encoding="utf-8"
    )
    recordings_path = root / "data" / "manifest" / "recordings.csv"
    fieldnames = [
        "recording_id",
        "text_id",
        "speaker_slug",
        "duration_s",
        "integrated_lufs",
        "peak_dbfs",
        "clipped_fraction",
        "original_sample_rate",
        "cut_start_s",
        "cut_end_s",
        "qa_flags",
    ]
    recording_rows.sort(key=lambda row: row["recording_id"])
    with recordings_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(recording_rows)
    LOGGER.info("Prepared %d recordings on %s", len(recording_rows), device)
    return recording_rows
