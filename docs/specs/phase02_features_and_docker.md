# Phase 2 spec — Feature extraction, speaker normalisation, Docker skeleton

Read `AGENTS.md` and `docs/PLAN.md` first. Requires Phase 1 complete (promoted alignment for every source recording).

## Goal

For every recording that has a promoted alignment, compute:

1. **frame-level** acoustic tracks (10 ms hop),
2. **word-level** features,
3. **sentence-level** features,
4. **speaker statistics** used for normalisation.

Also create a Docker image that runs the test suite, so packaging problems show up early.

## Units and conventions (use these exactly)

| Quantity | Unit | Notes |
|---|---|---|
| Time | seconds | rounded to 3 decimals in files |
| F0 (raw) | Hz | NaN when unvoiced |
| F0 (normalised) | semitones relative to the speaker's median F0: `st = 12 * log2(f0 / f0_median)` | removes voice-pitch differences between speakers |
| Intensity (raw) | dB (Praat intensity) | |
| Intensity (normalised) | dB relative to the speaker's median intensity over voiced frames | removes mic gain and natural loudness differences |
| Speech rate | syllables per second | **not** normalised: speed is a delivery choice, not biology |
| HNR | dB | |
| High-band ratio | dB: `10*log10(E[2–6 kHz] / E[0–2 kHz])` per frame | clarity proxy; drops when speech is muffled |

## Step 1 — Frame-level tracks (`src/speecheval/features.py`) — `speecheval features frames`

Input: `data/audio/hq/{recording_id}.wav`. Output: `data/features/frames/{recording_id}.parquet`.

Columns, one row per 10 ms frame (frame time = centre of the frame):

- `t`: seconds.
- `f0_hz`: Parselmouth pitch, **two-pass**:
  - pass 1 with floor 60 Hz and ceiling 600 Hz;
  - take Q1 and Q3 of voiced F0;
  - pass 2 with floor = 0.75 × Q1 and ceiling = 1.5 × Q3.
  - The ceiling multiplier is `features.pitch_ceiling_q3_factor` in config (default 1.5). Expressive speech may need 2.0. The QA report checks for octave jumps.
- `voiced`: bool.
- `intensity_db`: Parselmouth `to_intensity(minimum_pitch=75, time_step=0.01)`, interpolated to frame times.
- `hnr_db`: Parselmouth `to_harmonicity_cc(time_step=0.01, minimum_pitch=75)`; NaN where Praat returns −200.
- `centroid_hz`, `hiband_ratio_db`: from an STFT with 25 ms Hann window and 10 ms hop on the 44.1 kHz audio.
- `mfcc_1` … `mfcc_13`: librosa, same window and hop, 40 mel bands.

Frame times must line up exactly across all tracks. Use one shared time vector and interpolate Praat outputs onto it.

## Step 2 — Speaker statistics — `data/features/speaker_stats/{recording_id}.json`

```json
{
  "schema": "speaker_stats/v1",
  "recording_id": "...",
  "f0_median_hz": 118.2,
  "f0_q1_hz": 101.0,
  "f0_q3_hz": 139.5,
  "intensity_median_db": 62.3,
  "articulation_rate_syl_s": 4.21,
  "pitch_floor_hz": 75.8,
  "pitch_ceiling_hz": 209.3,
  "voiced_fraction": 0.61
}
```

All medians are over voiced frames inside aligned words only. Exclude silences, so pause length doesn't change the statistics.

## Step 3 — Syllable counts

- Use the `cmudict` package: the number of vowel phones (phones ending in a stress digit 0/1/2) in the first pronunciation.
- Fallback for words not in CMUdict: count vowel groups `[aeiouy]+` in the lowercase word, minimum 1.
- Numbers are already spelled out in `norm`.
- Store `syllables` per word.

## Step 4 — Word-level features — `data/features/words/{recording_id}.parquet`

One row per transcript word (`i` matches the alignment JSON):

| Column | Definition |
|---|---|
| `i`, `norm`, `sentence`, `start`, `end` | from alignment |
| `dur_s` | `end - start` |
| `syllables` | Step 3 |
| `log_dur_per_syl` | `ln(dur_s / syllables)` — word-level speed; larger = slower |
| `pause_before_s` | `start[i] - end[i-1]` (0 for the first word) |
| `pause_after_s` | `start[i+1] - end[i]` (0 for the last word) |
| `f0_st_median` | median normalised F0 (semitones) over voiced frames in the word; NaN if < 3 voiced frames |
| `f0_st_range` | p90 − p10 of normalised F0 in the word (semitones) |
| `int_rel_db_mean` | mean normalised intensity (dB) over frames in the word |
| `int_rel_db_max` | max normalised intensity in the word |
| `hnr_db_mean` | mean HNR over voiced frames |
| `hiband_ratio_db_mean`, `centroid_hz_mean` | means over frames in the word |
| `mfcc_k_mean` (k=1..13) | means over frames in the word |
| `voiced_frac` | fraction of voiced frames |

