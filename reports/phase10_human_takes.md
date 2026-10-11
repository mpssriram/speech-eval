# Phase 10 human takes

**Eight genuine recordings imported; consent, transcripts, notes and evaluation pending.**

No detector thresholds, bins, rubric weights or frozen scientific implementation were tuned.
The approved import preserves originals byte-for-byte and converts to mono PCM16 WAV at the native 48 kHz rate. No gain/loudness normalisation, filtering or trimming was performed.
The existing analysis workflow separately prepares 44.1 kHz uploads without gain normalisation and uses real CPU MFA with supplied as-spoken text and number expansion. This workflow has **not** run on these genuine takes; the previous verification below used only an explicitly synthetic fixture.

Primary interval matching: same type, one-to-one greedy IoU >= 0.3 for every type. Historical synthetic matching uses IoU >= 0.3 for regions but centre distance <= 0.25 s for pause events; its counts are shown separately.
Sentence-only notes are intended intervals, not independent time-labelled perceptual ground truth. Slips must be reflected in the supplied transcript; no automatic listening/review is claimed.

## Pending inputs

- `data/human/CONSENT.md`: missing; the existing validator rejects these inputs with `Missing nonempty data/human/CONSENT.md; no genuine takes processed`. Only the user can supply their actual consent. Import approval does not imply publication consent.
- `data/human/raw/notes.md`: missing. The user must supply actual intended flaws and slips for all eight take IDs in the fenced JSON format in `docs/HUMAN_TAKES.md`. No actual labels were inferred from the recording instructions. The absent notes cannot be checked for `FILL` or sentence 0.
- All eight as-spoken transcripts listed below are missing. The user must write the actual words spoken, including slips and only the Reagan excerpt actually recorded. Neither canonical text nor another reader's deviations were copied into these files.
- Read-only inspection of the supplied `Hackathon-20261011T161050Z-1-001.zip` found only the eight `.m4a` entries: no TXT, notes or consent. The extracted folder has the same eight audio files and no annotation documents.
- No ASR word diffs, listening, genuine MFA alignment, human detection counts or dashboard jobs have been produced. Processing stops at the requested consent/input gate, pending user completion and confirmation.
- The frozen driver currently executes B02/B03 only and submits v1 only. The current request additionally requires B04 and separately labelled frozen v2 results. These workflow-coverage gaps must be addressed and tested after input confirmation; no detector, threshold or matching rule may change.

## Verified audio import — 2026-10-11

The user approved this filename mapping before import. Copied originals are under `data/human/original/`; WAVs are under `data/human/raw/`. All sixteen audio files are git-ignored and excluded from the public release archive. Original and WAV SHA256 values, exact source metadata, sample counts and commands are recorded in `data/human/import_manifest.json`.

| Supplied original filename | Approved original filename (under `original/`) | Original bytes |
|---|---|---:|
| gettysburg__user__take01.m4a | gettysburg__user__take01.m4a | 4,424,351 |
| Gettysburg__user__take02.m4a | gettysburg__user__take02.m4a | 4,800,809 |
| Gettysburg__user__take03.m4a | gettysburg__user__take03.m4a | 4,327,881 |
| Gettysburg__user__take04.m4a | gettysburg__user__take04.m4a | 4,643,527 |
| Reagan Challenger take01.m4a | reagan_challenger__user__take01.m4a | 3,996,721 |
| Reagan challenger take02.m4a | reagan_challenger__user__take02.m4a | 4,075,009 |
| Reagan Challenger take03.m4a | reagan_challenger__user__take03.m4a | 4,220,998 |
| Reagan Challenger take04.m4a | reagan_challenger__user__take04.m4a | 4,630,276 |

