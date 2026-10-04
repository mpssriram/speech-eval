# Execution ledger — calibrated verification through Step 6

User approved the design and waived further spec/plan gates. Work stays in the explicitly requested WSL checkout/main. Stop before Step 7a; no gold boundaries or primary aligner choice are invented.

1. Regenerate 12 repaired recordings' full-source large-v3 caches, preserve legacy files, refresh windows and verify all 30 frozen cuts.
2. Bootstrap CPU alignment of ORIGINAL transcripts; score local A/B totals; build 300 seeded three-way-agreement controls, excluding prior uncertain words and allocating proportionally across all 30 recordings.
3. Calibrate inclusive empirical FAR <=2%, reapply decisions from original text, emit final uncertain word indices and provenance markers. Archive old audit/report for comparison; commit/push.
4. Step 5c: regenerate transcript diffs with honest automatic review status; commit/push.
5. Step 6: sentence windows, MFA OOV/G2P, both forced aligners, validated JSON/TextGrid and uncertain indices; commit/push. Stop before Step 7a.

Ruling: calibration labels are proxy labels, not human truth. The empirical <=2% rate is in-sample for controls, not guaranteed error on disputed real speech.
Ruling: inclusive fake advantage >= margin requires nextafter above tied excluded scores. A hand-written test initially miscounted tied 4-nat advantages; corrected expectation to margin >4 and zero/5 false accepts.
Ruling: use original-transcript CPU forced-alignment boundaries, not the already-edited transcript or ASR variant, for local windows. Invalid local boundaries stay UNSURE.

Task 1 complete: 12 actual large-v3 redecode runs; old/new ASR hashes and full-source provenance frozen. All 30 CSV cut start/end values match excerpts.yaml; current sentence windows refreshed. Raw audio unchanged. `make test`: 54 passed with local-scoring/word-mapping regressions present in the working tree.
Root-cause fix: midpoint overlap repair previously moved an earlier start backward in an overlap chain. Clamp the midpoint to the previous start; failing synthetic chain test now passes.
