# Execution decisions

## 2026-10-07 — Resumed execution

- Resumed the interrupted full dataset command with saved per-source caches, one worker and CPU affinity 0–3. The last completed source was 22/29; no completed audio was deleted or rebuilt intentionally. User reauthorized the main workload after the resource pause.
- Ruling: result reports are now explicitly requested (Phases 6–8); retain machine audits and write result reports, not status reports. Learned detector stays deferred until the required pipeline is complete.
- Evaluation corrections: pause eligibility uses centre distance but greedy ordering uses highest IoU; confusion counts wrong types only; predicted fragments overlapping excluded uncertain truth are excluded symmetrically; held-out cached reuse requires unchanged dataset/reference/measurement hashes. Four new regressions were observed RED then GREEN (10 evaluation/calibration tests).
- Phase 6 final review: four Important findings fixed in one TDD pass: establish alarm-budget feasibility with improving intermediate coordinate moves; freeze train/dev inputs and detector/calibration code before opening test evidence; fingerprint actual source/synthetic audio in final reuse; reuse unchanged implementation results across report-only commits and refuse automatic reruns after implementation/data changes. Four regressions RED→GREEN; focused suite 15 passed. Final whole-suite verification follows.
- Ruling: feasibility repair is deterministic coordinate descent, not exhaustive global search. If no improving move establishes the guard, report the unmet budget honestly; never claim global infeasibility. Cost if wrong: a feasible joint setting may be missed; reported budget status remains measured.
- Final: minor (deferred): manually repeating calibration consumes the previously calibrated initial candidate configuration. Do not rerun completed calibration without checking its saved audit; the current execution resumes missing work only.
- Final: Ruling: review did not establish actual DEV/test accuracy, corpus integrity, chart rendering, acoustic realism, human validation, learned quality, or commits/push. Executor verifies real artifacts and runs; absent human/learned results remain explicit. Cost if wrong: software tests could be mistaken for perceptual validation.
- User confirmed takes have not yet been recorded; preparation can happen later. Human settings and listener-rating agreement remain pending, not waived evidence.
- Phase 7 final review Important fixes: compare actual first and second analysis files even when IDs differ; validate genuine frozen Phase 6 data/config/code before validation and bind score audits to rubric/validator hashes; derive complete-series coverage from frozen test sources, not observed variant rows. Regraded negative configurable weights as Important because they can yield scores above 10; reject invalid finite/nonnegative/category weights. Four regressions RED→GREEN; whole suite 175 passed before the next Mode C additions.
- Ruling: human rating workflow is still unimplemented as well as unexecuted; do not describe missing ratings as its only blocker. Docker equivalence is pending Phase 9. Reviewer did not establish actual severity/corpus/host/Docker/perceptual results; executor must run them. Cost if wrong: arithmetic reproducibility could be confused with validated speech quality.
- Ruling: independently prepared scoring/Mode C code while the serial dataset finishes; their measured validation still follows the requested Phase 6 → 7 → 8 order. They do not select detection thresholds. Unit-test detector fixtures now explicitly retain known thresholds rather than changing expected behavior when DEV calibration updates the production YAML.
- Ruling: full corpus validation exposed 10 mixed-file oracle edges whose unrounded map step falls within 0.5 ms of a source edge, but millisecond serialization changes its step side (1–3 s inserted pauses). This supersedes the earlier purely continuous-map rounding bound at discontinuities. Validate the mathematically bounded source-time rounding interval only near a step; reject out-of-interval discrepancies, explicitly list all 10 unresolved step sides, and make no sub-millisecond ownership claim. Audio, real alignments and features are unchanged; no completed batch is restarted. Cost if wrong: oracle boundary agreement near these insertions is uncertain, so it cannot establish human accuracy. Two tiny step/continuous regressions RED→GREEN precede the real integrity rerun.
- Completed observed synthetic engineering evidence: all 29 batches, 1,073 files (zero skipped sites), real MFA plus features, full hash/index/split checks and 20 seeded fresh injection bundle replays pass. The 10 map-step ambiguities remain disclosed, not called resolved. Full current unit suite: 179 passed. Human Dataset v1 acceptance and tagging remain pending actual takes/labels/consent.
- Observed DEV-only calibration: 152 files, overall F1 0.150 and clean alarms 1.777/min; the ≤0.5 guard is NOT met. Report this acceptance limitation, freeze the selected conservative rules, and do not tune against held-out results.
- Phase 8 review fix pass: preserve false-positive supported types regardless of file truth; use one eligible-sentence mask for both systems/truth/clean duration; validate schemas and frozen Phase 7 provenance; regrade heuristic-evidence ID omission as Important and bind key moments to analysis identity. Four regressions RED→GREEN; full verification follows.
- Final: minor (deferred): Mode C speaker-rate aggregation overwrites earlier recordings for repeated speaker slugs (current split has unique slugs); strong-ending guideline wording does not render changed thresholds; additional end-to-end routing/norm/ingress tests are desirable. Actual fresh-ingress and evaluation runs remain executor responsibilities, not inferred from unit checks.
- Ruling: scoring/Mode C validation compares all originally frozen Phase 6 input hashes, allowing unrelated later artifacts (such as norms) without claiming the held-out inputs changed. The final-evaluation command itself remains conservative and refuses changed input sets rather than silently rerunning. The attempted unused-artifact cache relaxation was deferred; no completed calibration was retuned. Cost if wrong: a new artifact not referenced by the frozen index could be overlooked, but every original dependency and index hash must match.

