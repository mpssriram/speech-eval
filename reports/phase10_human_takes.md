# Phase 10 — genuine recorder-confirmed takes

COMPLETE: 8 distinct take(s) have completed analysis with real CPU MFA. Frozen v1 is primary; v2 is secondary.
post-hoc v2; test split was seen with v1, so results are optimistic.

Labels come from the recorder's 2026-10-12 confirmation of the planned script, not independent annotation or listening. The confirmation replaces manual TAKES_REVIEW markers. Severity was not supplied and is not invented.
Transcripts use canonical words with ASR whole-word insertions, omissions and repetitions; same-position substitutions keep canonical words, contractions follow ASR, and mumbling units retain canonical words. Numbers are expanded. These rule-authorised transcripts are not independently verified verbatim. Canonical units remain Gettysburg 1–10 and Reagan 1–17, stopping at “discover its truths.” Structural edits: `data/human/review/TRANSCRIPT_DIFFS.md`.
The predeclared six scored takes contain 13 declared flaws. Both spontaneous take04s have unknown flaws and are excluded from all hit/miss/FP calculations, not labelled clean. Requested scope is A for eight takes, B02/03 versus own01, and C for both take04s. Completed jobs are listed below; any processing failure makes the workflow INCOMPLETE. B never counts reference durations.
Localized spans are fixed from MFA word times: larger|sense, were|daring; units 8/9 and 14/15; last four words for trail-off; have thus far for dragging; whole unit otherwise. Gaps below 30 ms use a centred 30 ms event, declared before inference to match the frozen detector event representation. No detection results are used to place labels.
Primary: same type, one-to-one greedy IoU ≥ 0.3 for all types. Historical pause policy additionally uses pause-centre distance ≤ 0.25 s. Secondary: same type, any positive overlap with the labelled canonical unit, one-to-one. Raw/trim offsets and exact spans are in `data/human/evaluation.json`.
Native 48 kHz mono PCM16 raw WAVs and original ALAC files remain byte-unchanged. Upload conversion is 44.1 kHz mono PCM16, without gain, loudness normalization or filtering; prepared audio is lossless FLAC. Import QA: `data/human/import_manifest.json`. No detector thresholds, bins, weights or rules were tuned on these takes.
Human agreement was not measured: no independent raters were available; no AI or self-ratings were used. The rating pack/scripts are ready for future independent collection, with zero responses. Reagan has one expert reader, not a multi-reader empirical distribution.

## Frozen v1 — primary

