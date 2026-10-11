# Phase 11: report fixes and post-hoc detector v2

## Task 1: report presentation

The report now uses rounded display values, a three-sentence plain-language
opening, a five-line first-page summary, unique section numbers and one final
Pending items box. The original scientific JSON and frozen v1 outputs are
unchanged. Both requested dashboard screenshots are embedded as readable PDF
excerpts linked to the unmodified full originals. Natural pagination produces
five A4 pages instead of forced half-empty pages.

Section 4 quotes an actual explanation verbatim from analysis `86964ad39ead`,
test file `gettysburg__lv_sa__awkward_pause_s3_01`. Its first awkward-pause flag
matches the injected label under the frozen rule. This explicitly requested
existing test illustration is not an input to v2 tuning.

PDF repeat SHA256: `12951f9c053b9671bc3e85dd0308f8956ad55db6fe6a9f154b5d1ca4c5b55a5c`.
All five rendered pages inspected; 242 existing tests passed. PDF authoring
verification stores its own hash and does not replace scientific evidence.

## Task 2: protocol fixed before dev results

V1 remains frozen/published. V2 is explicitly post-hoc and will live alongside
it. Tune on DEV only, never `data/human` or test. Maximum 30 v2 configurations
and four hours of tuning, with every evaluated configuration logged here and
full-precision machine evidence retained separately. The v1 dev baseline is
measured on exactly the same rows/rule, not counted as a v2 configuration.

Objective: maximum dev F1 among configurations with clean alarms/min <=0.5;
deterministic ties prefer fewer clean alarms and then earlier configuration ID.
If none passes, report the best F1 candidate and explicitly state guard failure.

"Clear margin" is fixed now as both >=0.020 absolute dev F1 improvement and
>=10.0% relative improvement over v1, with the clean-alarm guard met. This is a
practical gate, not a significance claim. If not met, no v2 test run. If met,
commit/freeze v2 before a single test evaluation and disclose:
**post-hoc v2; test split was seen with v1, so results are optimistic**.

Use the unchanged matcher: same-type greedy one-to-one IoU >=0.3 for duration
regions; pause events use centre distance <=0.25 s. Use the same clean-duration
denominator, uncertainty exclusions, modes and severity strata for comparisons.

Task 1 committed/pushed: `032d9d1`. Task 2 implementation began before any new dev
numbers were inspected. The explicit test illustration above was completed first.

Search fixed before running: 18 combinations of reader k {2, 3.5, 5}, own-sentence
k {0.5, 1, 1.5} and two practical-effect profiles, then up to 12 unique duration/
merge combinations around the best dev first-stage candidate (one duplicate
removed). Duration grid {0.15, 0.4, 0.8, 1.2} seconds; merge gap {0.05, 0.2, 0.5}
seconds. Minimum three flagged words, one-word gap and v1 pause conditions remain.

Lenient / moderate effects: rate fraction 0.10 / 0.20; pitch variation reduction
0.20 / 0.35; relative loudness and clarity deficits 2 / 4 dB; excess pause
0.25 / 0.60 seconds; missing-pause deficit 0.10 / 0.25 seconds. Sentence contrasts
use real articulation rate and pitch range, plus the sentence median of valid
window loudness. Rate/range use log units. Robust scale floors are 0.05 log units
and 0.5 dB, with at least three valid sentences. These floors are numerical
stability choices, not optimised parameters. Invalid/uncertain sentences cannot
enter their own recording median. Mumbling and pause events have effect guards
but no invented within-recording clarity/pause norm.

The frozen split configuration is checked before opening dev measurements.
Human paths/IDs and mislabeled non-dev readers are rejected. V2 A/B inference is
explicit through `speecheval analyze ... --detector v2`; Mode C remains v1 and
rejects an explicit v2 request. V2 writes separately under `data/analyses_v2/`.
V1 `pipeline.py`, `detect.py`, calibration, references, features, evaluator and
threshold configuration remain byte-unchanged.

## V2 DEV configuration log