## 2026-10-07 — Phase 5 review fix pass

- Final: fixed reversed region evidence across merged gaps — retain the temporal span but aggregate only directional flags. The [3,-12,3,3] regression was RED before correction.
- Final: fixed pause boundary mismatches — both endpoints must map to the same adjacent reference boundary, in reference collection and participant comparison. Inserted/skipped endpoint regressions were RED before correction.
- Final: fixed measurement reuse — source, synthetic and incoming participant audio/alignment/feature hashes must match producing provenance. A changed-audio fixture was RED (accepted stale features) before the correction. Incoming caches now bind feature/alignment code, package versions, model/dictionary bytes; model hashing is streamed to avoid loading checkpoints into RAM.
- Final: fixed train-speaker pool leakage — exclude the speaker from both direct reference readers and pooled spreads/provenance. The existing generated, uncommitted playback-baseline choices are regenerated once using corrected LOSO statistics.
- Final: fixed reference path traversal — validate text/speaker/recording identifiers before any writes, and enforce output containment. The traversal regression was RED before correction.
- Final: minor (deferred): plot region text is truncated to 250 characters; Mode B templates contain plural verb agreement. These do not change measured evidence or detection.
- Final: Ruling: acoustic/ASR accuracy and human realism remain unverified by the code reviewer; actual CUDA transcription and supplied-transcript MFA ingress smoke checks ran, but neither is human validation. Cost if wrong: transcription/alignment errors affect downstream judgments.
- Final: Ruling: dataset/smoke completion, plot usability, held-out accuracy and commit/push evidence are executor responsibilities, not implied by review. Human acceptance remains pending. Cost if wrong: engineering success could be confused with quality evidence.
- Ruling: defer the one-time held-out accuracy run until detection/scoring integration is frozen, so later code changes are not silently scored against a stale evaluated commit. Calibration uses dev only. Cost if wrong: final accuracy remains unavailable until that freeze.
- Ruling: drop the optional learned detector under PLAN cut line 2 to prioritize the complete rules pipeline/dashboard and resource budget. No learned-training or rules-vs-learned result is claimed.

## 2026-10-07 — resource budget requested by user

- Parallel CPU batches caused high system load. User requested GPU/VRAM preference. Stopped only our owned build process group and resumed cached work with one dataset worker, OMP/OpenBLAS/MKL/Numba threads=1, CPU affinity 0–3. No audio or completed artifacts were deleted.
- Observed WSL used memory fell from 6.9 GiB to 1.5 GiB after serial restart; system memory figures include all WSL processes, not just this project.
- Installed MFA is CPU Kaldi; Praat and current SciPy feature kernels are also CPU. Do not replace the validated aligner or pretend these stages run on GPU. New participant ASR uses configured WhisperX large-v3 on CUDA when available, batch one, fixed beam/temperature; the explicit earlier CPU transcript-calibration/secondary-ASR settings remain unchanged.