## Step 5 — Window and sentence features

**Rolling 3-word windows** — `data/features/windows/{recording_id}.parquet`. One row per word `i`, covering words `i-1, i, i+1` and clipped at sentence boundaries:

- `rate_syl_s`: syllables in window ÷ (end of last word − start of first word − sum of internal pauses > 0.25 s).
- `f0_st_std`: std of normalised F0 over voiced frames in the window (semitones). This is the monotone measure.
- `int_rel_db_mean`.
- `hiband_ratio_db_mean`.

**Sentences** — `data/features/sentences/{recording_id}.parquet`. One row per sentence:

- `articulation_rate_syl_s`: syllables ÷ speaking time, excluding internal pauses > 0.25 s.
- `speech_rate_syl_s`: syllables ÷ total sentence time.
- `f0_st_range`: p90 − p10 over the sentence.
- `final_pitch_slope_st_s`: linear fit of normalised F0 over the last 2 words.
- `final_int_drop_db`: mean intensity of last word − mean intensity of the sentence (negative = trailing off).
- `pause_after_s`.
- `n_words`, `n_syllables`, `has_number` (sentence contains a number word or digit).

## Step 6 — QA report (`speecheval report features`) → `reports/phase02_features.md` + PNGs in `reports/img/`

1. Table per recording: `f0_median_hz`, pitch floor/ceiling, articulation rate, voiced fraction, octave-jump count.
   An octave jump is consecutive voiced frames whose F0 ratio is > 1.8 or < 0.55.
2. Flag recordings with octave-jump rate > 1% of voiced frames, or `f0_median_hz` outside 70–300 Hz.
3. Plot `reports/img/phase02_gettysburg_overlay.png` for two Gettysburg readers, preferably one male and one female. Show three stacked panels against word index:
   - `f0_st_median`,
   - `int_rel_db_mean`,
   - `log_dur_per_syl`.

   Draw vertical lines at sentence boundaries.
4. Sanity note: after normalisation, the two readers' pitch curves should be on the same scale even though their Hz values differ. State whether this holds.

**USER:** look at the overlay plot. Same words, different speakers: the curves should look comparable in scale, not identical in shape.

## Step 7 — Docker skeleton

`Dockerfile` (CPU only, used for reproducibility, not speed):

- Base: `mambaorg/micromamba` on Ubuntu 24.04.
- Create the conda env `aligner` with `montreal-forced-aligner` and `"kaldi=*=cpu*"` from conda-forge, and download the three MFA models used in Phase 1.
- Install system packages `ffmpeg rubberband-cli sox`. Install `uv`, then install the project with the **CPU** PyTorch wheel index.
- `WORKDIR /app`. The project is copied in, and data is mounted at runtime (`-v $PWD/data:/app/data`).
- Default command: `uv run speecheval --help`.

Add a `Makefile` with:

- `make docker-build`
- `make docker-test` (runs `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 env -u PYTHONPATH uv run pytest` in the container)
- `make docker-shell`

`docker-test` must pass now. Do **not** run the full data pipeline in Docker yet; that happens in Phase 10.

## Step 8 — Tests

- A 200 Hz sine (1 s, 44.1 kHz) gives median `f0_hz` within ±1 Hz of 200.
- Semitone conversion: 2 × median → +12.00 st.
- Halving amplitude lowers `intensity_db` by 6.0 ± 0.2 dB.
- `hiband_ratio_db` drops by > 10 dB after low-pass filtering white noise at 1.5 kHz.
- Syllables: "Gettysburg" = 3, "score" = 1, "dedicated" = 4; an out-of-vocabulary fallback is ≥ 1.
- The window rate function on a synthetic 3-word table gives the hand-computed value.
- The determinism test (features computed twice give identical parquet bytes) passes.

## Acceptance checklist

- [ ] All five feature outputs exist for every Phase 1 recording.
- [ ] `reports/phase02_features.md` + overlay PNG exist; the user has looked at the overlay.
- [ ] No recording is flagged for octave jumps, or the flagged ones are listed in `docs/BLOCKERS.md` with a proposed pitch-range fix.
- [ ] Re-running `speecheval features all` produces identical hashes.
- [ ] `make docker-build && make docker-test` pass.
- [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 env -u PYTHONPATH uv run pytest` passes; `PROGRESS.md` is updated.

## Out of scope

Flaw injection, comparison, detection.