| ID | Reader k | Own k | Effects | Min s | Gap s | Precision | Recall | F1 | Clean/min | Guard |
|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1 | 2 | 0.5 | lenient | 0.4 | 0.2 | 0.046 | 0.494 | 0.084 | 6.153 | False |
| 2 | 2 | 0.5 | moderate | 0.4 | 0.2 | 0.059 | 0.482 | 0.105 | 4.649 | False |
| 3 | 2 | 1 | lenient | 0.4 | 0.2 | 0.049 | 0.451 | 0.089 | 5.606 | False |
| 4 | 2 | 1 | moderate | 0.4 | 0.2 | 0.066 | 0.439 | 0.115 | 4.102 | False |
| 5 | 2 | 1.5 | lenient | 0.4 | 0.2 | 0.053 | 0.427 | 0.095 | 4.512 | False |
| 6 | 2 | 1.5 | moderate | 0.4 | 0.2 | 0.076 | 0.415 | 0.128 | 3.008 | False |
| 7 | 3.5 | 0.5 | lenient | 0.4 | 0.2 | 0.098 | 0.311 | 0.149 | 1.504 | False |
| 8 | 3.5 | 0.5 | moderate | 0.4 | 0.2 | 0.135 | 0.299 | 0.186 | 0.957 | False |
| 9 | 3.5 | 1 | lenient | 0.4 | 0.2 | 0.096 | 0.299 | 0.145 | 1.504 | False |
| 10 | 3.5 | 1 | moderate | 0.4 | 0.2 | 0.131 | 0.287 | 0.180 | 0.957 | False |
| 11 | 3.5 | 1.5 | lenient | 0.4 | 0.2 | 0.108 | 0.287 | 0.157 | 1.231 | False |
| 12 | 3.5 | 1.5 | moderate | 0.4 | 0.2 | 0.161 | 0.274 | 0.203 | 0.684 | False |
| 13 | 5 | 0.5 | lenient | 0.4 | 0.2 | 0.130 | 0.213 | 0.161 | 0.820 | False |
| 14 | 5 | 0.5 | moderate | 0.4 | 0.2 | 0.173 | 0.201 | 0.186 | 0.547 | False |
| 15 | 5 | 1 | lenient | 0.4 | 0.2 | 0.130 | 0.213 | 0.162 | 0.820 | False |
| 16 | 5 | 1 | moderate | 0.4 | 0.2 | 0.174 | 0.201 | 0.186 | 0.547 | False |
| 17 | 5 | 1.5 | lenient | 0.4 | 0.2 | 0.131 | 0.213 | 0.162 | 0.820 | False |
| 18 | 5 | 1.5 | moderate | 0.4 | 0.2 | 0.175 | 0.201 | 0.187 | 0.547 | False |
| 19 | 3.5 | 1.5 | moderate | 0.15 | 0.05 | 0.171 | 0.250 | 0.203 | 0.684 | False |
| 20 | 3.5 | 1.5 | moderate | 0.15 | 0.2 | 0.161 | 0.274 | 0.203 | 0.684 | False |
| 21 | 3.5 | 1.5 | moderate | 0.15 | 0.5 | 0.174 | 0.299 | 0.220 | 0.684 | False |
| 22 | 3.5 | 1.5 | moderate | 0.4 | 0.05 | 0.171 | 0.250 | 0.203 | 0.684 | False |
| 23 | 3.5 | 1.5 | moderate | 0.4 | 0.5 | 0.174 | 0.299 | 0.220 | 0.684 | False |
| 24 | 3.5 | 1.5 | moderate | 0.8 | 0.05 | 0.165 | 0.238 | 0.195 | 0.684 | False |
| 25 | 3.5 | 1.5 | moderate | 0.8 | 0.2 | 0.156 | 0.262 | 0.195 | 0.684 | False |
| 26 | 3.5 | 1.5 | moderate | 0.8 | 0.5 | 0.171 | 0.293 | 0.216 | 0.684 | False |
| 27 | 3.5 | 1.5 | moderate | 1.2 | 0.05 | 0.142 | 0.195 | 0.165 | 0.684 | False |
| 28 | 3.5 | 1.5 | moderate | 1.2 | 0.2 | 0.154 | 0.213 | 0.179 | 0.684 | False |
| 29 | 3.5 | 1.5 | moderate | 1.2 | 0.5 | 0.179 | 0.256 | 0.211 | 0.684 | False |
| 30 | 3.5 | 1.5 | guard-repair | 0.15 | 0.5 | 0.192 | 0.256 | 0.219 | 0.410 | True |

