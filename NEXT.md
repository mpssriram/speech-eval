# Next — 2026-10-12

Submission deadline: October 13.

## Pre-video fixes

1. False-alarm breakdown: added per-take/type v1/v2 A/B counts, take01 flags,
   shares and same-text reference timing to Phase10. Mode-A v1 FP: 53/77 missing
   pauses (68.8%), 7/77 rushing (9.1%). Source evaluation hash unchanged.
   Ruling: do not claim less pausing than every reader: lv_amb has 11.78 s of
   MFA gaps, below G01/G02/G04. All takes are shorter than every reference;
   pause context uses Reagan's 90.17 s excerpt, not its full 249.13 s speech.
2. Exact primary hit/demo table: added four A hits and three B hits per version,
   with labelled/detected intervals and actual live API display explanations.
   Video candidate: G02 B larger|sense, 29.900-31.470 s, IoU 1.0.
3. Report/README screenshots now use genuine G02 B versus own01, selecting
   the declared larger|sense hit. The old 120.98 s screenshot was licensed
   LibriVox lv_mk, not an excluded legacy upload; audit is recorded separately.
   Smoke fixture captures no longer overwrite genuine report screenshots.
   Page-one summary now includes genuine A/B counts. Six-page PDF repeated
   byte-identically and all pages inspected. Docker startup resolved by retaining
   only stale zero-byte IPC directories; no Docker/project data deleted.
4. Waveform overlap fixed: type/time on hover and accessible labels; no text
   inside intervals and no artificial minimum width. Legend colours retained,
   keyboard Enter/Space selects flags. Exact widths/labels verified at1440/390px;
   all six Playwright tests and 303 host tests pass. Web-only Docker rebuild;
   genuine/scientific JSON, frozen detector/config and labels unchanged.
   Fresh read-only review: no Critical/Important issues. Deferred minor:
   the 390px test's proof output currently assumes the desktop-width test ran
   first; use the full suite to refresh both entries, rather than a selected test.
5. Final no-spot-check/no-independent-raters wording: next.

## Genuine takes — complete

The recorder's 2026-10-12 chat confirmation supersedes manual TAKES_REVIEW
editing. Eight inputs validate, with actual consent and the supplied JSON notes.
Transcripts follow the explicitly authorised canonical/ASR structural-edit rule,
not independently verified verbatim transcription. Canonical units stay
Gettysburg 1–10 and Reagan 1–17 (stop at “discover its truths.”).

Initial inputs were frozen/pushed as `c1a6a02`; final pre-inference unit-map and
localized-label protocol as `a138825`. All original/raw hashes stayed unchanged.
Take04s have unknown flaws, not clean labels: excluded from hit/miss/FP pools,
but analysed in Modes A/C. Mode B is take02/03 versus own take01.

Real CPU MFA completed all requested jobs: frozen v1 A8/B4/C2 and separately
labelled post-hoc v2 A8/B4, 26 completed result rows, zero unresolved processing
problems. No detector code, threshold, bin, weight or matching rule was tuned.
The six scored takes contain 13 labels; B's four current recordings use those
same labels and do not add reference duration to the denominator.

| Version / mode | Primary hits / misses / FP | FP/min |
|---|---|---:|
| Frozen v1 / A | 4 / 9 / 77 | 9.625 |
| Frozen v1 / B | 3 / 10 / 60 | 11.236 |
| Post-hoc v2 / A | 4 / 9 / 58 | 7.250 |
| Post-hoc v2 / B | 3 / 10 / 27 | 5.056 |

Primary means same-type one-to-one IoU >=0.3. Historical pause-centre <=0.25 s
and secondary positive unit overlap are separate tables in Phase10. Many misses
and false alarms remain; recorder-confirmed planned labels are not independent
perceptual annotation. Take01 flags (Gettysburg/Reagan): v1 9/14, v2 7/11.

post-hoc v2; test split was seen with v1, so results are optimistic.
V1 remains the primary published result. Frozen config SHA256:
`3496a9c3549e5491af708c70657f4d5f4d94e23e9f23fa597b46a6e34aa60538`.
The existing benchmark one-shot marker was not rerun or changed.

The initial host-side v2 attempt rejected Docker's absolute model-path
provenance. Execution adapter `036363c` uses unchanged v2 inside the same API
container, retaining every provenance check. Historical failures are disclosed
in BLOCKERS/runtime_attempts; the complete run has none. This is an environment
adapter, not a detector fix or post-result label change.

