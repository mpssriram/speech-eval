# Recorder-confirmed human workflow, 2026-10-12

Authority: recorder's chat confirmation of this date replaces editing TAKES_REVIEW.
No independent listening, annotation, rating or transcript verification is claimed.
Use canonical Gettysburg units 1–10 and Reagan units 1–17 (stop at “truths.”).
Six takes are scored; the two spontaneous take04s have unknown flaws and are
excluded from every hit/miss/FP pool, but analysed in A and frozen C.

Transcripts: canonical words plus ASR whole-word insertions/omissions/repetitions;
same-position substitutions retain canonical words; contractions follow ASR;
G03 unit7 and R03 unit9 retain canonical words. Canonical unit punctuation and
unit-to-output word mapping are retained, not ASR sentence punctuation.
Alignment uses minimum word edit distance over expanded contractions; equal-cost
paths prefer same-position substitutions, then omissions, then insertions.
These are recorder-authorised rule-built transcripts, not independently checked
verbatim transcripts. Applied structural changes are recorded in TRANSCRIPT_DIFFS.

Before any human detector results, localized truth is fixed:
G02 awkward gap larger|sense in unit6; R02 were|daring in unit16.
G03 missing boundary units8/9; R03 units14/15.
G02 too_quiet last four words of unit8; R02 last four of unit15.
G03 dragging words have thus far in unit9.
The fixed dragging anchors span ordered have → thus → far; authorised ASR
insertions between them remain in the transcript and inside that anchored span.
Rushing, monotone and mumbling use the whole canonical unit's aligned interval.
Times come from real MFA, in trimmed participant seconds; raw offsets are saved.
A missing/very short gap is represented by a 30 ms boundary event centred on the
MFA gap, as the frozen detector represents pause events; no detector setting changes.
If an anchor cannot be placed unambiguously, stop that take's evaluation and report
the problem rather than inventing a span. Excluded G04 slips are unknown; R04 none.

Primary: same type, one-to-one greedy IoU >=0.3 for all types.
Historical synthetic pause-centre <=0.25 s counts are additionally reported.
Secondary (explicitly secondary): same type, any positive overlap with the
labelled canonical unit, one-to-one; no multiple credit for duplicate predictions.
A pools six scored takes; B pools four current takes (02/03 versus own01),
with references not added to its duration denominator. No human threshold tuning.
V1 is primary; frozen v2 is post-hoc and secondary. No new benchmark one-shot run.

## Implementation plan / ledger

1. Test-first input builder and excluded-input validation; save the supplied notes
   as first JSON block, construct eight transcripts and canonical unit word maps,
   validate without inference, commit and push before results.
   Files: human_recording_inputs.py, human_grounding.py, human_takes.py,
   tests/test_human_confirmation.py, human/transcripts and review provenance.
2. Test-first localized intervals, strict/historical/secondary matching, version
   routing and deterministic v2 completed-job publication; run unchanged real MFA
   v1 A/B/C then frozen v2 A/B. Verify audio/frozen hashes and all dashboard jobs.
3. Generate per-take/pooled Phase10 and Phase6 Human-A/B report sections, update
   genuine-takes report/pending box/NEXT, repeat output bytes, full tests, PDF
   repeat-render and inspect every page. Fresh-context code review before push.

Review focus: canonical numbering after ASR insertions; protected mumbling units;
contractions versus substitutions; zero-gap pause events; excluded unknown labels.
Latest explicit user workflow overrides old recording-script plans and manual
CONFIRMED markers; no plan approval gate is required by AGENTS user override.
Work stays in the existing user-authorised checkout so private audio and API
provenance are not duplicated into an unrelated worktree.
