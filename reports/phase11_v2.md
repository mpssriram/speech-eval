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
**post-hoc v2; the test split was seen with v1, so results are optimistic**.

Use the unchanged matcher: same-type greedy one-to-one IoU >=0.3 for duration
regions; pause events use centre distance <=0.25 s. Use the same clean-duration
denominator, uncertainty exclusions, modes and severity strata for comparisons.

Implementation and dev results follow below after Task 1 is committed/pushed.