| Take | Mode | Labels | Flags | Primary H/M/FP | Historical H/M/FP | Secondary H/M/FP | Dashboard |
|---|---|---:|---:|---|---|---|---|
| gettysburg__user__take01 | A | 0 | 9 | 0/0/9 | 0/0/9 | 0/0/9 | [Open](http://localhost:8080/results/0aae3748f747b13e89697e17) |
| gettysburg__user__take02 | A | 3 | 7 | 1/2/6 | 1/2/6 | 2/1/5 | [Open](http://localhost:8080/results/fef67fa2213341586f06ae19) |
| gettysburg__user__take02 | B | 3 | 13 | 1/2/12 | 1/2/12 | 1/2/12 | [Open](http://localhost:8080/results/6d8cbd6dec22ffc8f7827ebc) |
| gettysburg__user__take03 | A | 4 | 13 | 1/3/12 | 1/3/12 | 1/3/12 | [Open](http://localhost:8080/results/48f109663821934f4d6dc880) |
| gettysburg__user__take03 | B | 4 | 17 | 0/4/17 | 0/4/17 | 1/3/16 | [Open](http://localhost:8080/results/9a1e6c9b493bf38f97547c38) |
| gettysburg__user__take04 | A | unknown; excluded | 8 | excluded | excluded | excluded | [Open](http://localhost:8080/results/8e00a502dc970fc55000ec6a) |
| gettysburg__user__take04 | C | unknown; excluded | 9 | excluded | excluded | excluded | [Open](http://localhost:8080/results/b77c9d634e3c6d1d954f9989) |
| reagan_challenger__user__take01 | A | 0 | 14 | 0/0/14 | 0/0/14 | 0/0/14 | [Open](http://localhost:8080/results/57a55f0d18b627cda376b6aa) |
| reagan_challenger__user__take02 | A | 3 | 22 | 1/2/21 | 1/2/21 | 2/1/20 | [Open](http://localhost:8080/results/f76f550c01af931b64ea839b) |
| reagan_challenger__user__take02 | B | 3 | 14 | 1/2/13 | 1/2/13 | 1/2/13 | [Open](http://localhost:8080/results/d48bda35d22f96206a0ae2d7) |
| reagan_challenger__user__take03 | A | 3 | 16 | 1/2/15 | 1/2/15 | 1/2/15 | [Open](http://localhost:8080/results/940ff757c37df7af5db66146) |
| reagan_challenger__user__take03 | B | 3 | 19 | 1/2/18 | 1/2/18 | 1/2/18 | [Open](http://localhost:8080/results/b6890ffc341c98cd10d65a23) |
| reagan_challenger__user__take04 | A | unknown; excluded | 15 | excluded | excluded | excluded | [Open](http://localhost:8080/results/37e462f26a807a19c1dd4b2b) |
| reagan_challenger__user__take04 | C | unknown; excluded | 10 | excluded | excluded | excluded | [Open](http://localhost:8080/results/7f5552c3946a1dd0769ce02b) |

## post-hoc v2; test split was seen with v1, so results are optimistic

| Take | Mode | Labels | Flags | Primary H/M/FP | Historical H/M/FP | Secondary H/M/FP | Dashboard |
|---|---|---:|---:|---|---|---|---|
| gettysburg__user__take01 | A | 0 | 7 | 0/0/7 | 0/0/7 | 0/0/7 | [Open](http://localhost:8080/results/a45acf09d05328fd5a2ed22f) |
| gettysburg__user__take02 | A | 3 | 7 | 1/2/6 | 1/2/6 | 2/1/5 | [Open](http://localhost:8080/results/79fa3bca5e4f0e628f68c248) |
| gettysburg__user__take02 | B | 3 | 9 | 1/2/8 | 1/2/8 | 1/2/8 | [Open](http://localhost:8080/results/169576531217c5dd52c0218c) |
| gettysburg__user__take03 | A | 4 | 10 | 1/3/9 | 1/3/9 | 1/3/9 | [Open](http://localhost:8080/results/6a6c2162a1d1dff873520eca) |
| gettysburg__user__take03 | B | 4 | 9 | 0/4/9 | 0/4/9 | 1/3/8 | [Open](http://localhost:8080/results/505e99a3727fff0850ff3483) |
| gettysburg__user__take04 | A | unknown; excluded | 7 | excluded | excluded | excluded | [Open](http://localhost:8080/results/1974ba6e2bd01c54a225bb90) |
| reagan_challenger__user__take01 | A | 0 | 11 | 0/0/11 | 0/0/11 | 0/0/11 | [Open](http://localhost:8080/results/481650a2d25463ca2e6bf57a) |
| reagan_challenger__user__take02 | A | 3 | 15 | 1/2/14 | 1/2/14 | 1/2/14 | [Open](http://localhost:8080/results/a319a08a897f396f43ddab40) |
| reagan_challenger__user__take02 | B | 3 | 5 | 1/2/4 | 1/2/4 | 1/2/4 | [Open](http://localhost:8080/results/3cf79b05b5f2cfd572fefd2d) |
| reagan_challenger__user__take03 | A | 3 | 12 | 1/2/11 | 1/2/11 | 1/2/11 | [Open](http://localhost:8080/results/bd8cad248693bebc07331de1) |
| reagan_challenger__user__take03 | B | 3 | 7 | 1/2/6 | 1/2/6 | 1/2/6 | [Open](http://localhost:8080/results/957a6bb4d47b5aed5800fc67) |
| reagan_challenger__user__take04 | A | unknown; excluded | 13 | excluded | excluded | excluded | [Open](http://localhost:8080/results/ac8ebc3c73982f5047ac68c8) |

## Pooled scored takes

The complete protocol has six distinct scored takes (01–03 of both texts) in A and four current takes in B, using two of those six as references. Actual completed denominators are shown below. If INCOMPLETE, these are partial pools, not full-cohort claims. A and B are separate evaluations, not ten independent recordings.

| Detector | Mode | Matcher | Current takes | Labels | Hits | Misses | FP | Minutes | FP/min |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| v1 | A | primary | 6 | 13 | 4 | 9 | 77 | 8.00 | 9.625 |
| v1 | A | historical_pause_policy | 6 | 13 | 4 | 9 | 77 | 8.00 | 9.625 |
| v1 | A | secondary | 6 | 13 | 6 | 7 | 75 | 8.00 | 9.375 |
| v1 | B | primary | 4 | 13 | 3 | 10 | 60 | 5.34 | 11.236 |
| v1 | B | historical_pause_policy | 4 | 13 | 3 | 10 | 60 | 5.34 | 11.236 |
| v1 | B | secondary | 4 | 13 | 4 | 9 | 59 | 5.34 | 11.049 |
| v2 | A | primary | 6 | 13 | 4 | 9 | 58 | 8.00 | 7.250 |
| v2 | A | historical_pause_policy | 6 | 13 | 4 | 9 | 58 | 8.00 | 7.250 |
| v2 | A | secondary | 6 | 13 | 5 | 8 | 57 | 8.00 | 7.125 |
| v2 | B | primary | 4 | 13 | 3 | 10 | 27 | 5.34 | 5.056 |
| v2 | B | historical_pause_policy | 4 | 13 | 3 | 10 | 27 | 5.34 | 5.056 |
| v2 | B | secondary | 4 | 13 | 4 | 9 | 26 | 5.34 | 4.869 |

Take01 flags are reported explicitly in the Flags column and count as false positives because those takes are declared natural readings with no delivery-flaw labels. Slips and mispronunciations are not automatically delivery flaws.

## Provenance and reproducibility

Initial recorder-input freeze: `c1a6a02`; final pre-inference unit-map/label protocol freeze: `a138825`; execution-environment adapter: `036363c`. Confirmation SHA256: `5f1d78bf2bc74709be418d9d5aee72aebc108741b2c4200cc044284216efbeac`.
Frozen code/config hashes, one-shot benchmark marker and all 16 original/raw hashes verified before and after inference. The existing v2 benchmark one-shot was not rerun. Genuine human inference is separate from the synthetic test benchmark. Human audio remains git-ignored and excluded from the public archive.
The real API jobs persist under data/app/jobs; v2 results are published as separately identified completed jobs without changing their scientific JSON. The dashboard displays the user's prepared waveform/audio, not reference audio; the same-words baseline is a separate playback.
The first host-side v2 attempt correctly rejected Docker-produced absolute model-path provenance. Running unchanged v2 in the existing API container resolved it without bypassing checks, regenerating labels or tuning. Historical attempt evidence: `data/human/runtime_attempts.json`; no unresolved processing problems remain in the completed run.
Repeat-output hashes and live API/history/tracks/audio checks: `data/human/verification.json`. This is byte-identity evidence using the retained real-MFA cache, not a second independent alignment-accuracy experiment.

Re-run from WSL `~/speech-eval` with the existing Docker API healthy:

```sh
env -u PYTHONPATH ~/.local/bin/uv run python scripts/prepare_human_confirmation.py
env -u PYTHONPATH ~/.local/bin/uv run python scripts/analyze_human.py --detector both --v2-runtime docker
env -u PYTHONPATH ~/.local/bin/uv run python scripts/report_human_demo.py --hits
```

## False-alarm breakdown (primary IoU >=0.3)

Counts below are unmatched predictions, not independently verified delivery errors. No unlabelled difference is reclassified as a hit. Unknown take04s show flags only, with no false-alarm claim.

| Detector | Take | Mode | Rushing | Dragging | Monotone | Too quiet | Mumbling | Awkward pause | Missing pause | FP | Missing-pause share | Rushing share |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | gettysburg__user__take01 | A | 1 | 0 | 0 | 0 | 0 | 1 | 7 | 9 | 77.8% | 11.1% |
| v2 | gettysburg__user__take01 | A | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 7 | 100.0% | 0.0% |
| v1 | gettysburg__user__take02 | A | 2 | 0 | 0 | 0 | 0 | 0 | 4 | 6 | 66.7% | 33.3% |
| v2 | gettysburg__user__take02 | A | 2 | 0 | 0 | 0 | 0 | 0 | 4 | 6 | 66.7% | 33.3% |
| v1 | gettysburg__user__take02 | B | 0 | 0 | 0 | 0 | 0 | 4 | 8 | 12 | 66.7% | 0.0% |
| v2 | gettysburg__user__take02 | B | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 8 | 100.0% | 0.0% |
| v1 | gettysburg__user__take03 | A | 2 | 0 | 0 | 0 | 0 | 2 | 8 | 12 | 66.7% | 16.7% |
| v2 | gettysburg__user__take03 | A | 0 | 0 | 0 | 0 | 0 | 0 | 9 | 9 | 100.0% | 0.0% |
| v1 | gettysburg__user__take03 | B | 0 | 0 | 1 | 0 | 0 | 8 | 8 | 17 | 47.1% | 0.0% |
| v2 | gettysburg__user__take03 | B | 0 | 0 | 1 | 0 | 0 | 0 | 8 | 9 | 88.9% | 0.0% |
| v1 | gettysburg__user__take04 | A | 1 | 0 | 0 | 0 | 0 | 1 | 6 | excluded; flags only | excluded | excluded |
| v2 | gettysburg__user__take04 | A | 0 | 0 | 0 | 0 | 0 | 1 | 6 | excluded; flags only | excluded | excluded |
| v1 | reagan_challenger__user__take01 | A | 0 | 0 | 0 | 0 | 0 | 3 | 11 | 14 | 78.6% | 0.0% |
| v2 | reagan_challenger__user__take01 | A | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 11 | 100.0% | 0.0% |
| v1 | reagan_challenger__user__take02 | A | 1 | 2 | 0 | 0 | 0 | 5 | 13 | 21 | 61.9% | 4.8% |
| v2 | reagan_challenger__user__take02 | A | 0 | 1 | 0 | 0 | 0 | 0 | 13 | 14 | 92.9% | 0.0% |
| v1 | reagan_challenger__user__take02 | B | 0 | 1 | 0 | 0 | 0 | 8 | 4 | 13 | 30.8% | 0.0% |
| v2 | reagan_challenger__user__take02 | B | 0 | 1 | 0 | 0 | 0 | 0 | 3 | 4 | 75.0% | 0.0% |
| v1 | reagan_challenger__user__take03 | A | 1 | 1 | 0 | 0 | 0 | 3 | 10 | 15 | 66.7% | 6.7% |
| v2 | reagan_challenger__user__take03 | A | 0 | 1 | 0 | 0 | 0 | 0 | 10 | 11 | 90.9% | 0.0% |
| v1 | reagan_challenger__user__take03 | B | 0 | 0 | 0 | 0 | 0 | 12 | 6 | 18 | 33.3% | 0.0% |
| v2 | reagan_challenger__user__take03 | B | 0 | 0 | 0 | 0 | 0 | 0 | 6 | 6 | 100.0% | 0.0% |
| v1 | reagan_challenger__user__take04 | A | 0 | 0 | 0 | 0 | 0 | 2 | 13 | excluded; flags only | excluded | excluded |
| v2 | reagan_challenger__user__take04 | A | 0 | 0 | 0 | 0 | 0 | 0 | 13 | excluded; flags only | excluded | excluded |

Take01 rows give flags by type explicitly: all are unmatched because no delivery flaws were declared. Slips are not delivery labels.

| Detector / mode | FP | Missing pause | Rushing | Combined share |
|---|---:|---:|---:|---:|
| v1 / A | 77 | 53 (68.8%) | 7 (9.1%) | 77.9% |
| v1 / B | 60 | 26 (43.3%) | 0 (0.0%) | 43.3% |
| v2 / A | 58 | 54 (93.1%) | 2 (3.4%) | 96.6% |
| v2 / B | 27 | 25 (92.6%) | 0 (0.0%) | 92.6% |

## Same-text reference duration and pause context

Timing uses retained real MFA, not listening. Inter-word pause is the sum of positive gaps between consecutive aligned words; it is not a new detector feature. Compare the same excerpt, not the full 249.13 s Reagan speech.

| Text | Reference readers | Prepared audio range (s) | Same-text aligned span range (s) | Inter-word pause range (s) |
|---|---:|---:|---:|---:|
| gettysburg | 10 | 102.88-190.95 | 101.57-190.55 | 11.78-68.27 |
| reagan_challenger | 1 | 249.13-249.13 | 90.17-90.17 | 27.01-27.01 |

| Take | Prepared duration (s) | Same-text aligned span (s) | Inter-word pause (s) |
|---|---:|---:|---:|
| gettysburg__user__take01 | 83.21 | 82.21 | 12.74 |
| gettysburg__user__take02 | 83.03 | 82.75 | 14.06 |
| gettysburg__user__take03 | 80.99 | 80.56 | 11.28 |
| gettysburg__user__take04 | 86.81 | 86.50 | 19.43 |
| reagan_challenger__user__take01 | 76.42 | 76.05 | 16.06 |
| reagan_challenger__user__take02 | 76.94 | 76.25 | 16.81 |
| reagan_challenger__user__take03 | 79.43 | 77.26 | 15.03 |
| reagan_challenger__user__take04 | 80.29 | 78.84 | 16.24 |

Gettysburg reference readers are the ten actual Mode-A train readers, not all fifteen available readers. Reagan has one reference: its first 17 canonical units, ending “discover its truths.”, are compared with the recordings. Duration alone does not establish faster delivery in every sentence, and fewer total gap seconds does not mean every individual pause is shorter.

Machine-readable full precision and reference IDs: `data/human/demo_evidence.json`. Frozen genuine evaluation JSON is unchanged.

## Exact primary hits for the video

Four Mode-A hits for each version, plus three Mode-B hits for each version. A/B are separate comparisons of the same takes, not fourteen independent human events. Intervals are trimmed participant seconds. Explanations are quoted verbatim from the live API presentation shown in the dashboard; raw scientific explanation strings and z values remain unchanged.

| Version | Take | Mode | Type | Detected interval (s) | Label interval (s) | Dashboard explanation (verbatim) |
|---|---|---|---|---|---|---|
| v1 | [gettysburg__user__take02](http://localhost:8080/results/fef67fa2213341586f06ae19) | A | awkward_pause | 29.900-31.470 | 29.900-31.470 | 29.90–31.47 s, "larger sense,": you paused 1.57 s between "larger" and "sense,", where good readers do not pause (1.57 s longer, more than 10 SD above). It breaks the sentence. |
| v2 | [gettysburg__user__take02](http://localhost:8080/results/79fa3bca5e4f0e628f68c248) | A | awkward_pause | 29.900-31.470 | 29.900-31.470 | 29.90–31.47 s, "larger sense,": you paused 1.57 s between "larger" and "sense,", where good readers do not pause (1.57 s longer, more than 10 SD above). It breaks the sentence. |
| v1 | [gettysburg__user__take02](http://localhost:8080/results/6d8cbd6dec22ffc8f7827ebc) | B | awkward_pause | 29.900-31.470 | 29.900-31.470 | 29.90–31.47 s, "larger sense,": you paused 1.57 s between "larger" and "sense,", where your previous take had no pause (1.57 s longer, more than 10 SD above). It breaks the sentence. |
| v2 | [gettysburg__user__take02](http://localhost:8080/results/169576531217c5dd52c0218c) | B | awkward_pause | 29.900-31.470 | 29.900-31.470 | 29.90–31.47 s, "larger sense,": you paused 1.57 s between "larger" and "sense,", where your previous take had no pause (1.57 s longer, more than 10 SD above). It breaks the sentence. |
| v1 | [gettysburg__user__take03](http://localhost:8080/results/48f109663821934f4d6dc880) | A | missing_pause | 47.055-47.085 | 47.055-47.085 | 47.05–47.09 s, "here. It": you left no pause after "here." where good readers pause 1.39 s (1.39 s shorter, more than 10 SD below). The listener gets no breathing space. |
| v2 | [gettysburg__user__take03](http://localhost:8080/results/6a6c2162a1d1dff873520eca) | A | missing_pause | 47.055-47.085 | 47.055-47.085 | 47.05–47.09 s, "here. It": you left no pause after "here." where good readers pause 1.39 s (1.39 s shorter, more than 10 SD below). The listener gets no breathing space. |
| v1 | [reagan_challenger__user__take02](http://localhost:8080/results/f76f550c01af931b64ea839b) | A | awkward_pause | 63.130-64.690 | 63.130-64.690 | 63.13–64.69 s, "were daring": you paused 1.56 s between "were" and "daring", where good readers do not pause (1.56 s longer, more than 10 SD above). It breaks the sentence. |
| v2 | [reagan_challenger__user__take02](http://localhost:8080/results/a319a08a897f396f43ddab40) | A | awkward_pause | 63.130-64.690 | 63.130-64.690 | 63.13–64.69 s, "were daring": you paused 1.56 s between "were" and "daring", where good readers do not pause (1.56 s longer, more than 10 SD above). It breaks the sentence. |
| v1 | [reagan_challenger__user__take02](http://localhost:8080/results/d48bda35d22f96206a0ae2d7) | B | awkward_pause | 63.130-64.690 | 63.130-64.690 | 63.13–64.69 s, "were daring": you paused 1.56 s between "were" and "daring", where your previous take pause 0.37 s (1.19 s longer, more than 10 SD above). It breaks the sentence. |
| v2 | [reagan_challenger__user__take02](http://localhost:8080/results/3cf79b05b5f2cfd572fefd2d) | B | awkward_pause | 63.130-64.690 | 63.130-64.690 | 63.13–64.69 s, "were daring": you paused 1.56 s between "were" and "daring", where your previous take pause 0.37 s (1.19 s longer, more than 10 SD above). It breaks the sentence. |
| v1 | [reagan_challenger__user__take03](http://localhost:8080/results/940ff757c37df7af5db66146) | A | missing_pause | 63.205-63.235 | 63.205-63.235 | 63.20–63.23 s, "tragedy. But": you left no pause after "tragedy." where good readers pause 0.77 s (0.77 s shorter, more than 10 SD below). The listener gets no breathing space. |
| v2 | [reagan_challenger__user__take03](http://localhost:8080/results/bd8cad248693bebc07331de1) | A | missing_pause | 63.205-63.235 | 63.205-63.235 | 63.20–63.23 s, "tragedy. But": you left no pause after "tragedy." where good readers pause 0.77 s (0.77 s shorter, more than 10 SD below). The listener gets no breathing space. |
| v1 | [reagan_challenger__user__take03](http://localhost:8080/results/b6890ffc341c98cd10d65a23) | B | missing_pause | 63.205-63.235 | 63.205-63.235 | 63.20–63.23 s, "tragedy. But": you left no pause after "tragedy." where your previous take pause 0.40 s (0.40 s shorter, more than 10 SD below). The listener gets no breathing space. |
| v2 | [reagan_challenger__user__take03](http://localhost:8080/results/957a6bb4d47b5aed5800fc67) | B | missing_pause | 63.205-63.235 | 63.205-63.235 | 63.20–63.23 s, "tragedy. But": you left no pause after "tragedy." where your previous take pause 0.40 s (0.40 s shorter, more than 10 SD below). The listener gets no breathing space. |

Suggested demonstrable primary hit: frozen v1 Gettysburg take02 Mode B, awkward pause at larger|sense, detected and labelled 29.900-31.470 s. This is a declared recorder-confirmed pause, not an independent perceptual rating.

## Why mostly pause flags

Read-only diagnosis of frozen v1 genuine takes. No detector, threshold, score or feature changes; no new human inference or synthetic test benchmark evaluation. All recorder-confirmed declared flaws are listed below (26 A/B comparisons of 13 labels). Monotone and mumbling were declared in take03, not take02. G = Gettysburg, R = Reagan Challenger. Take04 has unknown labels and contributes only to the flags table, not the distributions or hit counts.

**Feature evidence and near misses.** A/B use ±3.5 SD. Rate is the 3-word-window syllable rate (one neighbour on either side, restricted to the sentence), pitchvar is window pitch standard deviation, loud is window mean intensity relative to the speaker median, and clarity is window mean high-band energy ratio. Mumbling evaluates clarity alone. Pause is the gap before the boundary word. z = (transformed measured value − reference centre) / shrunk reference sigma. Measured and reference values below are in physical units; z is calculated after the stated transform, rounded to the detector’s four significant digits. Each row shows the strongest z **in the flaw direction** within the exact declared span, plus median z and threshold-crossing word count. It does not represent a unit-averaged detector or imply a hit. Full per-word values and reference sigma are in `phase10_human_near_misses.json`.

Non-pause rules require at least 3 flagged words in a sentence with at most 1 intervening word; unmatched/invalid evidence breaks a run. Pause flags additionally require gap ≥0.45 s (awkward), or reference gap ≥0.3 s and participant gap ≤40% of reference (missing). Ordered containment suppression still applies. A hit below means the original frozen same-type, one-to-one strict IoU ≥0.3 pair; a flag elsewhere is not a labelled hit.

| Take | Mode | Unit / flaw | Feature (physical units) | Measured | Reference | z (strongest signed) | Median z | Threshold | Words crossing / finite | Primary hit |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| G take02 | A | 4 / rushing | rate (syllables/s (log transformed)) | 4.762 | 2.778 | 5.26 | 2.705 | 3.5 | 8/26 | no |
| G take02 | A | 6 / awkward_pause | pause (seconds (log +0.05)) | 1.57 | 6.93889e-18 | 6024 | 6024 | 3.5 | 1/1 | yes |
| G take02 | A | 8 / too_quiet | loud (dB relative to speaker median) | -5.259 | -8.7095 | 0.7644 | 2.00755 | 3.5 | 0/4 | no |
| G take02 | B | 4 / rushing | rate (syllables/s (log transformed)) | 4.412 | 2.703 | 3.284 | 1.444 | 3.5 | 0/26 | no |
| G take02 | B | 6 / awkward_pause | pause (seconds (log +0.05)) | 1.57 | 6.93889e-18 | 3810 | 3810 | 3.5 | 1/1 | yes |
| G take02 | B | 8 / too_quiet | loud (dB relative to speaker median) | -7.414 | -0.136 | -2.788 | -1.22288 | 3.5 | 0/4 | no |
| G take03 | A | 2 / monotone | pitchvar (semitones (log +0.5)) | 1.198 | 2.99258 | -3.249 | 0.28975 | 3.5 | 0/24 | no |
| G take03 | A | 7 / mumbling | clarity (high-band ratio dB) | -18.27 | -14.575 | -0.9724 | 0.2891 | 3.5 | 0/21 | no |
| G take03 | A | 8 / missing_pause | pause (seconds (log +0.05)) | 6.93889e-18 | 1.38652 | -13.09 | -13.09 | 3.5 | 1/1 | yes |
| G take03 | A | 9 / dragging | rate (syllables/s (log transformed)) | 2.206 | 3.10912 | -2.614 | 1.037 | 3.5 | 0/3 | no |
| G take03 | B | 2 / monotone | pitchvar (semitones (log +0.5)) | 0.7396 | 3.117 | -4.368 | -0.87785 | 3.5 | 1/24 | no |
| G take03 | B | 7 / mumbling | clarity (high-band ratio dB) | -18.27 | -15.87 | -0.5563 | 0.1321 | 3.5 | 0/21 | no |
| G take03 | B | 8 / missing_pause | pause (seconds (log +0.05)) | 6.93889e-18 | 0.26 | -1999 | -1999 | 3.5 | 1/1 | no |
| G take03 | B | 9 / dragging | rate (syllables/s (log transformed)) | 2.206 | 2.256 | -0.1502 | 2.052 | 3.5 | 0/3 | no |
| R take02 | A | 10 / rushing | rate (syllables/s (log transformed)) | 8.108 | 4 | 4.736 | 2.2005 | 3.5 | 3/18 | no |
| R take02 | A | 15 / too_quiet | loud (dB relative to speaker median) | -6.128 | -7.424 | 0.4965 | 0.8218 | 3.5 | 0/4 | no |
| R take02 | A | 16 / awkward_pause | pause (seconds (log +0.05)) | 1.56 | 6.93889e-18 | 3803 | 3803 | 3.5 | 1/1 | yes |
| R take02 | B | 10 / rushing | rate (syllables/s (log transformed)) | 6.667 | 5.263 | 1.585 | 0.6228 | 3.5 | 0/17 | no |
| R take02 | B | 15 / too_quiet | loud (dB relative to speaker median) | -6.53 | -3.72 | -1.077 | 0.76505 | 3.5 | 0/4 | no |
| R take02 | B | 16 / awkward_pause | pause (seconds (log +0.05)) | 1.56 | 0.37 | 1472 | 1472 | 3.5 | 1/1 | yes |
| R take03 | A | 6 / monotone | pitchvar (semitones (log +0.5)) | 1.659 | 1.774 | -0.2087 | 2.1295 | 3.5 | 0/18 | no |
| R take03 | A | 9 / mumbling | clarity (high-band ratio dB) | -15.75 | -3.578 | -2.821 | -1.776 | 3.5 | 0/14 | no |
| R take03 | A | 14 / missing_pause | pause (seconds (log +0.05)) | 6.93889e-18 | 0.772 | -3067 | -3067 | 3.5 | 1/1 | yes |
| R take03 | B | 6 / monotone | pitchvar (semitones (log +0.5)) | 1.659 | 5.576 | -3.98 | -1.1875 | 3.5 | 1/18 | no |
| R take03 | B | 9 / mumbling | clarity (high-band ratio dB) | -23.74 | -17.84 | -1.368 | 0.08113 | 3.5 | 0/13 | no |
| R take03 | B | 14 / missing_pause | pause (seconds (log +0.05)) | 6.93889e-18 | 0.4 | -2407 | -2407 | 3.5 | 1/1 | yes |

**All stored flags by type per take.** Includes matched and unmatched flags; zeros are explicit.

| Take | Mode | Rushing | Dragging | Monotone | Too quiet | Mumbling | Awkward pause | Missing pause | Total |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| G take01 | A | 1 | 0 | 0 | 0 | 0 | 1 | 7 | 9 |
| G take02 | A | 2 | 0 | 0 | 0 | 0 | 1 | 4 | 7 |
| G take02 | B | 0 | 0 | 0 | 0 | 0 | 5 | 8 | 13 |
| G take03 | A | 2 | 0 | 0 | 0 | 0 | 2 | 9 | 13 |
| G take03 | B | 0 | 0 | 1 | 0 | 0 | 8 | 8 | 17 |
| G take04 (unknown labels) | A | 1 | 0 | 0 | 0 | 0 | 1 | 6 | 8 |
| R take01 | A | 0 | 0 | 0 | 0 | 0 | 3 | 11 | 14 |
| R take02 | A | 1 | 2 | 0 | 0 | 0 | 6 | 13 | 22 |
| R take02 | B | 0 | 1 | 0 | 0 | 0 | 9 | 4 | 14 |
| R take03 | A | 1 | 1 | 0 | 0 | 0 | 3 | 11 | 16 |
| R take03 | B | 0 | 0 | 0 | 0 | 0 | 12 | 7 | 19 |
| R take04 (unknown labels) | A | 0 | 0 | 0 | 0 | 0 | 2 | 13 | 15 |

**Distribution of |z| on the scored takes.** A: six takes01–03. B: four current takes02–03 versus own take01. Pause flags use each retained region’s evidence z. Non-pause feature samples use every finite word × feature in rate/pitchvar/loud/clarity, including subthreshold values. These populations have different sampling units; repeated overlapping windows are correlated. All pause-feature and non-pause-flag distributions are also shown to make the distinction explicit.

| Mode | Population | n | Minimum | p25 | Median | p75 | p95 | Maximum |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A | pause flags | 71 | 3.953 | 11.315 | 1150 | 2193 | 3895.5 | 6024 |
| A | non-pause flags | 10 | 3.929 | 4.1032 | 4.1865 | 4.3442 | 6.1814 | 7.369 |
| A | non-pause features (all words) | 5909 | 0 | 0.5716 | 1.23 | 2.085 | 3.8096 | 9.58 |
| A | pause feature (all words) | 1398 | 0 | 0 | 0 | 0.8261 | 1786.4 | 6024 |
| B | pause flags | 61 | 19.05 | 315.1 | 1122 | 2331 | 2875 | 3810 |
| B | non-pause features (all words) | 3944 | 0 | 0.39537 | 0.84505 | 1.472 | 2.8859 | 6.806 |
| B | pause feature (all words) | 924 | 0 | 0 | 0 | 43.363 | 1847 | 3810 |
| B | non-pause flags | 2 | 4.635 | 4.7505 | 4.866 | 4.9815 | 5.0739 | 5.097 |

| Mode / population | Absolute z <1 | 1–<2 | 2–<3.5 | 3.5–<10 | 10–<100 | 100–<1000 | 1000–<10000 | ≥10000 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A / pause flags | 0 | 0 | 0 | 17 | 8 | 6 | 40 | 0 |
| A / non-pause features (all words) | 2449 | 1855 | 1203 | 402 | 0 | 0 | 0 | 0 |
| B / pause flags | 0 | 0 | 0 | 0 | 7 | 22 | 32 | 0 |
| B / non-pause features (all words) | 2257 | 1165 | 434 | 88 | 0 | 0 | 0 | 0 |

**Why pauses dominate.** The pooled training pause spread is near zero because most aligned word boundaries have no gap; its median robust spread is zero before the numerical safeguard. There is no substantive pause sigma floor in v1: `reference.py` has a generic numerical `SCALE_FLOOR = .001` in transformed units, but no pause-specific timing/noise floor. The pooled pause sigma is .001; shrinking toward it can make the per-boundary sigma even smaller. This is not literally a zero denominator. Tiny timing changes at low-spread boundaries can therefore produce very large z, while real monotone/mumbling/rate/volume edits may remain within their broader reference distributions or fail the region/localization gates. Some Mode-A boundaries have substantial reader spread, so not every pause has tiny sigma. The comparison is especially sensitive in B (one previous take) and Reagan A (one expert reader). No fix in v1.

| Mode | Reference feature sigma (transformed units; word-weighted) | n | Minimum | Median | p95 | Maximum |
|---|---|---:|---:|---:|---:|---:|
| A | clarity | 1478 | 2.93345 | 4.31403 | 5.7062 | 7.63711 |
| A | loud | 1478 | 1.69505 | 2.61008 | 7.19489 | 11.194 |
| A | pitchvar | 1475 | 0.180199 | 0.280344 | 0.429282 | 0.660461 |
| A | rate | 1478 | 0.102469 | 0.149199 | 0.255762 | 0.477201 |
| A | pause | 1398 | 0.00057735 | 0.000912871 | 0.661693 | 1.47299 |
| B | clarity | 986 | 4.31403 | 4.31403 | 4.31403 | 4.31403 |
| B | loud | 986 | 2.61008 | 2.61008 | 2.61008 | 2.61008 |
| B | pitchvar | 986 | 0.280344 | 0.280344 | 0.280344 | 0.280344 |
| B | rate | 986 | 0.149199 | 0.149199 | 0.149199 | 0.149199 |
| B | pause | 924 | 0.000912871 | 0.000912871 | 0.000912871 | 0.000912871 |

Smallest stored awkward-pause differences (still subject to the ≥0.45 s gate): 0.49 s versus 0.48 s, Δ=0.01 s, z=20.48; 0.5 s versus 0.49 s, Δ=0.01 s, z=20.1; 0.53 s versus 0.52 s, Δ=0.01 s, z=19.05.

Reproduce this read-only analysis: `env -u PYTHONPATH .venv/bin/python scripts/diagnose_human_near_misses.py`. Stored artifact hashes are checked against the retained producer state; runtime/model-path identity is not re-executed or rewritten. Genuine evaluation bytes and primary pairs remain unchanged.

### DEV rule activation audit

No detector activation bug found; no post-hoc detector bug fix and **zero benchmark test reruns**. All seven A/B rules and all five supported C-lite rules fire in isolated feature probes using the unchanged configuration. The probes are fabricated feature evidence, separate from the real DEV audio runs below. A non-hit on one selected audio file does not mean the rule is disabled. C-lite intentionally does not implement mumbling or awkward_pause; its too_quiet rule measures final intensity drop, not general quietness. C retains its frozen feature threshold **2.0**, not A/B’s 3.5.

One preselected single-flaw synthetic DEV file per type was run once in each mode (7 files, 21 mode runs), using retained real alignment/features. A uses the train-reader distribution excluding the source speaker; B uses that DEV speaker’s original recording; C uses the retained train-only sentence norms. Selection was based on stored DEV examples and strongest injection severity (severity 4 trail shape for quietness, since C supports sentence-final drop); it is a diagnostic sample, not a new performance estimate. No new feature extraction or benchmark test evaluation.

| Injected flaw / recording | Severity | Mode | Target type supported | All fired types (counts) | Target type fires anywhere | Same-type IoU ≥0.3 hit |
|---|---:|---|---|---|---|---|
| o_captain__lv_s__rushing_s5_01 | 5 | A | yes | awkward_pause (2), rushing (1), too_quiet (1) | yes | yes |
| o_captain__lv_s__rushing_s5_01 | 5 | B | yes | awkward_pause (5), rushing (1) | yes | yes |
| o_captain__lv_s__rushing_s5_01 | 5 | C | yes | dragging (3), missing_pause (1), too_quiet (1) | no | no |
| gettysburg__lv_pc__dragging_s5_01 | 5 | A | yes | awkward_pause (1) | no | no |
| gettysburg__lv_pc__dragging_s5_01 | 5 | B | yes | awkward_pause (3), dragging (1) | yes | yes |
| gettysburg__lv_pc__dragging_s5_01 | 5 | C | yes | too_quiet (1) | no | no |
| o_captain__lv_sjs__monotone_s5_01 | 5 | A | yes | awkward_pause (7), too_quiet (3) | no | no |
| o_captain__lv_sjs__monotone_s5_01 | 5 | B | yes | awkward_pause (7), monotone (1) | yes | yes |
| o_captain__lv_sjs__monotone_s5_01 | 5 | C | yes | dragging (2), missing_pause (2), monotone (6), rushing (1) | yes | no |
| o_captain__lv_s__too_quiet_s4_01 | 4 | A | yes | awkward_pause (2), too_quiet (1) | yes | no |
| o_captain__lv_s__too_quiet_s4_01 | 4 | B | yes | awkward_pause (4) | no | no |
| o_captain__lv_s__too_quiet_s4_01 | 4 | C | yes | dragging (3), missing_pause (1), too_quiet (1) | yes | no |
| gettysburg__lv_rk__mumbling_s5_01 | 5 | A | yes | dragging (1), missing_pause (1), mumbling (1) | yes | yes |
| gettysburg__lv_rk__mumbling_s5_01 | 5 | B | yes | awkward_pause (2), mumbling (1), rushing (1) | yes | yes |
| gettysburg__lv_rk__mumbling_s5_01 | 5 | C | unsupported | too_quiet (1) | no | no |
| o_captain__lv_s__awkward_pause_s5_01 | 5 | A | yes | awkward_pause (3), too_quiet (2) | yes | yes |
| o_captain__lv_s__awkward_pause_s5_01 | 5 | B | yes | awkward_pause (4) | yes | yes |
| o_captain__lv_s__awkward_pause_s5_01 | 5 | C | unsupported | dragging (3), missing_pause (1), too_quiet (1) | no | no |
| o_captain__lv_s__missing_pause_s5_01 | 5 | A | yes | awkward_pause (2), missing_pause (1), too_quiet (1) | yes | yes |
| o_captain__lv_s__missing_pause_s5_01 | 5 | B | yes | awkward_pause (3), missing_pause (1) | yes | yes |
| o_captain__lv_s__missing_pause_s5_01 | 5 | C | yes | dragging (3), missing_pause (2), too_quiet (1) | yes | no |

Every A/B path calls the same `detect()` function. Its non-pause loop evaluates rate (positive rushing, negative dragging), pitchvar (negative monotone), loud (negative too_quiet), and clarity (negative mumbling); its boundary loop evaluates both pause types. C’s `sentence_regions()` evaluates rate both directions, pitchrange, final_drop and end_pause. The probes confirm all branches produce regions. DEV audio misses reflect measured evidence, threshold/region gates and word-versus-sentence aggregation, not disabled code. Full flags, references, activation probes and frozen hashes: `phase10_rule_coverage.json`. Reproduce DEV only: `env -u PYTHONPATH .venv/bin/python scripts/diagnose_rule_coverage.py`.