## DEV decision and freeze preparation

Exactly 30 distinct v2 configurations were evaluated on 152 dev files. The
first 29 did not meet the guard. Trial 30 was an explicitly adaptive final
guard repair: use only selected-candidate clean-dev pause excesses, raise the
minimum to the next 50-ms point removing enough alarms for the remaining budget.
The resulting pause-excess threshold is 1.10 s, replacing 0.60 s; all other
trial-21 parameters stay unchanged. No test or human data selected this repair.

Selected configuration: 30. YAML SHA256:
`3496a9c3549e5491af708c70657f4d5f4d94e23e9f23fa597b46a6e34aa60538`.
Measured computation for the search and repair: 25.136 seconds, comfortably
inside the four-hour task window. Full configuration/metrics/provenance and
unrounded floats: `data/review/detector_v2_dev.json`.

| Type | v1 P | v2 P | v1 R | v2 R | v1 F1 | v2 F1 | v1 clean/min | v2 clean/min |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| awkward_pause | 0.050 | 0.102 | 0.870 | 0.478 | 0.095 | 0.168 | 1.367 | 0.273 |
| dragging | 0.500 | 1.000 | 0.087 | 0.043 | 0.148 | 0.083 | 0.000 | 0.000 |
| missing_pause | 0.156 | 0.156 | 0.304 | 0.304 | 0.206 | 0.206 | 0.137 | 0.137 |
| monotone | 0.778 | 1.000 | 0.304 | 0.087 | 0.438 | 0.160 | 0.000 | 0.000 |
| mumbling | 1.000 | 0.833 | 0.458 | 0.417 | 0.629 | 0.556 | 0.000 | 0.000 |
| rushing | 0.667 | 1.000 | 0.250 | 0.208 | 0.364 | 0.345 | 0.000 | 0.000 |
| too_quiet | 0.047 | 0.130 | 0.333 | 0.250 | 0.082 | 0.171 | 0.273 | 0.000 |
| overall | 0.094 | 0.192 | 0.372 | 0.256 | 0.150 | 0.219 | 1.777 | 0.410 |

Dev F1 intervals: v1 [0.117, 0.185], v2 [0.166, 0.271]. Selection used the
predeclared practical gate, not a significance claim or interval-overlap rule.
F1 clears both margins and clean alarms pass. Recall decreases; mild strengths
1/2 have zero overall recall in selected v2. Rushing recall also decreases on
dev. The within-recording AND rule can miss uniform recording-wide problems;
short/invalid sentence sets are unavailable evidence, not inferred good delivery.
This is a precision/clean-alarm trade-off, not universal detector improvement.

Before any v2 test evidence is opened, code/config/tests are reviewed, verified
and committed. A one-shot marker refuses another decision-bearing evaluation.
Fresh-clone numerical reruns are separately labelled frozen reproductions.

### Pre-freeze independent review

The review found no detector-scoring defect. Three regression tests first failed
because the gate trusted detached selected metrics/configuration and did not
enforce the DEV objective; they now pass after binding both to the selected
history entry, checking recorded configuration hashes and deterministic selection.
The parsed selected YAML must also equal that entry. Before consuming the marker,
preflight checks the manifest and v1 YAML against their byte-identical versions
in the original frozen scientific commit `aaf1832` (verified with `git show`).
This supplements, rather than rewrites, the original DEV provenance. The exact
requested disclaimer is used. No configuration, detector or DEV number changed.

Inherited inference limitation: Mode B's optional progress summary uses Mode A
for each take, requiring a same-text train/expert reference. Gettysburg and the
Reagan workflow have references; arbitrary custom texts do not. This is recorded
in `docs/BLOCKERS.md`, not silently fixed after DEV selection. The test comparison
path directly uses the earlier same-speaker recording and does not use that
inference progress wrapper. V2 does not claim new custom-text Mode B support.

## One-shot post-hoc v2 test results

Test JSON SHA256: `e770969c2d44e97cff3ee0d58b318d81edb8264356004070f6edfa4aa9f9c754`.
The exclusive marker records one decision-bearing evaluation. Frozen v1 metrics,
confidence intervals, file counts and uncertainty exclusions match the published
JSON exactly. No detector, evaluator or configuration changes follow this result.