Reports: `reports/phase10_human_takes.md`, Human-A/B in `phase06_results.md`,
and genuine-takes section 7.1 of `docs/report/report.md`. Full precision, fixed
spans, score/flag evidence and 26 dashboard links: `data/human/evaluation.json`.
Applied transcript insertions/omissions: `data/human/review/TRANSCRIPT_DIFFS.md`.
Private audio stays git-ignored and outside the public archive.

Repeated genuine workflow artifacts are byte-identical (134 outputs; retained
MFA cache, not independent alignment-accuracy evidence). All 26 completed jobs
are in API history with working tracks; eight genuine participant audio
endpoints work. `data/human/verification.json` contains the hashes/checks.
Evaluation SHA256:
`58c6f712059cea44051051466f56a7f8e1d65fa04b6503a8026197d8e8e65013`.
Latest host suite: 303 tests passed. Report: six A4 pages, repeated PDF bytes
identical, every page inspected. Frozen code/config/audio hashes remain intact.

## Open your voice in the dashboard

The existing Docker API and dashboard are running at http://localhost:8080.
These are genuine participant recordings, not synthetic fixtures:

- [Gettysburg take01, frozen v1](http://localhost:8080/results/0aae3748f747b13e89697e17)
- [Reagan take01, frozen v1](http://localhost:8080/results/57a55f0d18b627cda376b6aa)
- [Gettysburg take02 vs take01, frozen v1](http://localhost:8080/results/6d8cbd6dec22ffc8f7827ebc)
- [Gettysburg take04, frozen C](http://localhost:8080/results/b77c9d634e3c6d1d954f9989)

Every other take/mode and separately labelled v2 link is in Phase10. The
participant player uses your aligned/trimmed recording. Baseline playback is a
separate matching-word reference; it is disabled when no exact phrase matches.
Automatic score/flag inspection is not listening or an independent rating.

After restart, start Docker Desktop, then WSL `cd ~/speech-eval && make up`.
With the API healthy, repeat the genuine workflow without editing inputs:

```sh
cd ~/speech-eval
env -u PYTHONPATH ~/.local/bin/uv run python scripts/prepare_human_confirmation.py
env -u PYTHONPATH ~/.local/bin/uv run python scripts/analyze_human.py --detector both --v2-runtime docker
```

## Previously verified

Phases 1–9, Modes A/B/C prototype, API/dashboard, Playwright smoke tests,
Docker packaging, licensed release/fetcher, blind rating pack/scripts and report
display fixes remain complete. Earlier host/Docker/browser and fresh-clone
evidence is in `reports/phase12_fixes.md` and `reports/reproducibility.md`.
The DEV-only Mode B diagnosis found amplified tiny pause differences, not a
demonstrated timing bug; no new benchmark test run or detector tuning followed.
All 563 published scientific release outputs matched repeated fresh-clone CPU
Docker reproduction. The human evidence is separate and private.

## Needs user

1. Upload the unchanged `data/release/speech-eval-dataset-v1.zip` and supply its
   URL. Exact size: 7,586,867,457 bytes = 7.586867457 decimal GB. SHA256:
   `a41a18482a72107e449d9562d106a94193f90b8a4e11718bdbfdf746e374a23b`.
2. Confirm author and formal code/annotation licence files; record/publish the
   final demo. Review `docs/TODO_PLACEHOLDERS.md` and remaining BLOCKERS.
3. Try the full app tomorrow with your microphone/files. Transcript acoustic
   fidelity can be reviewed later; the authorised rule-built texts are explicitly
   disclosed, and confirmation-gated genuine analysis is no longer pending.

## Needs other people

1. Independent human agreement is pending: zero responses. Pack/scripts and
   `data/rating_pack/INSTRUCTIONS.md` are ready (about 15 minutes). Future
   agreement measurement needs independent raters' CSVs. Share only the blind
   pack, not answer keys/system scores. Never use AI or self-ratings as rater data.
2. Human listening/spot-check of the visually placed alignment reference and,
   if stronger genuine evidence is needed, independent flaw/transcript review.
   Recorder confirmation is not independent annotation.

## Remaining technical limitations

An isolated clean-install peak/minimum disk requirement is still unmeasured.
The prior retained snapshot was 55.037300736 GB including shared Docker VHDX
and other projects, not a project minimum. No estimate is substituted.
The interpolation-warning schema and user-specific MFA path remain disclosed
limitations. Plotly's bundle-size warning is known and harmless. Low precision,
failed synthetic clean-alarm guards and C-lite's limited types remain disclosed;
no human takes or ratings are used to repair them before submission.
