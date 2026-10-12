# Phase 10 — genuine recorder-confirmed takes

COMPLETE: 8 distinct take(s) have completed analysis with real CPU MFA. Frozen v1 is primary; v2 is secondary.
post-hoc v2; test split was seen with v1, so results are optimistic.

Labels come from the recorder's 2026-10-12 confirmation of the planned script, not independent annotation or listening. The confirmation replaces manual TAKES_REVIEW markers. Severity was not supplied and is not invented.
Transcripts use canonical words with ASR whole-word insertions, omissions and repetitions; same-position substitutions keep canonical words, contractions follow ASR, and mumbling units retain canonical words. Numbers are expanded. These rule-authorised transcripts are not independently verified verbatim. Canonical units remain Gettysburg 1–10 and Reagan 1–17, stopping at “discover its truths.” Structural edits: `data/human/review/TRANSCRIPT_DIFFS.md`.
The predeclared six scored takes contain 13 declared flaws. Both spontaneous take04s have unknown flaws and are excluded from all hit/miss/FP calculations, not labelled clean. Requested scope is A for eight takes, B02/03 versus own01, and C for both take04s. Completed jobs are listed below; any processing failure makes the workflow INCOMPLETE. B never counts reference durations.
Localized spans are fixed from MFA word times: larger|sense, were|daring; units 8/9 and 14/15; last four words for trail-off; have thus far for dragging; whole unit otherwise. Gaps below 30 ms use a centred 30 ms event, declared before inference to match the frozen detector event representation. No detection results are used to place labels.
Primary: same type, one-to-one greedy IoU ≥ 0.3 for all types. Historical pause policy additionally uses pause-centre distance ≤ 0.25 s. Secondary: same type, any positive overlap with the labelled canonical unit, one-to-one. Raw/trim offsets and exact spans are in `data/human/evaluation.json`.
Native 48 kHz mono PCM16 raw WAVs and original ALAC files remain byte-unchanged. Upload conversion is 44.1 kHz mono PCM16, without gain, loudness normalization or filtering; prepared audio is lossless FLAC. Import QA: `data/human/import_manifest.json`. No detector thresholds, bins, weights or rules were tuned on these takes.
Independent human agreement is pending: the rating pack and scripts are ready, zero responses. No AI or self-ratings are rater data. Reagan has one expert reader, not a multi-reader empirical distribution.

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
```
