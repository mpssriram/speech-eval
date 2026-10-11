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
see `docs/BLOCKERS.md`. Health build/runtime metadata is tested and pushed as
`99cf2fc`; Plotly warning and retained schema/MFA limitations are documented and
tested. All 275 tests pass; frozen scientific code/config hashes still match.
Live rebuilt-container health is blocked, not claimed verified.
Frozen host v2 reproduction passed byte-for-byte (published SHA
`e770969c2d44e97cff3ee0d58b318d81edb8264356004070f6edfa4aa9f9c754`);
the one-shot marker is unchanged. This does not substitute for fresh-clone Docker.
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

## Needs user

1. Upload `data/release/speech-eval-dataset-v1.zip` unchanged and supply its URL.
   Exact size: 7,586,867,457 bytes = 7.586867457 decimal GB. SHA256:
   `a41a18482a72107e449d9562d106a94193f90b8a4e11718bdbfdf746e374a23b`.
2. Supply eight requested WAVs, consent, actual notes and as-spoken transcripts
   following `docs/HUMAN_TAKES.md` (include spoken slips and the Reagan excerpt).
3. Restore Docker Desktop (inaccessible `dockerInference` socket; no reset/data
   deletion attempted). This unblocks the frozen fresh-clone v2 reproduction,
   two-run hashes, exact Docker-inclusive installation/build measurement and
   a rebuilt-container `/api/health` check. Agent can finish these after recovery;
   do not consume a second one-shot test evaluation or retune.
4. Confirm author and formal code/annotation licence files; record/publish the demo.
   Final submission is due October 13.
   Review `docs/TODO_PLACEHOLDERS.md` and `docs/BLOCKERS.md` before submission.

## Needs other people

1. At least three independent raters: complete separate CSVs for all twelve blind
   clips. Distribute only `data/rating_pack/`, never the answer key/repository or
   system scores. Actual agreement can be computed only after responses arrive.
2. A human alignment spot-check/listening and boundary corrections for the
   visually annotated reference. This cannot be claimed from the existing
   automatic/Claude visual evidence. Genuine-take notes/annotations also need
   actual listening by the recorder/annotator, not invented labels.

Submission deadline: October 13. No thresholds were tuned on test reproductions,
fixture takes, absent genuine takes or ratings.
