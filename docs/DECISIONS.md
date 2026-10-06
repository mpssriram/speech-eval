# Execution decisions

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
