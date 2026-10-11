# Next

Phase12 update (2026-10-12): display correction, DEV-only B diagnosis,
recorder-confirmation review sheet, rating instructions and report wording are
verified. Genuine human evaluation is still confirmation-gated, not complete.
Results: `reports/phase12_fixes.md`. Latest full suite: 279 passed; all three
real browser tests pass at port 8080; six PDF pages inspected, repeated renders
byte-identical. No frozen detector change or new test-split evaluation.
Latest human instruction: Gettysburg04 and Reagan04 (global08) were spontaneous
mixed readings; types/locations remain unspecified, not clean or invented labels.
Latest Mode B scope is take02/03 versus take01, not take04.
Display item committed/pushed as `23e6ec5` (277 Python tests, three browser
tests). DEV-only B diagnosis found tiny pause differences amplified by reference
spread, not a demonstrated detector timing bug; no test rerun or tuning.
See Phase12 for FP breakdown and the two rounded oracle-step QA limitations.
B diagnosis committed/pushed as `a305075`. Take review is now at
`data/human/review/TAKES_REVIEW.md`; correct each transcript/actual flaw list and
write `CONFIRMED` under each take. No ASR/PDF plan has been promoted to labels.
Review committed/pushed as `0ebfd70`; rating instructions and pending-agreement
wording as `23f0548`. Independent rating responses remain zero.
Report wording/footer and host application verification pushed as `0630caf`.
Docker recovered during the final retry. Fresh-clone testing exposed omitted
README/docs in the image; including them fixes three missing-file failures.
All 279 rebuilt-container tests pass. Frozen Docker v2 and disk checks are
being completed; the older startup blocker below is historical.

## Local application testing (without Docker)

The API and dashboard are running at `http://localhost:8080` in WSL host mode,
not Docker. `/api/health` reports a real git commit and the frozen v1 hash.
Browser checks cover upload, recording controls (synthetic browser device, not
your microphone), waveform, score/explanation, selected regions, Yours/Baseline
playback, Modes A/B/C and mobile overflow. A separate synthetic-only upload
check completed real CPU MFA 3.4.2 in A/B; it missed the injected rushing region,
which remains an honest detector limitation. This is not human accuracy evidence.

If the machine is restarted, start two WSL terminals:

```sh
# Terminal 1
cd ~/speech-eval
env -u PYTHONPATH ~/.local/bin/uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
# Terminal 2: clean Linux frontend dependencies, verified from current source
cd ~/.cache/speech-eval-web
env PATH=/home/sriram/.cache/speech-eval-node/node-v22.14.0-linux-x64/bin:/usr/bin:/bin npm run dev -- --port 8080
```

Open `http://localhost:8080`. For A choose the matching text and upload audio;
for B select an earlier completed same-text take; C accepts a supplied transcript
without a same-text reference. For an uploaded recording containing slips, supply
the actual words, not a corrected canonical reading. Click a flag to inspect its
region/explanation and try both playback buttons. Baseline playback is disabled
when those exact words are unavailable; that is disclosed, not silently substituted.
Your own microphone permission/audio and genuine take correctness still need
your testing/review. Do not present synthetic fixture jobs as your recordings.

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

Human audio update (2026-10-11): all eight approved M4As are copied unchanged
under `data/human/original/`; all eight native 48 kHz mono PCM16 WAVs are under
`data/human/raw/`. Hashes, decoded duration, exact bytes, peaks and saturation
counts are in `data/human/import_manifest.json` and `reports/phase10_human_takes.md`.
All pass technical size/duration checks; samples match native original decoding
exactly and repeat conversions are byte-identical. These checks are not human
annotation validation or detection results. Actual consent/prose notes supplied
in chat are now saved verbatim; the global 01–08 mapping is confirmed. Existing
local ASR ran on all eight takes and wrote explicitly unconfirmed drafts plus
canonical-text word diffs (`reports/phase10_asr_review.md`). No draft was promoted
to the validator input folder. Validation now stops on the missing fenced notes
JSON; confirmed transcripts and complete supported-type/location labels are
still required. No genuine MFA/scoring/counts/dashboard jobs are claimed. The
user must confirm these inputs before processing. Preserve v1/v2 and the one-shot marker;
never tune on human takes. Latest requested B scope is B02/B03 versus A01;
the earlier B04 scope is superseded. Separately labelled frozen v2 output still
requires the workflow extension, which the existing v1 driver lacks.

## Needs user

1. Upload `data/release/speech-eval-dataset-v1.zip` unchanged and supply its URL.
   Exact size: 7,586,867,457 bytes = 7.586867457 decimal GB. SHA256:
   `a41a18482a72107e449d9562d106a94193f90b8a4e11718bdbfdf746e374a23b`.
2. Review/correct the eight actual ASR drafts and confirm the as-spoken text
   (including repetitions/slips and the recorded Reagan excerpt). Supply explicit
   supported delivery-flaw types and sentence/raw-time locations for every take,
   or explicitly declare none only when true. Prose notes and actual consent are
   already saved; neither transcription nor ground truth will be invented.
   `data/human/input_validation.json` lists all remaining validation problems.
3. Restore Docker Desktop (inaccessible `dockerInference` socket; no reset/data
   deletion attempted). This unblocks the frozen fresh-clone v2 reproduction,
   two-run hashes, exact Docker-inclusive installation/build measurement and
   a rebuilt-container `/api/health` check. Agent can finish these after recovery;
   do not consume a second one-shot test evaluation or retune.
4. Confirm author and formal code/annotation licence files; record/publish the demo.
   Final submission is due October 13.
   Review `docs/TODO_PLACEHOLDERS.md` and `docs/BLOCKERS.md` before submission.

## Needs other people

1. Independent rater agreement is pending (zero responses).
   Disclose this limitation in the submission; pack and scripts are ready. Future
   measurement needs at least three independent raters with separate CSVs for
   all twelve blind clips. Distribute only `data/rating_pack/`, never the answer
   key/repository or system scores. Do not substitute AI or self-ratings.
   Plain-English instructions and CSV return steps are in
   `data/rating_pack/INSTRUCTIONS.md` (allow about 15 minutes).
2. A human alignment spot-check/listening and boundary corrections for the
   visually annotated reference. This cannot be claimed from the existing
   automatic/Claude visual evidence. Genuine-take notes/annotations also need
   actual listening by the recorder/annotator, not invented labels.

Submission deadline: October 13. No thresholds were tuned on test reproductions,
fixture takes, absent genuine takes or ratings.
