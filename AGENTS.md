# AGENTS.md — speech-eval

Read this file fully before every task. It is the contract for this repository.
The phase-by-phase roadmap is `docs/PLAN.md`. Task specs live in `docs/specs/`.
Do one spec at a time. Do not start work that no spec asks for.
When a spec step is marked **USER**, stop and report; that step is done by the human.

## 1. What we are building

A speech **delivery** evaluation system for the Multimodal AI Hackathon 2026, Track C
("Contrastive Speech Analytics & Temporal Flaw Grounding").

The system compares a participant recording against reference deliveries of speech,
finds the exact time regions where delivery is flawed, explains each flaw with the
measured numbers, and produces reproducible rubric scores.

### Locked scope

| Mode | What it compares | Priority |
|---|---|---|
| A — Expert comparison | Participant vs a strong speaker reading the **same text** | Core (days 1–6) |
| B — Rehearsal comparison | Participant take N vs their own earlier take of the same text | Add on day 5–6 |
| C-lite — Good-speaker norms | Participant vs statistical norms learned from all good recordings (no same-text reference). Only 4 features: speech rate, pitch variation, sentence-end pause, sentence-end loudness. Plus a key-moment check (numbers, final sentence). | Days 7–8, cut to prototype if late |

Content quality of a speech (argument, wording) is **out of scope**. We judge delivery only.

### Hackathon scoring we optimise for

| Criterion | Weight |
|---|---|
| Data engineering & stress testing (dataset, labels, severity gradient) | 30% |
| Causal explainability & temporal grounding (flaw timestamps, number-backed explanations) | 25% |
| Feature extraction rigor | 20% |
| Dashboard | 15% |
| Reproducibility & code quality | 10% |

## 2. Hard rules

1. **Determinism.** The same input must give byte-identical outputs on every run.
   - No LLM, no sampling, no unseeded randomness anywhere in the scoring path.
   - Any randomness (e.g. choosing where to inject a flaw) takes a seed from config.
   - Floats written to JSON are rounded (times to 3 decimals = 1 ms, features to 4 significant digits).
2. **Never modify `data/raw/`.** Everything else in `data/` must be re-creatable from raw + code + configs.
3. **No silent loudness normalisation of stored audio.** Volume is a feature we measure.
   Speaker normalisation happens only in the features/normalise stage, never by editing audio.
4. **Licensing.** Only use sources listed in `data/manifest/sources.yaml` with a license field.
   Do not add audio from YouTube, TED, or any source without a verified public-domain/CC0 statement.
5. **No secrets or large files in git.** Audio (`*.wav`, `*.mp3`, `*.ogg`, `*.flac`, `*.mp4`) is git-ignored.
   Small artefacts (JSON, TextGrid, YAML, CSV) are committed.