## 2026-10-07 — Phase 4 final review and autonomous continuation

- Important cache finding fixed: feature reuse binds HQ FLAC hashes as well as real alignment artifacts. A constant-boundary fixture with halved audio gain recomputes measured intensity by approximately -6.02 dB; cache replay is unchanged for unchanged audio.
- Important CLI finding fixed: `human script` runs independently of dataset workers with the configured seed. Both behavior regressions were observed failing before implementation; the full suite passes 125 tests.
- Minor findings deferred after the single final review: shard runtime telemetry changes on cold rebuild; the dataset card includes prospective manifest sources and lacks a label example. These do not alter audio/alignment/feature hashes; do not claim whole-shard byte determinism.
- Human takes, listening labels and publication consent remain missing, not waived or invented. Synthetic engineering and independent downstream algorithms can advance under the latest autonomous scope, but Dataset v1 / human validation cannot be claimed accepted.
- Phase 5 formula conflict: specified n=1,n0=5 shrinkage gives sqrt(5/6) times pooled sigma (about 0.913), not within 1 percent. Preserve the formula and test its exact result; zero pooled spread requires an explicit positive scale floor to avoid division by zero.

## 2026-10-07 — final Phase 1 analysis and autonomous continuation

Current order: correct provenance/counts; signed/bias/bootstrap/breakdown diagnostics; deterministic committed G2P dictionary experiment; MFA promotion; QA, acceptance and tests; commit/push. The latest user then authorizes continuing later phases without approval pauses. Respect missing user-audio and human-evidence limits; never fabricate them.

- Human spot-check is PENDING, not reported/completed. The prior report's claim is corrected; historical log statements are superseded, not treated as evidence.
- Ruling: keep corpus coverage in a separate table (30 recordings, actual transcript-word count); the gold table uses 37 words / 74 edges. The 84 baseline OOVs count repeated whitespace-word occurrences containing a base-dictionary-missing normalized token. There were 18 unique forms and temporary G2P already supplied pronunciations; this is not a count of failed alignments.
- Ruling: bootstrap paired words, stratified within the three recordings (15/15/7), retain both edges together, 10,000 resamples, seed 20261007. Show mean and median absolute-error differences MFA minus WhisperX and percentile 95% CIs. These are conditional on the selected visual reference, not population CIs over readers or annotation uncertainty.
- Ruling: subtract each aligner's separate median signed start/end bias only for an in-sample pooled-error diagnostic. Do not alter stored timings or use corrected errors for aligner selection.
- Ruling: CMUdict first phoneme defines lexical stop initials P/B/T/D/K/G; affricates are other, absent/mixed variants unknown. No acoustic onset claim. Cost if wrong: subgroup descriptions may not reflect realized speech.
- Ruling: G2P creates a committed supplemental dictionary; pipeline combines it with the installed base dictionary. Generate twice and hash canonical outputs, preserve all variants. Adopt only if OOV coverage reaches zero and gold absolute errors do not worsen; retain the baseline audit/alignments for comparison. Hash-check dictionary contents before cached reuse.
- Five behavior regressions were observed failing before implementing signed bias, paired bootstrap, onset classification, pronunciation canonicalization and QA edge/count rules. Existing main-branch workflow/push authorization is retained; no new worktree or approval gate is introduced.

Final review: one Important adoption-gate finding accepted and fixed in one pass. Comparison now validates all current source alignments/provenance, counts OOV occurrences from the actual corpus outputs, binds dictionary/candidate/input/gold artifacts by hashes and fails rejection. Default alignment/evaluation, promotion and Phase 1 acceptance require matching accepted evidence. Candidate runs require explicit `--dictionary-experiment` and cannot promote. One rejection/stale-evidence regression was observed RED before the fix; complete suite verification follows.

Final: minor (deferred): bootstrap unit regression has homogeneous rows and does not strongly detect independently resampled edges or lost stratification. The implemented algorithm was reviewed as correctly paired/stratified; defer a heterogeneous-fixture regression rather than a second review/fix loop.