A F1 changes only 0.190 to 0.193; recall falls 0.400 to 0.288. Clean alarms halve
but 0.671/min still fails the 0.5 guard on test. B F1 rises 0.035 to 0.070 and
precision 0.018 to 0.042, while recall falls 0.390 to 0.207. Neither setting
supports a claim of universal improvement. V1 remains the primary frozen result.

The six-page A4 report adds a secondary v2 section with the exact disclaimer;
all six rendered pages were visually inspected. Two renders are byte-identical:
SHA256 `5f4ab454589d77d43f146715dddb77a49f896363ce05125b12ace339e81a8cea`.
This is authoring evidence, not another scientific evaluation.

Fresh-clone v2 Docker reproduction is blocked by a Docker Desktop startup failure,
not a second scientific decision. WSL has no Docker command integration; Windows
Docker has no Linux-engine pipe. Startup logs identify an inaccessible stale
`dockerInference` endpoint. Startup and a recoverable endpoint rename failed;
no reset/deletion or settings change was attempted. The GitHub-clone target is
`/tmp/speech-eval-v2-3AIBAv/clone`; exact blocker and rerun command are in
`docs/BLOCKERS.md`. No fresh-clone v2 hash or successful run is claimed yet.

### Task 3: archive and disk measurements

Fresh ZIP measurements: 7,586,867,457 bytes = 7.586867457 decimal GB;
SHA256 `a41a18482a72107e449d9562d106a94193f90b8a4e11718bdbfdf746e374a23b`.
The GitHub clone at `ae2a301` completed (208,314,368 allocated bytes);
`make reproduce-v2 DATA_ARCHIVE=/home/sriram/speech-eval/data/release/speech-eval-dataset-v1.zip`
failed at its first Docker fetch command. No imported-data or reproduced hash is
claimed. README/dataset card now document measured components with hard-link
de-duplication and exact units; machine evidence is `reports/disk_usage.json`.
Linux development footprint is 57,456,644,096 allocated bytes; whole-engine
non-sparse Docker VHDX lengths are 39,405,486,080 bytes. Their combined snapshot
is 96,862,130,176 bytes, explicitly not the fresh project minimum. The complete
Docker-inclusive installation requirement remains blocked/unmeasured, not guessed.

### Task 4: tested small fixes

Health now prefers successful real Git HEAD, otherwise the supplied
`SPEECHEVAL_GIT_COMMIT`; missing metadata stays null. Failed Git no longer reports
the literal `HEAD`, and missing executable is handled. Docker build arg
`GIT_COMMIT` becomes that environment value; api/tools Compose builds receive it.
Make defaults to actual checkout HEAD, respecting explicit environment/Make
overrides. Five tests cover real unborn/committed Git fixtures, absent executable
and configuration wiring. Four failed before the fix; all five pass afterwards.
Health fix committed/pushed separately as `99cf2fc`.

README documents the known Plotly bundle advisory as harmless for correctness,
while acknowledging initial download/parse time; no refactor or suppression.
The GitHub clone at `ae2a301` passed locked `npm ci` and `npm run build` with
checksum-verified Linux Node 22.14.0, matching the Docker build version. Vite
8.3.3 emitted the actual >500-kB warning and returned success. The development
checkout's platform-specific node_modules did not build under Linux; they were
left unchanged, and the clean clone was used instead.

Interpolation/MFA behavior is retained and tested/documented, not silently fixed:
the per-word extra flag is dropped by Word validation, but its indexed warning
survives and the API uses warnings. The producer's user-specific MFA model path
remains; Docker supplies the compatibility paths. Three characterization/doc
tests cover these claims. Missing README documentation first failed its test,
then passed after documentation. No frozen aligner/producer edits were made.

Full suite: 275 passed in 14.31 s; repeat before final commit: 275 in 12.52 s.
All scientific code/config hashes in the v2
payload still verify unchanged after test. Compose client `--profile tools`
resolved actual checkout commit `2783f1e24ae83b3211648fc6b6322718e3f54ffc` into
both build arguments without a daemon. Independent read-only review found no
critical/important issues; its Make override wording correction was applied.
Machine evidence: `reports/phase11_small_fixes.json`. Live rebuilt-container
health remains unverified while Docker startup is blocked; no deployed fix is
claimed. Only the requested service metadata/deployment/docs/tests changed.

