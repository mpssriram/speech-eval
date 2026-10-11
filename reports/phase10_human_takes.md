# Phase 10 human takes

**Eight genuine recordings imported; recorder consent and prose notes saved; confirmed transcripts, evaluable labels and analysis pending.**

No detector thresholds, bins, rubric weights or frozen scientific implementation were tuned.
The approved import preserves originals byte-for-byte and converts to mono PCM16 WAV at the native 48 kHz rate. No gain/loudness normalisation, filtering or trimming was performed.
The existing analysis workflow separately prepares 44.1 kHz uploads without gain normalisation and uses real CPU MFA with supplied as-spoken text and number expansion. This workflow has **not** run on these genuine takes; the previous verification below used only an explicitly synthetic fixture.

Primary interval matching: same type, one-to-one greedy IoU >= 0.3 for every type. Historical synthetic matching uses IoU >= 0.3 for regions but centre distance <= 0.25 s for pause events; its counts are shown separately.
Sentence-only notes are intended intervals, not independent time-labelled perceptual ground truth. Slips must be reflected in the supplied transcript; no automatic listening/review is claimed.

## Pending inputs

- `data/human/CONSENT.md` now contains the recorder's exact chat statement: `i fully agree for usage o my voice`. This is actual supplied consent, not generated consent. No public audio licence or public-release inclusion is inferred.
- `data/human/raw/notes.md` now preserves the recorder's supplied prose. They confirmed global takes 01–04 mean Gettysburg 01–04 and 05–08 mean Reagan 01–04. It does not yet contain the required fenced JSON annotation block: the existing validator now stops with `notes.md needs an explicit JSON annotation block; see docs/HUMAN_TAKES.md`. It is not a missing-consent failure anymore. No `FILL` or sentence-0 label was inserted.
- All eight **recorder-confirmed** as-spoken transcripts listed below are absent. Real local ASR drafts are in `data/human/asr_drafts/`, explicitly unconfirmed; none was automatically promoted to `data/human/transcripts/` or marked human-reviewed. Neither canonical text nor another reader's deviations were copied into the required input files.
- The supplied ZIP contained audio only. The recorder clarified that notes/consent were supplied as chat content, not existing Markdown files. That content has now been saved without invented wording or labels.
- ASR draft/word-diff preparation has run; genuine MFA analysis, human detection counts and dashboard jobs have **not**. Full input validation fails on incomplete annotations and confirmed transcripts. Validation evidence: `data/human/input_validation.json`.
- The frozen driver currently executes B02/B03 only and submits v1 only. The current request additionally requires B04 and separately labelled frozen v2 results. These workflow-coverage gaps must be addressed and tested after input confirmation; no detector, threshold or matching rule may change.

## Recorder notes and ASR review — not evaluation results

The supplied notes report repetitions near "government" (Gettysburg 01), an "or" slip and "they who have fought" (Gettysburg 02), slowing near "have thus far" and a pronunciation problem with "Died" (Gettysburg 03), and pronunciation/self-correction around "Terrible", "truths" and "special spirit" (Reagan 01). Reagan 02 has the recorder's explicit "No issues" statement. For the remaining takes they said: `yes, the flaws are random but i felt they were good ot me.` This does not establish supported types, time intervals or clean labels. Repetition/word slips and pronunciation reports are not automatically relabelled as mumbling or other detector types; recorder statements are not independent rater data.

[ASR review](phase10_asr_review.md) contains the eight full drafts and every suggested word edit. Because no complete recorder transcript was supplied, these are **canonical-versus-ASR** differences, not the originally requested ASR-versus-user-transcript comparison. ASR can omit repetitions, mishear proper names and impose incorrect punctuation. The same existing large-v3 / beam-5 / temperature-0 / Silero settings were used locally, with no detector/configuration changes. Approximate word times are ASR/CTC outputs, not human boundaries or real-MFA evaluation. The recorder must confirm actual wording and sentence punctuation before alignment.

| Take | Suggested canonical/ASR edit groups | Confirmed transcript | v1 primary A/B counts | post-hoc v2 A/B counts |
|---|---:|---|---|---|
| gettysburg__user__take01 | 15 | pending | not run / not estimable | not run / not estimable |
| gettysburg__user__take02 | 18 | pending | not run / not estimable | not run / not estimable |
| gettysburg__user__take03 | 10 | pending | not run / not estimable | not run / not estimable |
| gettysburg__user__take04 | 16 | pending | not run / not estimable | not run / not estimable |
| reagan_challenger__user__take01 | 17 | pending | not run / not estimable | not run / not estimable |
| reagan_challenger__user__take02 | 18 | pending | not run / not estimable | not run / not estimable |
| reagan_challenger__user__take03 | 16 | pending | not run / not estimable | not run / not estimable |
| reagan_challenger__user__take04 | 16 | pending | not run / not estimable | not run / not estimable |

These edit-group counts are suggestions, **not** numbers of actual slips, flaws or detector hits. No genuine dashboard links exist yet; the links below are still synthetic fixtures only. V1 stays the frozen primary result. Future v2 output must remain separately labelled **post-hoc v2; test split was seen with v1, so results are optimistic**. No one-shot test evaluation was rerun and no thresholds, bins, weights or rules were tuned on these recordings.

Verification of this input-preparation item: the full unchanged-code suite passed **275 tests**; cached ASR draft/review regeneration preserved all 21 draft/review/consent/notes/validation artifact hashes and all 16 original/WAV hashes. This proves cache idempotence, not an independent fresh-ASR accuracy check. The updated technical report rendered twice to identical six-page PDF bytes (SHA256 `2174954c9ee99dcaf9f04f167978488dafaf6f74d634637de7e646fedbe3ec1b`); all six final page images were visually inspected. Frozen v1 detector/pipeline and v2 configuration/one-shot-marker hashes remain unchanged.

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

Only the user confirms actual text, flaws and slips. Their actual consent/prose notes were saved from chat. ASR drafts remain separate and unconfirmed; no automatic transcript corrections or inferred labels are made. Real-MFA evaluation remains gated on complete validated inputs and the user's confirmation.

## Synthetic workflow verification — not human results

| Take | Mode | IoU hits / misses / FP | Synthetic-policy hits / misses / FP | Dashboard |
|---|---|---|---|---|
| workflow_fixture_1 | A | 0 / 0 / 0 | 0 / 0 / 0 | [Open](http://localhost:8080/results/86cb86dc2e9402d769f5a14c) |
| workflow_fixture_2 | A | 0 / 1 / 0 | 0 / 1 / 0 | [Open](http://localhost:8080/results/90e5cbba14d9486b41c32754) |
| workflow_fixture_2 | B | 0 / 1 / 0 | 0 / 1 / 0 | [Open](http://localhost:8080/results/2f439711be18c1451466e9e1) |

QA, hashes, exact declared label basis, trim bounds, aligner and score evidence: `data/human/fixture_verification.json` (explicitly synthetic).
Jobs are real completed API jobs, visible via their dashboard links and the existing previous-take history. Fixture jobs must not be presented as the user's recordings.

Confirmed as-spoken transcripts and complete delivery-flaw annotations remain user actions; genuine audio, actual consent and prose notes are supplied. Independent rating responses: **zero**. No independent raters are available before the deadline; the ready pack/scripts do not establish agreement. AI or self-ratings will not substitute for independent rater data. No human accuracy, rehearsal improvement or agreement claim is available from this import/ASR preparation.
