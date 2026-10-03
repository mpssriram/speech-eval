# Phase 4 spec — Full dataset, splits, dataset card, human recordings

Read `AGENTS.md` and `docs/PLAN.md` first. Requires Phase 3, including the user's listening sign-off.

## Goal

1. Freeze speaker-based splits.
2. Generate the full synthetic dataset.
3. Collect and label the user's own recordings.
4. Write the dataset card.

The result is **Dataset v1**, frozen. Later phases may add files but never change v1 files.

## Step 1 — Splits — `configs/splits.yaml` (committed, written once)

Splits are by **source recording (= speaker)**. Rule, applied deterministically by sorting `speaker_slug` alphabetically within each text:

| Text | train | dev | test |
|---|---|---|---|
| `gettysburg` (≈15 readers) | first 10 | next 2 | last 3 |
| `o_captain` (≈12 readers) | first 8 | next 2 | last 2 |
| `jfk_rice` | — | — | all (setting B-same-speaker) |
| `reagan_challenger` | — | — | all (setting B-same-speaker) |
| user's recordings | — | — | all (Human setting) |

- Readers flagged in Phase 1/2 QA (clipping, octave jumps, > 10% transcript deviation) are put in `excluded` with a reason, before the split is applied.
- Write the resulting lists to `configs/splits.yaml` and never regenerate it automatically. Add a test asserting no `speaker_slug` appears in two splits.

## Step 2 — Generate the synthetic set — `speecheval dataset build`

For every source recording in train, dev and test:

- **Single-flaw files:** each of the 7 types × severities 1–5 × **1 placement**
  (`too_quiet`: alternate `flat`/`trail` by severity, with odd severities flat and even severities trail).
- **Mixed files:** 2 per source. Each has 3 different flaw types, random severities 2–5 and non-overlapping sites. These test detection when several flaws co-occur.

Expected size: about 29 sources × (35 + 2) ≈ 1,070 files. As FLAC, roughly 6–8 GB plus the 16 kHz copies.

Then run the **real pipeline** on every flawed file:

1. Align with the primary aligner (Phase 1) using the source's as-spoken transcript → `data/alignment/{flawed_recording_id}.json`.
2. Compute Phase 2 features.

The detector in Phase 5 must use this real alignment, not the oracle. The oracle alignment is kept only to measure alignment error on flawed audio.

**Alignment-on-flawed-audio check:** compare real vs oracle word boundaries per flaw type. Report median absolute error in `reports/phase04_dataset.md`. If a flaw type has median error > 60 ms, list it as a risk. Alignment drift under extreme rushing is expected and should be reported.

Use multiprocessing with a fixed number of workers. The output must not depend on worker scheduling.

## Step 3 — Dataset index and card

`data/manifest/dataset_index.csv`, one row per audio file (sources, flawed and human):

`recording_id, kind(source|synthetic|human), text_id, speaker_slug, split, flaw_types, max_severity, duration_s, audio_path, label_path, sha256`

`docs/DATASET.md` (the dataset card, which is also used in the report):

1. Purpose and the "contrastive" design: same text, graded flaws.
2. Sources table with licenses and evidence links (from `sources.yaml`).
3. Construction: trimming, alignment, the injection method per type, severity tables (copy from `flaws.yaml`), site rules, time maps.
4. Label schema with an example.
5. Splits and the evaluation settings from PLAN.md §4.
6. Composition table: counts by text × split × type × severity, total hours.
7. Known limitations: synthetic flaws are approximations; the LibriVox reading style differs from oratory; English only.
8. Required attributions: LibriVox, US government works, Internet Archive.

## Step 4 — Human recordings

**4a. Codex — `speecheval human script`** writes `reports/phase04_recording_script.md` for 3 texts: Gettysburg (full), O Captain (full) and the first ~90 s of the Reagan address (cut at a sentence end).

For each text it lists 4 takes:

| Take | Instruction |
|---|---|
| `take01` | Best natural delivery |
| `take02` | Rush sentence X; insert a long pause inside sentence Y; drop your voice at the end of sentence Z |
| `take03` | Read sentence X in a flat monotone; mumble sentence Y; run sentences Y and Z together with no pause |
| `take04` | Mix of 3 flaws of the user's own choice; write down which and where right after recording |

X, Y and Z are concrete sentence numbers, quoted in full, chosen deterministically from the seed.

**4b. USER — record**

- Quiet room, laptop or phone mic, about 30 cm from the mouth, same setup for all takes.
- Save as WAV (or the phone's default format) into `data/human/raw/`, named `{text_id}__user__take01.wav` and so on.
- Read the transcript exactly (as-spoken = canonical). Note any slip in `data/human/raw/notes.md`.
- Consent: the user agrees to publish their own voice. If friends record too, get written consent in `data/human/CONSENT.md` first, or keep their audio private and publish only features and labels.

**4c. Codex — `speecheval human prepare`**

Convert, trim, align and extract features exactly as for sources (Phases 1–2). Then write a Praat TextGrid per take into `data/human/todo/{recording_id}.TextGrid` with:

- tier `words` (from alignment),
- tier `intended` (intervals pre-filled from the script for take02/03, labelled with the intended flaw type),
- an empty tier `flaws`.

**4d. USER — label in Praat**

For each take, mark in tier `flaws` where each flaw **actually** is, label it with a type from the taxonomy plus severity (e.g. `rushing:3`), and save to `data/human/labels_textgrid/`.

- Label any obvious unintended flaws too.
- Leave `take01` empty unless it has real flaws.

**4e. Codex — `speecheval labels import`**

Convert the TextGrids to `labels/v1` JSON (`source: human`, `reference_id: null`). Validate them, and report per-take flaw counts.

## Acceptance checklist

- [ ] `configs/splits.yaml` is committed, with the no-overlap test passing.
- [ ] Dataset built: counts match the expected composition (allowing logged skipped sites).
- [ ] `reports/phase04_dataset.md` has the composition table and the real-vs-oracle alignment error per flaw type.
- [ ] `docs/DATASET.md` is complete.
- [ ] **USER**: 12 human takes recorded, labelled and imported, and they validate.
- [ ] Re-running `dataset build` produces identical hashes for 20 randomly sampled files (fixed sample seed).
- [ ] Tag the commit `dataset-v1`.

## Out of scope

Detection and scoring.