### Frozen host reproduction (not fresh-clone Docker proof)

`uv run python -m speecheval.evaluate_v2 --reproduce` succeeded after the service
metadata fix. It checks frozen scientific inputs/code/config and recomputes only
the frozen expected result, with no tuning, selection or new marker. Reproduced
JSON SHA256 equals the published one exactly:
`e770969c2d44e97cff3ee0d58b318d81edb8264356004070f6edfa4aa9f9c754`.
Marker SHA256 remains
`e05e0bbe789fff7fc9d29747a456165e7171091c735363a9b2d3a397917b2e9a`.
This is explicitly a host byte-identity check, not the blocked fresh-clone Docker
requirement and not an additional decision-bearing test evaluation.

**post-hoc v2; test split was seen with v1, so results are optimistic.**

Frozen commit before test: `95c8f334faf4c134fcbf5b4fa31fda4635f336ea`. One decision-bearing test run; any later numerical runs are requested frozen reproductions, not additional tuning/evaluation decisions.

### A-LOSO

Files: 190; excluded uncertain truth: 0.

| Type | Version | Precision | Recall | F1 [95% CI] | Onset ms | Offset ms | Clean/min | Severity rho |
|---|---|---:|---:|---|---:|---:|---:|---:|
| rushing | frozen v1 | 0.625 | 0.167 | 0.263 [0.067, 0.450] | 80.0 | 12.0 | 0.000 | 0.19 |
| rushing | post-hoc v2 | 0.800 | 0.133 | 0.229 [0.054, 0.417] | 73.5 | 43.5 | 0.000 | 0.27 |
| dragging | frozen v1 | 1.000 | 0.185 | 0.312 [0.105, 0.511] | 479.0 | 7.0 | 0.000 | N/A |
| dragging | post-hoc v2 | 1.000 | 0.148 | 0.258 [0.069, 0.462] | 1554.0 | 139.0 | 0.000 | N/A |
| monotone | frozen v1 | 0.100 | 0.419 | 0.161 [0.087, 0.242] | 105.0 | 619.0 | 0.335 | 0.68 |
| monotone | post-hoc v2 | 1.000 | 0.129 | 0.229 [0.056, 0.400] | 56.5 | 13.0 | 0.000 | N/A |
| too_quiet | frozen v1 | 0.714 | 0.179 | 0.286 [0.069, 0.487] | 215.0 | 205.0 | 0.000 | N/A |
| too_quiet | post-hoc v2 | 1.000 | 0.143 | 0.250 [0.062, 0.462] | 188.5 | 135.0 | 0.000 | N/A |
| mumbling | frozen v1 | 1.000 | 0.483 | 0.651 [0.467, 0.800] | 119.0 | 74.0 | 0.000 | N/A |
| mumbling | post-hoc v2 | 0.750 | 0.414 | 0.533 [0.345, 0.703] | 150.0 | 107.5 | 0.000 | N/A |
| awkward_pause | frozen v1 | 0.156 | 0.903 | 0.265 [0.197, 0.332] | 15.5 | 39.0 | 0.447 | 0.75 |
| awkward_pause | post-hoc v2 | 0.322 | 0.613 | 0.422 [0.296, 0.528] | 16.0 | 40.0 | 0.112 | 0.69 |
| missing_pause | frozen v1 | 0.038 | 0.414 | 0.070 [0.037, 0.108] | 6.0 | 6.5 | 0.559 | N/A |
| missing_pause | post-hoc v2 | 0.038 | 0.414 | 0.070 [0.037, 0.108] | 6.0 | 6.5 | 0.559 | N/A |
| overall | frozen v1 | 0.125 | 0.400 | 0.190 [0.156, 0.223] | 26.0 | 40.5 | 1.341 | 0.28 |
| overall | post-hoc v2 | 0.145 | 0.288 | 0.193 [0.154, 0.232] | 26.0 | 34.0 | 0.671 | 0.21 |

### Same-file severity cohorts

Shared clean controls repeated; only homogeneous eligible truth strengths; mixed strengths excluded. Full-set recall_by_severity includes every eligible truth region instead.