All originals are ALAC lossless, 16-bit, 48,000 Hz, one channel. All output WAVs are little-endian PCM16, 48,000 Hz, one channel. Independent native PCM16 decoding of every original matches the corresponding WAV samples exactly, so their sample peaks and saturation counts are identical. Two fresh conversions per take have byte-identical WAV hashes. Repeated complete imports and independent verification also passed, preserving the final manifest SHA256 `f23d27e920d4a5f67a0dbefeac5ea9e3702fbb0f89d82c47ebac1cd3a7ceacbd` (JSON times rounded to milliseconds; sample counts remain exact). The unchanged-code full test suite passed: **275 tests** (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 env -u PYTHONPATH ~/.local/bin/uv run pytest`). The human validator's consent rejection was observed, not bypassed.

| WAV filename (under `raw/`) | Decoded duration (s) | WAV bytes | Peak (dBFS) | Full-scale samples | <=600 s / <=25 MiB |
|---|---:|---:|---:|---:|---|
| gettysburg__user__take01.wav | 83.277 | 7,994,696 | -0.7706 | 0 | pass / pass |
| gettysburg__user__take02.wav | 83.494 | 8,015,496 | -0.6415 | 0 | pass / pass |
| gettysburg__user__take03.wav | 81.475 | 7,821,704 | -0.7674 | 0 | pass / pass |
| gettysburg__user__take04.wav | 87.365 | 8,387,084 | -0.7933 | 0 | pass / pass |
| reagan_challenger__user__take01.wav | 77.665 | 7,455,912 | -0.6031 | 0 | pass / pass |
| reagan_challenger__user__take02.wav | 76.936 | 7,385,920 | -1.4372 | 0 | pass / pass |
| reagan_challenger__user__take03.wav | 79.661 | 7,647,570 | -2.7421 | 0 | pass / pass |
| reagan_challenger__user__take04.wav | 80.773 | 7,754,264 | -0.6207 | 0 | pass / pass |

Full-scale samples count decoded PCM16 endpoints (-32768/+32767); none were observed. This is not a listening judgement or proof that capture-stage/analogue clipping is absent. Peak dBFS uses max absolute sample divided by 32768. M4A container durations differ slightly from decoded frame durations (both recorded in the manifest); no trimming option was used and every decoded sample is preserved. The exact upload-size limit is 26,214,400 bytes. These are technical audio checks, **not** successful validation of the missing human annotations/consent.

The API checks upload size and duration (`src/speecheval/service.py`). The human-input validator (`src/speecheval/human_takes.py`) checks nonempty consent, a fenced notes JSON block, explicit `flaws` and `slips` for each discovered take, nonempty as-spoken transcripts, supported note types and valid sentence/raw-time fields. It does not itself enforce the upload limits or reject the literal `FILL`; the user's stronger no-placeholder rule still applies. Notes do not require severity; the separate TextGrid label importer requires `type:severity` with severity 1–5.

### Exact missing transcript paths

```text
data/human/transcripts/gettysburg__user__take01.txt
data/human/transcripts/gettysburg__user__take02.txt
data/human/transcripts/gettysburg__user__take03.txt
data/human/transcripts/gettysburg__user__take04.txt
data/human/transcripts/reagan_challenger__user__take01.txt
data/human/transcripts/reagan_challenger__user__take02.txt
data/human/transcripts/reagan_challenger__user__take03.txt
data/human/transcripts/reagan_challenger__user__take04.txt
```

Only the user supplies actual text, flaws, slips and consent. After they are supplied, ASR-versus-transcript differences are suggestions for the user to confirm, not ground truth; neither transcripts nor notes will be edited automatically. Real-MFA evaluation remains gated on the user's confirmation.

## Synthetic workflow verification — not human results

| Take | Mode | IoU hits / misses / FP | Synthetic-policy hits / misses / FP | Dashboard |
|---|---|---|---|---|
| workflow_fixture_1 | A | 0 / 0 / 0 | 0 / 0 / 0 | [Open](http://localhost:8080/results/86cb86dc2e9402d769f5a14c) |
| workflow_fixture_2 | A | 0 / 1 / 0 | 0 / 1 / 0 | [Open](http://localhost:8080/results/90e5cbba14d9486b41c32754) |
| workflow_fixture_2 | B | 0 / 1 / 0 | 0 / 1 / 0 | [Open](http://localhost:8080/results/2f439711be18c1451466e9e1) |

QA, hashes, exact declared label basis, trim bounds, aligner and score evidence: `data/human/fixture_verification.json` (explicitly synthetic).
Jobs are real completed API jobs, visible via their dashboard links and the existing previous-take history. Fixture jobs must not be presented as the user's recordings.

Actual notes, consent and as-spoken transcripts remain user actions; the eight genuine audio recordings are now imported. Independent rating responses: **zero**. No independent raters are available before the deadline; the ready pack/scripts do not establish agreement. AI or self-ratings will not substitute for independent rater data. No human accuracy, rehearsal improvement or agreement claim is available from this import.