Final: Ruling: reviewer declined acoustic/pronunciation accuracy, annotator independence and human review — retain pending-human provenance and gold-quality risk; code/hash agreement is not human truth. Cost if wrong: visually annotated boundaries or G2P phones may bias later feature placement.

Final: Ruling: reviewer declined ongoing real inference/QA/acceptance/tests and source/push verification — executor runs them, reads results and checks hashes/remote before claiming completion. Later-phase engineering may proceed under the latest explicit authorization; no implicit human acceptance is inferred.

## 2026-10-06 — supplied visual gold and number rendering

Latest scope: copy supplied annotations, expand numbers, regenerate affected alignment inputs, complete Step 7b bake-off and STOP after its report. Do not start Phase 2. Do not silently promote an aligner or claim Phase 1 complete before the remaining choice/QA/acceptance steps.

- Annotation provenance: Claude visually annotated waveform/spectrogram/intensity/pitch without listening, plus a human spot-check reported by the user. The notes list seven suggested spot checks but contain no actual human boundary measurements/error estimate. Treat these as a limited visually annotated reference, not fully human-listened gold. Independence is asserted by the annotator, not verified here.
- Validate labelled words, not total intervals: the supplied grids have 41 intervals including blank gaps and 20 labelled words. Exclude any label ending in ?; remove only that suffix for matching the frozen template label.
- Supplied independent annotations may extend beyond the original aligner-derived template boxes (17 do). Retain them within recording bounds and report excursions; clipping them would bias the comparison toward the aligners. Cost if wrong: bad annotation may influence measured errors, so provenance and excursions remain explicit limitations.
- Spell all remaining numeric body tokens for alignment, not only the seven examples: also 25, 390, the 2006 poem readout, and digit portions of C-1/F-1. Preserve comments and punctuation. Hyphenated number words normalize identically to digits; arbitrary compounds retain their prior normalization.
- Freeze pre-expansion transcripts/masks/windows; remap final uncertainty and gold word indices through old-to-new spans. A single numeric label maps to the full expanded phrase. Preserve all supplied gold/todo files unchanged. The old calibrated acoustic audit is historical, not relabelled as a new verification of expanded text.
- Determinism means two real fresh-process runs per aligner on the three gold recordings, not cached output copying. Use fixed CPU settings and isolate MFA's three-recording corpus from its main corpus.
- Apply the pooled start/end median rule. Within 10 ms, prefer a deterministic CPU aligner; if both qualify, prefer MFA, as the spec anticipates. Neither the recommendation nor a comparison against a small visual sample establishes general accuracy.

Ledger: eight new behavior tests were observed failing before implementation. Full suite then passed 77/77. Numeric migration and fresh model runs follow; commit/push at the completed report.

Final review fix pass: three Important findings were accepted. Validate scored dataset JSON/provenance against all current inputs and word identities, require complete hash-validated numeric remapping, and fingerprint checkpoint/dictionary contents plus inference dependency versions before reusing determinism evidence. Three regressions were observed RED then GREEN; full suite 80/80 passed. This is one root fix pass, not a second review loop.

Environment finding: Kalpy is installed by conda without Python distribution metadata. Python metadata lookup failed once; read-only `conda list --json` confirmed Kalpy 0.10.5 and CPU Kaldi 5.5.1172. Fingerprint all 281 conda package versions/builds instead; the actual fingerprint check then passed. Nothing was installed or upgraded.

Final reviewer declined acoustic correctness, annotator independence and spot-check extent: retain the user's provenance report and explicitly state those are not established by the code review. Cost if wrong: the visually annotated reference could bias error estimates; no error-free human-gold claim is made.

Final reviewer could not compare external done-file bytes in its limited read-only scope: root compared them directly at copy and in the final verification script. Cost if wrong: accidental annotation changes would invalidate provenance; byte identity is required.

Final reviewer did not judge running inference, final report, full tests or commit/push: root must check actual completed runs/hashes, arithmetic and source preservation, rerun the suite, and verify git/remote state before handing off. No deferred Minor findings.