| Severity | Type | v1 P | v2 P | v1 R | v2 R | v1 F1 | v2 F1 |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | rushing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | dragging | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | monotone | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | too_quiet | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | mumbling | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | awkward_pause | 0.111 | 0.000 | 0.800 | 0.000 | 0.195 | 0.000 |
| 1 | missing_pause | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | overall | 0.033 | 0.000 | 0.114 | 0.000 | 0.051 | 0.000 |
| 2 | rushing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2 | dragging | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2 | monotone | 0.042 | 0.000 | 0.200 | 0.000 | 0.069 | 0.000 |
| 2 | too_quiet | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2 | mumbling | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2 | awkward_pause | 0.132 | 0.000 | 1.000 | 0.000 | 0.233 | 0.000 |
| 2 | missing_pause | 0.032 | 0.032 | 0.400 | 0.400 | 0.059 | 0.059 |
| 2 | overall | 0.064 | 0.028 | 0.229 | 0.057 | 0.100 | 0.037 |
| 3 | rushing | 1.000 | 1.000 | 0.200 | 0.200 | 0.333 | 0.333 |
| 3 | dragging | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 3 | monotone | 0.037 | 0.000 | 0.200 | 0.000 | 0.062 | 0.000 |
| 3 | too_quiet | 1.000 | 1.000 | 0.200 | 0.200 | 0.333 | 0.333 |
| 3 | mumbling | 1.000 | 1.000 | 0.200 | 0.200 | 0.333 | 0.333 |
| 3 | awkward_pause | 0.111 | 0.333 | 0.800 | 0.800 | 0.195 | 0.471 |
| 3 | missing_pause | 0.032 | 0.032 | 0.400 | 0.400 | 0.059 | 0.059 |
| 3 | overall | 0.078 | 0.115 | 0.286 | 0.257 | 0.122 | 0.159 |
| 4 | rushing | 1.000 | 1.000 | 0.400 | 0.200 | 0.571 | 0.333 |
| 4 | dragging | 1.000 | 1.000 | 0.200 | 0.200 | 0.333 | 0.333 |
| 4 | monotone | 0.148 | 1.000 | 0.800 | 0.200 | 0.250 | 0.333 |
| 4 | too_quiet | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 4 | mumbling | 1.000 | 0.833 | 1.000 | 1.000 | 1.000 | 0.909 |
| 4 | awkward_pause | 0.132 | 0.385 | 1.000 | 1.000 | 0.233 | 0.556 |
| 4 | missing_pause | 0.046 | 0.046 | 0.600 | 0.600 | 0.086 | 0.086 |
| 4 | overall | 0.145 | 0.184 | 0.571 | 0.457 | 0.231 | 0.262 |
| 5 | rushing | 0.400 | 0.667 | 0.400 | 0.400 | 0.400 | 0.500 |
| 5 | dragging | 1.000 | 1.000 | 0.600 | 0.400 | 0.750 | 0.571 |
| 5 | monotone | 0.156 | 1.000 | 0.833 | 0.333 | 0.263 | 0.500 |
| 5 | too_quiet | 0.500 | 1.000 | 0.333 | 0.333 | 0.400 | 0.500 |
| 5 | mumbling | 1.000 | 0.667 | 1.000 | 0.800 | 1.000 | 0.727 |
| 5 | awkward_pause | 0.143 | 0.385 | 1.000 | 1.000 | 0.250 | 0.556 |
| 5 | missing_pause | 0.071 | 0.071 | 0.833 | 0.833 | 0.132 | 0.132 |
| 5 | overall | 0.175 | 0.224 | 0.711 | 0.579 | 0.281 | 0.324 |

Full-set severity recall (all eligible truth regions, including mixed files):

