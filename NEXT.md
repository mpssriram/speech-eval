# Next — 2026-10-12

Submission deadline: October 13.

## New Drive migration — first link verified

The new Drive ID `1rDbbPMKORv0nnQ-QnmbrQXIg1mqktvTm` is **speech-eval-dataset-v1.zip**:
7,586,867,457 bytes; SHA256 `a41a18482a72107e449d9562d106a94193f90b8a4e11718bdbfdf746e374a23b`.
Full anonymous gdown 5.2.0 download in /tmp matches the actual local ZIP;
trusted internal inventory also matches. Neither release archive was modified.
Updated config, README, dataset/submission docs, report source/PDF and current
download evidence. Old folder retired; replacement folder and human-takes links
are awaited. The new main ID is never assigned to the human release.
`scripts/fetch_data.py` was already config-driven and had no old ID: skipped
code edits; existing integrity checks and --from-local stay unchanged.
Historical rejected-upload identity is retained as a digest; original raw-link
evidence remains in Git history. Verification: reports/drive_release_migration.json.
312 host tests passed; all 17 frozen code/config hashes still match. Report:
six A4 pages, repeated bytes identical; final layout inspected. PDF SHA256:
`b8f6ecc1e360bedb825c215a03fcc4ef04d3bc3c0010994dc136818b368d1e26`. No retired ID remains in current tracked files, including
the PDF. Evidence: reports/drive_migration_verification.json.
Docker stayed stopped; WSL will be shut down after push to release RAM.

## Prompt B release metadata

1. Dataset links/fetcher: main Drive ID and folder published; gdown 5.2.0 pinned,
   SHA256/size/member verification retained, --from-local retained, optional
   --with-human-takes and --human-from-local added. Anonymous main transport
   sampled 1 MiB; complete local import verifies the frozen ZIP and payload.
   Human download link withheld pending correction; prepared ZIP metadata is
   published. README/dataset/submission docs contain manual browser fallback.
2. Takes ZIP verification: downloaded the supplied file with gdown to /tmp.
   It is byte-identical to the main dataset ZIP (a41a1848..., 7,586,867,457 bytes),
   with zero human WAVs; all required human-release members are missing.
   Its link is deliberately withheld. Upload the correct file:
   `C:/python_practice/Speech/data/release/speech-eval-human-takes-v1.zip`
   (62,520,905 bytes; SHA256 33e8e0e80a562dfc40e828f6ef1d9ff5285cf24ae543b5dbb7b6ff31377658bd).
   Separate builder repeated byte-identically; eight WAVs/transcripts/label files,
   notes, unchanged consent, review protocol/evaluation and SHA256 list all match
   repo bytes. Local human import verifies all 33 payloads. Main archive unchanged.
   Evidence: reports/human_release_verification.json. Builder regression test
   prevents accidentally targeting the main ZIP. Original consent is retained.
   Read-only review follow-up: regression tests also reject symlink/hardlink
   aliases to the main ZIP and exclude unrelated human/review files. The five
   frozen review files are explicitly listed. Correct archive hash stayed exact;
   reviewer verified both fixes and found no further Important issues.
3. Author/licences: Sriram MPS, IIT Mandi, with assistance from Claude (Anthropic)
   and Codex (OpenAI). LICENSE grants MIT for code; LICENSE-DATA grants CC BY 4.0
   for labels, annotations, documentation and the author's recordings, with the
   original consent unchanged. Source audio remains public domain per source.
   README, dataset card and report source updated. PDF renderer now reads the
   source author for visible credit and PDF metadata; final regeneration is item 6.
4. Mode B precision check: SKIPPED rerun because already completed DEV-only in
   scripts/diagnose_mode_b_dev.py and reports/phase12_fixes.md. Existing audit
   covers before/after/inside/overlap FP positions, rushing/dragging/pause maps,
   independent MFA jitter and gain-adjusted outside-edit PCM checks. Added the
   554-FP breakdown and conclusions to report section 6.2. No demonstrated live
   timing/processing bug; no detector fix or new benchmark test evaluation.
   Rounded insertion-knot oracle QA outliers remain explicit, not silently fixed.
5. Disk: measured 32,170,019,620 bytes (32.170 GB / 29.961 GiB): required
   retained tools/API image 16,804,236,803 + main archive 7,586,867,457 + unpacked
   inventory payload 7,778,915,360. README/card/report carry the number/method.
   Excludes unrelated images, host environments, repeat archives, optional takes,
   build cache and scratch. Not a clean-build peak; image predates gdown layer.
   Docker startup restored by preserving stale zero-byte run/Secrets IPC dirs;
   no images, volumes or data deleted. Existing API/web healthy again.
