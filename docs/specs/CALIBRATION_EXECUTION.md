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

Ruling: when a disputed insertion is at a transcript edge, there is no aligned word on that side. Use the prepared clip boundary as that outer edge, retaining the one available aligned neighbour plus 0.2 s on its outside. Otherwise the test would omit the disputed edge audio and mechanically favour the original. Cost if wrong: edge/noise material may influence model preference; the report explicitly discloses this and human ground truth is not claimed.
Ruling: sentence-clipped medium.en provided no eligible sentence for one reader; independent unprompted full-recording medium.en resolved agreement without relaxing the exact normalized matching requirement. Its cache and prepared-clip time basis are preserved.

Numerics investigation: two fresh CPU models were identical to each other but a preliminary mixed-process cache differed by ~0.002 nats. Precision/thread/fastpath toggles alone did not reproduce that cache. Do not label that preliminary cache deterministic. Preserve it as `*_pre_isolation.json`; all calibration and disputed scoring now runs in a clean CPU worker with explicit thread, backend, precision and inference settings and new cache identity. The requested original A remains unchanged. Backend pinning has a failing-then-passing regression test; the real fresh-model acceptance check must pass before Task 2 is complete.

Task 2 complete: final isolated margin 2.425378476083314 total nats; 6/300 empirical fake acceptances (2%). All 300 controls span all 30 recordings with 100 of each fake type, excluding prior uncertain words. Exact fresh seed replay succeeded; all 100 substitutions have cmudict distance 1–2. All 85 comparisons have finite scores: 64 APPLY_B, 18 KEEP_A, 3 UNSURE. Final masks: one word each in gettysburg lv_eep, gettysburg lv_fb and O Captain lv_rg; all 27 other recordings have empty masks. All 12 missing-stanza candidates kept the full original text. Independent uncached CPU models have byte-identical emissions and scores matching the stored audit. `make test`: 60 passed. Model, audio, transcript and final-window hashes checked; 15 repaired-recording medium.en clips were actually regenerated across all 12 recordings.
