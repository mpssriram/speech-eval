# Frozen v1 diagnosis and demo gallery

Goal: check rule activation on DEV only, explain genuine v1 near misses using retained evidence, and publish seven stored synthetic hits in both demos.

User specification: diagnosis request of 2026-10-13. Repository autonomy override permits execution without plan approval.

Constraints: preserve all detector, feature, reference and rubric code/configuration. Never reevaluate the benchmark test split unless a detector activation bug is proven; then label one post-hoc rerun. Human near misses are analysis of existing measurements, not new inference. Report exact supported C-lite types and its frozen threshold 2.0; A/B thresholds remain 3.5. Preserve pre-existing UI work.

- [x] Add `scripts/diagnose_rule_coverage.py`: run one stored single-flaw DEV recording per type through A/B/C, record every flag and target match; add isolated feature probes for activation coverage. Write `reports/phase10_rule_coverage.json`.
- [x] Add `scripts/diagnose_human_near_misses.py`: verify retained measurement/reference hashes, reconstruct per-word z evidence, preserve original hit pairs, list flags, and summarize pause/non-pause |z| and reference spreads. Append `Why mostly pause flags` to `reports/phase10_human_takes.md`; emit full evidence JSON and copy the report to the requested Downloads directory.
- [x] Extend `deploy/hf-static/scripts/export_examples.py` with stored dragging, too_quiet and missing_pause hits. Label all seven with injection severity and pin same-type IoU >=0.3. Keep shared catalog ownership in `web/src/catalog.js`; repair playback exporter for that ownership.
- [x] Expose stored gallery in `web/src/App.tsx` with existing `ExampleResults`; package the same public files for local production, preserving API result flows. Build both targets and check every synthetic selection, JSON hashes and playback.
- [ ] Run repository pytest and focused UI checks (no corpus test benchmark). Verify frozen hashes, publish built Space, verify public gallery, commit and push only this task's files.