6. **If blocked** (a download needs a browser, a library won't install), write the blocker to
   `docs/BLOCKERS.md` with what you tried, then continue with the rest of the spec.

## 3. Environment

- Development OS: **WSL2 Ubuntu** on Windows (GPU: RTX 5080, 16 GB VRAM).
- Python **3.11**, managed with **uv** (`uv venv`, `uv pip install`, `uv run`).
- PyTorch must be a **CUDA 12.8+ build** (the RTX 5080 needs it). Everything must also run on CPU.
- Montreal Forced Aligner (MFA) lives in a separate **conda** env named `aligner`
  (installed via Miniforge). Call it through `conda run -n aligner mfa ...` from Python via `subprocess`.
- System packages: `ffmpeg`, `rubberband-cli`, `sox`.

## 4. Repository layout

```
speech-eval/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── configs/
│   ├── default.yaml          global settings (sample rates, paths, rounding)
│   ├── flaws.yaml            flaw types and severity parameters (phase 3)
│   ├── splits.yaml           speaker-based train/dev/test splits, written once (phase 4)
│   ├── baselines.yaml        expert baseline recording per text (phase 5)
│   ├── detector.yaml         thresholds, conflict rules, severity bins, engine choice (phases 5–6, 8)
│   └── rubric.yaml           score categories and weights (phase 7)
├── models/                   learned detector (phase 6)
├── data/
│   ├── manifest/sources.yaml every source recording + license evidence
│   ├── raw/                  untouched downloads (git-ignored audio)
│   ├── transcripts/
│   │   ├── canonical/        one official text per text_id
│   │   └── as_spoken/        one verified transcript per recording_id
│   ├── audio/                prepared audio (git-ignored)
│   │   ├── hq/               44.1 kHz mono PCM16, used for features
│   │   └── align16k/         16 kHz mono PCM16, used for alignment only
│   ├── alignment/            word timestamps, one JSON + one TextGrid per recording
│   ├── gold/alignment/       hand-marked word boundaries for evaluating aligners
│   ├── features/             frames/ words/ windows/ sentences/ speaker_stats/ (phase 2)
│   ├── flawed/               generated flawed audio as FLAC: hq/ align16k/ timemaps/ preview/ (phase 3+)
│   ├── human/                user's own recordings, labels_textgrid/, CONSENT.md (phase 4+)
│   ├── labels/               one label JSON per recording (phase 3+)
│   ├── reference/            reference models, pooled sigma, norms (phases 5, 8)
│   ├── analyses/             analysis/v1 JSON outputs (phase 5+)
│   ├── rating_pack/          blind human-rating pack (phase 7)
│   └── app/                  API job state (phase 9)
├── src/speecheval/
│   ├── __init__.py
│   ├── cli.py                single Typer CLI: `uv run speecheval <command>`
│   ├── config.py
│   ├── io.py                 audio load/save, JSON helpers with rounding
│   ├── sources.py            manifest loading + downloading
│   ├── prepare.py            format conversion, excerpting, trimming
│   ├── transcripts.py        normalisation, ASR-vs-canonical diffing
│   ├── align/
│   │   ├── base.py           common interface + output schema
│   │   ├── mfa.py
│   │   └── whisperx_align.py
│   ├── features.py           (phase 2)
│   ├── normalize.py          (phase 2)
│   ├── inject.py             (phase 3)
│   ├── dataset.py            (phase 4)
│   ├── pipeline.py           participant pipeline (phase 5)
│   ├── reference.py          reference models + norms (phases 5, 8)
│   ├── detect.py             (phase 5)
│   ├── explain.py            (phase 5)
│   ├── learned.py            (phase 6)
│   ├── score.py              (phase 7)
│   └── evaluate.py           (phase 1 for aligners, phase 6+ for detection)
├── api/                      FastAPI app (phase 9)
├── web/                      React + Vite dashboard (phase 9)
├── Dockerfile, docker-compose.yml, Makefile   (phases 2, 9, 10)
├── tests/
├── reports/                  generated QA/eval reports (markdown + PNG)
└── docs/
    ├── specs/                task specs, one per day
    └── BLOCKERS.md
```

## 5. Identifiers and naming

- `text_id`: the text being spoken. Lowercase snake case. Examples: `gettysburg`, `o_captain`, `jfk_rice`, `reagan_challenger`.
- `speaker_slug`: lowercase snake case, e.g. `jfk`, `reagan`, `lv_ann_boulais` (`lv_` prefix = LibriVox reader).
- `recording_id`: `{text_id}__{speaker_slug}__{variant}`
  - `variant` = `orig` for a source recording, `take01`… for user recordings,
    `{flaw}_s{severity}_{n}` for generated flawed audio, e.g. `rushing_s3_01`.
  - Example: `gettysburg__lv_ann_boulais__orig`.
- File names use the `recording_id` plus extension. No spaces anywhere.

## 6. Data formats (contracts between modules — do not change without a spec)

### 6.1 Alignment JSON — `data/alignment/{recording_id}.json`

```json
{
  "schema": "alignment/v1",
  "recording_id": "gettysburg__lv_ann_boulais__orig",
  "audio": "data/audio/hq/gettysburg__lv_ann_boulais__orig.wav",
  "duration_s": 125.412,
  "transcript": "data/transcripts/as_spoken/gettysburg__lv_ann_boulais__orig.txt",
  "aligner": {"name": "mfa", "version": "3.x.y", "model": "english_mfa"},
  "words": [
    {"i": 0, "text": "Four", "norm": "four", "start": 0.312, "end": 0.598, "sentence": 0},
    {"i": 1, "text": "score", "norm": "score", "start": 0.598, "end": 0.951, "sentence": 0}
  ],
  "sentences": [
    {"i": 0, "start": 0.312, "end": 9.874, "word_start": 0, "word_end": 28}
  ],
  "warnings": []
}
```

- `i` is the 0-based index of the word in the as-spoken transcript. Every transcript word appears exactly once, in order.
- `text` keeps original casing/punctuation; `norm` is lowercase, punctuation stripped, numbers spelled out.
- `word_end` in `sentences` is **inclusive**.
- Words the aligner could not place get `start`/`end` interpolated and the index added to `warnings`
  as `{"type": "interpolated", "word": i}`.

### 6.2 Flaw label JSON — `data/labels/{recording_id}.json` (written from day 3)

```json
{
  "schema": "labels/v1",
  "recording_id": "gettysburg__lv_ann_boulais__rushing_s3_01",
  "reference_id": "gettysburg__lv_ann_boulais__orig",
  "text_id": "gettysburg",
  "source": "synthetic",
  "flaws": [
    {
      "type": "rushing",
      "start": 12.400,
      "end": 15.100,
      "severity": 3,
      "word_start": 28,
      "word_end": 35,
      "parameters": {"speed_factor": 1.5}
    }
  ]
}
```

- `source` is `synthetic` (generated) or `human` (hand-labelled user recording).
- Times are in the **flawed** recording's timeline.
- Flaw `type` is one of: `rushing`, `dragging`, `monotone`, `too_quiet`, `awkward_pause`, `missing_pause`, `mumbling`.
- `severity` is an integer 1 (subtle) to 5 (botched).

### 6.3 Features (phase 2)

Parquet tables under `data/features/{frames,words,windows,sentences}/{recording_id}.parquet`, plus
`data/features/speaker_stats/{recording_id}.json`. Columns and units are defined in
`docs/specs/phase02_features_and_docker.md` and must not be renamed.

Normalised pitch is in **semitones relative to the speaker's median F0**. Normalised loudness is in **dB relative to the
speaker's median intensity**. Speech rate is **not** normalised.

### 6.4 Analysis JSON — `data/analyses/{analysis_id}.json` (phase 5+)

```json
{
  "schema": "analysis/v1",
  "analysis_id": "3f9a1c07b2de",
  "recording_id": "gettysburg__user__take02",
  "text_id": "gettysburg",
  "mode": "A",
  "reference": {"kind": "distribution", "text_id": "gettysburg", "exclude_speaker": null,
                "n_readers": 10, "reference_version": "a1b2c3", "baseline_recording_id": "gettysburg__lv_x__orig"},
  "transcript_source": "canonical",
  "detector": {"engine": "rules", "config_hash": "d4e5f6"},
  "duration_s": 131.204,
  "regions": [
    {
      "type": "rushing", "start": 12.400, "end": 15.100,
      "word_start": 28, "word_end": 35, "severity": 3, "mean_abs_z": 3.12,
      "evidence": {"feature": "rate", "participant": 5.8, "reference": 2.9, "unit": "syllables/s", "z": 3.1},
      "tags": ["final_sentence"],
      "explanation": "12.4–15.1 s, \"that we here highly resolve...\": you spoke at 5.8 syllables/s; ..."
    }
  ],
  "key_moments": [],
  "scores": {"pace": 7.0, "pitch": 10.0, "pauses": 9.6, "volume": 10.0, "clarity": 10.0, "overall": 9.2},
  "progress": null,
  "warnings": []
}
```

- `mode` is `A` (expert/distribution reference), `B` (previous take) or `C` (good-speaker norms, no same-text reference).
- For mode B, `reference.kind = "previous_take"`, and `progress` holds per-type counts and durations for the previous and current take.
- For mode C, `reference.kind = "norms"`, and `key_moments` holds heuristic checks (`{kind, start, end, words, passed, message}`). Key moments never affect scores.
- Region `start`/`end` are in the participant recording's timeline. Word indices refer to the participant's transcript.
- The example's `regions` list is shortened. The `pauses` score of 9.6 comes from one severity-1 pause event that isn't shown.

### 6.5 Generated audio

Generated and human audio is stored as **FLAC** (lossless). Source audio prepared in phase 1 stays WAV.

## 7. Code conventions

- Type hints everywhere. Docstrings on public functions state units (seconds, Hz, dB, semitones).
- Every stage is a CLI command that reads files and writes files. Stages are idempotent:
  re-running skips outputs that already exist unless `--force` is passed.
- Paths and numeric settings come from `configs/default.yaml`, never hard-coded.
- Logging via the `logging` module, not `print`.
- Tests with `pytest`. Each module gets at least one test on a tiny synthetic signal
  (e.g. a generated sine wave or a 3-word clip), so tests run in seconds without real data.
- Pin every dependency version in `pyproject.toml` once it works.

## 8. Definition of done for any spec

1. All acceptance checks in the spec pass.
2. `uv run pytest` passes.
3. Running the spec's commands a second time produces identical outputs (check with `sha256sum`).
4. A short summary is appended to `docs/specs/PROGRESS.md`: what was done, commands to reproduce, open issues.