Praatio's generated TextGrid format includes trailing spaces. Preserve supplied gold/todo bytes and generated alignment evidence rather than cosmetically rewriting them; run the whitespace diagnostic with `git -c core.whitespace=-blank-at-eol diff --check`. Other whitespace-error checks remain enabled. Hardware was read from `lscpu`: Intel Core Ultra 9 275HX, 24 CPUs visible in WSL. Both inference paths use one CPU thread/job; no GPU timing is claimed.

Completed evidence: both independent three-recording hash pairs pass (MFA and WhisperX). Pooled medians are 52 and 72 ms respectively: recommend MFA by lower median, not the tie-break. Both fail the spec's 90% within 50 ms target (48.649% / 39.189%). Do not hide this or treat visual gold/spot-checks as error-free human truth. Current source/mask/window checks, cached report/alignment hash checks and 80 tests pass. Stop after the report; primary remains null and no promotion/QA or Phase 2 is attempted in this scope.

## Autonomous continuation, 2026-10-07

The preceding entries describe earlier scopes, not the current state. Phase 1
promotion and engineering closure are committed in afa25f8. Human spot-checks
remain pending and neither aligner meets the gold-boundary accuracy target.

Ruling: use the existing phase specs directly, with approval gates and narrative
phase reports waived by the user. Keep tests, artifact provenance, machine QA,
and reproducible commands. Docker moves to Phase 9. Cost if wrong: less narrative
handoff context, but no reduction in executable checks or evidence integrity.

Phase 2 review: fixes exclude uncertain endpoints from adjacent pause features
and use the same valid-sentence mask for syllable totals and speaking duration.
Both regressions failed before the fixes. Current corpus has no zero-duration
words. No human, Docker or downstream detector validity is claimed here.

Final: minor (deferred): the feature unit determinism test serializes a single
computed table twice. A separate fresh recomputation compared all 150 corpus
artifacts byte-for-byte successfully; the regression can be strengthened later.

Ruling: effect checks use the same fixed source-speaker pitch bounds on both
audio candidates, not a wide search that introduces octave errors. The initial
wide-search audit is retained (104/105 passed); corrected bounds gave 105/105.
Cost if wrong: pitch-range fidelity remains model-measured, not human realism.

Ruling: insert pauses strictly inside the inter-word gap; zero/sub-sample gaps
use their exact semantic boundary instead of unsafe zero-crossing snapping.
The physical cut is within half a sample. Cost if wrong: tiny seam artifacts;
crossfade/zero-gap regression tests enforce continuity and correct word ownership.

Ruling: serialized maps use the required 1 ms time rounding. Replay verification
uses the derived quantization bound (1 ms plus 0.5 ms times local maximum stretch
slope), not an impossible fixed 1 ms bound on three separately rounded values.
Cost if wrong: sub-3 ms mapping differences could be missed, never whole-word
or inserted-pause errors. The 10% effect threshold is unchanged.

Phase 3 review fixes: shared post-resample attenuation protects both exported
sample rates and is recorded in labels; optional real-audio tests skip when any
audio/stat fixture is missing. Both failure cases reproduced before fixing.
Re-graded ignored small artifacts as an Important reproducibility issue: only
generated audio directories remain ignored, so maps, labels and evidence commit.
Final: minor (deferred): repeated preview comparison clicks retain old playback
callbacks. Single comparisons work; this demo-aid polish does not alter audio,
labels or objective measurements. Listening realism/human acceptance and Phase 4
mixed-file behavior are not established by the Phase 3 review.

Ruling: intentional JFK excerpt coverage is compared against its best canonical
substring (semiglobal token alignment), not the full 2,233-token address. Otherwise
unrecorded bookends incorrectly exclude this required Mode B source. The initial,
uncommitted draft split was manually corrected before any dataset was generated;
subsequent split changes are rejected. Cost if wrong: an inaccurately chosen
excerpt could underestimate deviation. The source transcript remains the frozen
automatically verified as-spoken text, with uncertainty masks preserved.

Ruling: the Phase 1 short/long-word flags are alignment risks, not automatic
source exclusions. Apply the Phase 4 clipping, pitch and transcript-deviation
criteria. O Captain reader lv_rg has clipped samples and is excluded. This yields
29 usable sources: 18 train, 4 dev, 7 test. Cost if wrong: alignment-risk sources
can reduce feature quality; their Phase 1 QA provenance is retained.