| Type | Version | S1 | S2 | S3 | S4 | S5 |
|---|---|---:|---:|---:|---:|---:|
| rushing | v1 | 0.000 | 0.000 | 0.167 | 0.333 | 0.333 |
| rushing | v2 | 0.000 | 0.000 | 0.167 | 0.167 | 0.333 |
| dragging | v1 | 0.000 | 0.000 | 0.000 | 0.286 | 0.600 |
| dragging | v2 | 0.000 | 0.000 | 0.000 | 0.286 | 0.400 |
| monotone | v1 | 0.000 | 0.143 | 0.200 | 0.833 | 0.750 |
| monotone | v2 | 0.000 | 0.000 | 0.000 | 0.167 | 0.375 |
| too_quiet | v1 | 0.000 | 0.000 | 0.429 | 0.000 | 0.333 |
| too_quiet | v2 | 0.000 | 0.000 | 0.286 | 0.000 | 0.333 |
| mumbling | v1 | 0.000 | 0.000 | 0.286 | 1.000 | 1.000 |
| mumbling | v2 | 0.000 | 0.000 | 0.143 | 1.000 | 0.833 |
| awkward_pause | v1 | 0.800 | 0.833 | 0.857 | 1.000 | 1.000 |
| awkward_pause | v2 | 0.000 | 0.000 | 0.857 | 1.000 | 1.000 |
| missing_pause | v1 | 0.000 | 0.333 | 0.333 | 0.500 | 0.833 |
| missing_pause | v2 | 0.000 | 0.333 | 0.333 | 0.500 | 0.833 |
| overall | v1 | 0.114 | 0.195 | 0.349 | 0.571 | 0.705 |
| overall | v2 | 0.000 | 0.049 | 0.279 | 0.452 | 0.591 |
### B-same-speaker

Files: 76; excluded uncertain truth: 0.

| Type | Version | Precision | Recall | F1 [95% CI] | Onset ms | Offset ms | Clean/min | Severity rho |
|---|---|---:|---:|---|---:|---:|---:|---:|
| rushing | frozen v1 | 0.500 | 0.182 | 0.267 [0.000, 0.556] | 57.5 | 5.0 | 0.000 | N/A |
| rushing | post-hoc v2 | 0.000 | 0.000 | 0.000 [0.000, 0.000] | N/A | N/A | 0.000 | N/A |
| dragging | frozen v1 | 0.059 | 0.273 | 0.097 [0.000, 0.197] | 84.0 | 510.0 | 0.000 | 1.00 |
| dragging | post-hoc v2 | 0.023 | 0.091 | 0.036 [0.000, 0.107] | 1.0 | 510.0 | 0.000 | N/A |
| monotone | frozen v1 | 1.000 | 0.357 | 0.526 [0.182, 0.769] | 325.0 | 660.0 | 0.000 | 1.00 |
| monotone | post-hoc v2 | 0.500 | 0.071 | 0.125 [0.000, 0.316] | 2435.0 | 455.0 | 0.000 | N/A |
| too_quiet | frozen v1 | 0.667 | 0.200 | 0.308 [0.000, 0.615] | 10.5 | 307.5 | 0.000 | N/A |
| too_quiet | post-hoc v2 | 0.500 | 0.100 | 0.167 [0.000, 0.400] | 8.0 | 2502.0 | 0.000 | N/A |
| mumbling | frozen v1 | 0.800 | 0.364 | 0.500 [0.125, 0.800] | 136.0 | 229.0 | 0.000 | N/A |
| mumbling | post-hoc v2 | 0.571 | 0.364 | 0.444 [0.125, 0.667] | 136.0 | 778.0 | 0.000 | N/A |
| awkward_pause | frozen v1 | 0.007 | 0.833 | 0.014 [0.007, 0.024] | 37.5 | 32.5 | 0.000 | N/A |
| awkward_pause | post-hoc v2 | 0.118 | 0.333 | 0.174 [0.043, 0.320] | 30.5 | 25.5 | 0.000 | N/A |
| missing_pause | frozen v1 | 0.019 | 0.462 | 0.037 [0.012, 0.065] | 10.0 | 3.5 | 0.000 | N/A |
| missing_pause | post-hoc v2 | 0.019 | 0.462 | 0.037 [0.012, 0.065] | 10.0 | 3.5 | 0.000 | N/A |
| overall | frozen v1 | 0.018 | 0.390 | 0.035 [0.026, 0.045] | 31.0 | 35.5 | 0.000 | 0.09 |
| overall | post-hoc v2 | 0.042 | 0.207 | 0.070 [0.043, 0.099] | 16.0 | 37.0 | 0.000 | 0.11 |

### Same-file severity cohorts

Shared clean controls repeated; only homogeneous eligible truth strengths; mixed strengths excluded. Full-set recall_by_severity includes every eligible truth region instead.