6. Report PDF regenerated: six A4 pages, 11 pt body, confirmed visible author
   and PDF metadata. Two renders matched SHA256
   d46a3ca3fa72f28de6937ac19b31deb775157a4d23fc99d7265ba707d54207c5;
   all six pages visually inspected. Condensed repeated prose/chart spacing to
   keep the page budget while retaining results and limitations. Final host suite:
   312 passed. Seventeen frozen code/config hashes, sixteen original/WAV hashes,
   original consent, main ZIP and separate human ZIP verified unchanged.
   Evidence: reports/release_metadata_verification.json and PDF verification.json.
   All Prompt B work committed/pushed item by item, with the packaging review fix
   in an additional commit. Only replacement human upload requires user action.

Already completed work was retained: no main archive rebuild, no genuine-take
inference rerun, no new Mode B DEV/test benchmark run or detector tuning.
Main download is public; the supplied takes upload is the wrong file. Folder
anonymous gdown listing failed, so a logged-out browser folder check remains
pending rather than being claimed as verified.

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
5. Final wording now states no human spot-check was done and human agreement
   was not measured: no independent raters were available; no AI/self-ratings.
   Active report, README, dataset/rating/Docker docs, genuine reports and video
   script are consistent. Historic frozen reports/protocol/hash manifests remain
   unchanged; they describe their original state, not new human validation.
   New diagnostics/extended Phase10 report repeated byte-identically. All133
   original non-document workflow artifacts still match the frozen hash map;
   only the narrative Phase10 document was intentionally supplemented.

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
Human WAVs stay git-ignored and outside the frozen main archive; the owner
authorised a separate CC BY 4.0 human release in Prompt B.

Original genuine workflow artifacts repeated byte-identically (134 outputs; retained
MFA cache, not independent alignment-accuracy evidence). All 26 completed jobs
are in API history with working tracks; eight genuine participant audio
endpoints work. `data/human/verification.json` contains the hashes/checks.
Evaluation SHA256:
`58c6f712059cea44051051466f56a7f8e1d65fa04b6503a8026197d8e8e65013`.
Latest host suite: 312 tests passed (Prompt B). Report: six A4 pages, repeated PDF bytes
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
env -u PYTHONPATH ~/.local/bin/uv run python scripts/report_human_demo.py --hits
```

## Previously verified

Phases 1–9, Modes A/B/C prototype, API/dashboard, Playwright smoke tests,
Docker packaging, licensed release/fetcher, blind rating pack/scripts and report
display fixes remain complete. Earlier host/Docker/browser and fresh-clone
evidence is in `reports/phase12_fixes.md` and `reports/reproducibility.md`.
The DEV-only Mode B diagnosis found amplified tiny pause differences, not a
demonstrated timing bug; no new benchmark test run or detector tuning followed.
All 563 published scientific release outputs matched repeated fresh-clone CPU
Docker reproduction. Human evidence is separate; the optional consented release
does not change those frozen scientific outputs.

## Needs user

1. Provide a new Drive link for the matching separate human release:
   `C:/python_practice/Speech/data/release/speech-eval-human-takes-v1.zip`
   (62,520,905 bytes; SHA256
   33e8e0e80a562dfc40e828f6ef1d9ff5285cf24ae543b5dbb7b6ff31377658bd),
   share as "Anyone with the link" and provide its replacement Drive ID.
   Main ZIP publication and author/licence confirmation are DONE.
2. Record/publish the final demo video and supply the working URL. Check the
   replacement Drive folder once its new URL is supplied; the old folder is retired.
3. Optional: try the app with your microphone/files. Transcript acoustic fidelity
   can be reviewed later; rule-built texts and recorder-confirmed labels are
   explicitly disclosed. Genuine analysis is complete.

## Needs other people

1. Human agreement was not measured: no independent raters were available;
   no AI or self-ratings were used. Zero responses. Pack/scripts and
   `data/rating_pack/INSTRUCTIONS.md` are ready (about 15 minutes). Future
   agreement measurement needs independent raters' CSVs. Share only the blind
   pack, not answer keys/system scores. Never use AI or self-ratings as rater data.
2. No human spot-check was done on the visually placed alignment reference.
   Future stronger genuine evidence needs independent flaw/transcript review.
   Recorder confirmation is not independent annotation.

## Remaining technical limitations

Measured required retained Docker image + one archive + unpacked payload is
32.170019620 GB; component evidence is in reports/reproduction_disk_usage.json.
Clean-install/build peak remains unmeasured; the measured image predates the
gdown metadata layer and the total excludes scratch/cache. No minimum is inferred.
The interpolation-warning schema and user-specific MFA path remain disclosed
limitations. Plotly's bundle-size warning is known and harmless. Low precision,
failed synthetic clean-alarm guards and C-lite's limited types remain disclosed;
no human takes or ratings are used to repair them before submission.
