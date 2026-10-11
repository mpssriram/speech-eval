# Next

Phase 11: Task 1 report fixes verified (five-page PDF, rounded display values,
real correct-hit explanation, dashboard screenshots, consolidated pending box).
The corrected canonical eight-take recording sheet is ready at
`docs/recording_script.pdf` (one page), committed/pushed as `3dd043c`.
Task 2 post-hoc v2 DEV search is complete: exactly 30 configurations, selected
YAML SHA256 `3496a9c3549e5491af708c70657f4d5f4d94e23e9f23fa597b46a6e34aa60538`.
Independent review and 267 tests passed. Freeze commit `95c8f33` was pushed before
the exactly-one marker-protected test evaluation. V1 stays primary; v2 is secondary
and post-hoc. A F1 0.190 -> 0.193, recall 0.400 -> 0.288, clean/min 1.341 -> 0.671
(test guard still fails); B F1 0.035 -> 0.070 with lower recall. No detector,
evaluator or threshold edits follow test results. Report/PDF verification is
complete (six pages, repeated identical render, every page inspected).
Fresh-clone frozen v2 reproduction is blocked by Docker Desktop failing to start;
see `docs/BLOCKERS.md`. Continuing measured disk documentation and tested health
metadata without claiming unavailable Docker evidence.
Archive upload size/hash and measured local disk components are now documented
in README, `docs/DATASET.md` and `reports/disk_usage.json`. Full Docker-inclusive
installation/peak-build requirement remains unmeasured until Docker is restored.
See `reports/phase11_v2.md` for the protocol and inherited Mode B limitation.

Done: A licensed archive/fetcher, fresh GitHub-clone CPU Docker numerical
reproduction twice with identical hashes; B consent-gated real-MFA A/B driver
tested on an explicitly synthetic fixture; C twelve-clip blind pack and agreement
scripts; D measured dataset card; E evidence-based README, technical report and
video script. Each item is committed/pushed after verification.

Not done: genuine human-take evaluation, actual independent rater agreement,
human alignment spot-check, public archive upload and recorded/published video.
These cannot be replaced by generated recordings or ratings.

Needs you:

1. Upload `data/release/speech-eval-dataset-v1.zip` unchanged and supply its URL.
2. Supply eight requested WAVs, consent, actual notes and as-spoken transcripts
   following `docs/HUMAN_TAKES.md` (include spoken slips and the Reagan excerpt).
3. Give only `data/rating_pack/` to independent raters and return their separate
   CSVs; never share the private answer key or repository with them.
4. Confirm author and formal code/annotation licences; record/publish the demo.
   Review `docs/TODO_PLACEHOLDERS.md` and `docs/BLOCKERS.md` before submission.

Submission deadline: October 13. No thresholds were tuned on test reproductions,
fixture takes, absent genuine takes or ratings.