| Severity | Type | v1 P | v2 P | v1 R | v2 R | v1 F1 | v2 F1 |
|---:|---|---:|---:|---:|---:|---:|---:|
| 1 | rushing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | dragging | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | monotone | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | too_quiet | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | mumbling | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | awkward_pause | 0.007 | 0.000 | 1.000 | 0.000 | 0.015 | 0.000 |
| 1 | missing_pause | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 1 | overall | 0.006 | 0.000 | 0.143 | 0.000 | 0.012 | 0.000 |
| 2 | rushing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2 | dragging | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2 | monotone | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2 | too_quiet | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2 | mumbling | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2 | awkward_pause | 0.008 | 0.000 | 1.000 | 0.000 | 0.015 | 0.000 |
| 2 | missing_pause | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 2 | overall | 0.006 | 0.000 | 0.143 | 0.000 | 0.012 | 0.000 |
| 3 | rushing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 3 | dragging | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 3 | monotone | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 3 | too_quiet | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 3 | mumbling | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 3 | awkward_pause | 0.004 | 0.167 | 0.500 | 0.500 | 0.007 | 0.250 |
| 3 | missing_pause | 0.033 | 0.033 | 1.000 | 1.000 | 0.065 | 0.065 |
| 3 | overall | 0.009 | 0.040 | 0.214 | 0.214 | 0.017 | 0.067 |
| 4 | rushing | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 4 | dragging | 0.167 | 0.100 | 1.000 | 0.500 | 0.286 | 0.167 |
| 4 | monotone | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 |
| 4 | too_quiet | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 4 | mumbling | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| 4 | awkward_pause | 0.008 | 0.250 | 1.000 | 1.000 | 0.015 | 0.400 |
| 4 | missing_pause | 0.033 | 0.033 | 1.000 | 1.000 | 0.063 | 0.063 |
| 4 | overall | 0.030 | 0.086 | 0.714 | 0.500 | 0.057 | 0.147 |
| 5 | rushing | 1.000 | 0.000 | 1.000 | 0.000 | 1.000 | 0.000 |
| 5 | dragging | 0.091 | 0.000 | 0.500 | 0.000 | 0.154 | 0.000 |
| 5 | monotone | 1.000 | 0.000 | 0.500 | 0.000 | 0.667 | 0.000 |
| 5 | too_quiet | 1.000 | 0.500 | 1.000 | 0.500 | 1.000 | 0.500 |
| 5 | mumbling | 1.000 | 0.500 | 1.000 | 1.000 | 1.000 | 0.667 |
| 5 | awkward_pause | 0.004 | 0.143 | 0.500 | 0.500 | 0.008 | 0.222 |
| 5 | missing_pause | 0.033 | 0.033 | 1.000 | 1.000 | 0.063 | 0.063 |
| 5 | overall | 0.032 | 0.073 | 0.786 | 0.429 | 0.062 | 0.125 |

Full-set severity recall (all eligible truth regions, including mixed files):

| Type | Version | S1 | S2 | S3 | S4 | S5 |
|---|---|---:|---:|---:|---:|---:|
| rushing | v1 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| rushing | v2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| dragging | v1 | 0.000 | 0.000 | 0.000 | 1.000 | 0.500 |
| dragging | v2 | 0.000 | 0.000 | 0.000 | 0.500 | 0.000 |
| monotone | v1 | 0.000 | 0.000 | 0.000 | 1.000 | 0.750 |
| monotone | v2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.250 |
| too_quiet | v1 | 0.000 | 0.000 | 0.000 | 0.000 | 1.000 |
| too_quiet | v2 | 0.000 | 0.000 | 0.000 | 0.000 | 0.500 |
| mumbling | v1 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| mumbling | v2 | 0.000 | 0.000 | 0.000 | 1.000 | 1.000 |
| awkward_pause | v1 | 1.000 | 1.000 | 0.500 | 1.000 | 0.500 |
| awkward_pause | v2 | 0.000 | 0.000 | 0.500 | 1.000 | 0.500 |
| missing_pause | v1 | 0.000 | 0.000 | 1.000 | 1.000 | 0.667 |
| missing_pause | v2 | 0.000 | 0.000 | 1.000 | 1.000 | 0.667 |
| overall | v1 | 0.143 | 0.211 | 0.167 | 0.714 | 0.765 |
| overall | v2 | 0.000 | 0.000 | 0.167 | 0.500 | 0.412 |
