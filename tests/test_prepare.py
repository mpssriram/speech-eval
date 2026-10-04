from pathlib import Path

import numpy as np
import soundfile as sf

from speecheval.prepare import _import_whisperx, compute_trim_bounds, render_prepared_audio


def test_compute_trim_bounds_ignores_intro_and_outro() -> None:
    """Including non-canonical intro or outro speech must break this test."""
    canonical = "Four score and seven years ago our fathers brought forth"
    words = [
        {"word": "LibriVox", "start": 0.1, "end": 0.4},
        {"word": "Four", "start": 0.5, "end": 0.7},
        {"word": "score", "start": 0.7, "end": 0.9},
        {"word": "and", "start": 0.9, "end": 1.0},
        {"word": "seven", "start": 1.0, "end": 1.2},
        {"word": "years", "start": 1.2, "end": 1.4},
        {"word": "ago", "start": 1.4, "end": 1.6},
        {"word": "our", "start": 1.6, "end": 1.8},
        {"word": "fathers", "start": 1.8, "end": 2.0},
        {"word": "brought", "start": 2.0, "end": 2.2},
        {"word": "forth", "start": 2.2, "end": 2.4},
        {"word": "end", "start": 2.5, "end": 2.8},
    ]

    assert compute_trim_bounds(canonical, words, duration_s=3.0, padding_s=0.25) == (0.25, 2.65)


def test_render_prepared_audio_trims_synthetic_signal(tmp_path: Path) -> None:
    """Wrong cut bounds, channel count, or sample rate must break this test."""
    sample_rate = 16_000
    silence = np.zeros(sample_rate // 2, dtype=np.float32)
    time = np.arange(sample_rate, dtype=np.float32) / sample_rate
    tone = 0.25 * np.sin(2 * np.pi * 440 * time)
    signal = np.concatenate([silence, tone, silence])
    raw = tmp_path / "raw.wav"
    hq = tmp_path / "hq.wav"
    align = tmp_path / "align.wav"
    sf.write(raw, signal, sample_rate, subtype="PCM_16")

    render_prepared_audio(raw, hq, align, 0.5, 1.5, 44_100, 16_000, 10)

    hq_audio, hq_rate = sf.read(hq, always_2d=True)
    align_audio, align_rate = sf.read(align, always_2d=True)
    assert hq_rate == 44_100
    assert align_rate == 16_000
    assert hq_audio.shape == (44_100, 1)
    assert align_audio.shape == (16_000, 1)
    assert np.max(np.abs(hq_audio)) <= 0.251


def test_whisperx_import_compatibility() -> None:
    """Removing the torchaudio compatibility bridge must break this test."""
    whisperx = _import_whisperx()

    assert callable(whisperx.load_model)
    assert callable(whisperx.load_align_model)
