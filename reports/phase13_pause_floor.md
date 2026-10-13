# Phase 13 — post-hoc pause-floor sensitivity check

**Status at protocol freeze:** no sensitivity evaluation has been run. This protocol is written and committed before implementation or DEV/TEST/genuine sensitivity runs. v1 remains the primary result. This is a post-hoc sensitivity check; the test split was previously seen with v1. The timebox is two hours from receipt of the complete specification on 2026-10-13.

## Fixed rule and its source

Use exactly one floor value: **0.052 seconds**. Its source is the MFA pooled median absolute boundary error, **52.0 ms**, in the [Day 1 aligner bake-off, “Error table — 37 scored words, 74 pooled edges”](day01_aligner_bakeoff.md#error-table--37-scored-words-74-pooled-edges). That report uses 37 selected visually annotated words across three recordings; the human listening/spot-check is pending. This observed median supplies the prescribed sensitivity constant, not a validated per-boundary noise standard deviation. No alternative floor values, tuning, or propagation multiplier will be tried.

The v1 pause transform is exactly `T(x) = ln(x + 0.05)`, using NumPy `np.log`, the natural logarithm, in [reference.py](../src/speecheval/reference.py). For each eligible reference boundary i, retain its existing transformed centre `mu_i` and shrunk reference spread `sigma_i`. Recover the physical reference centre as `p_i = exp(mu_i) - 0.05` seconds, using the existing v1 inverse transform. The reference is unchanged except for this denominator in the experimental path:

```text
sigma_floor_i = T(p_i + 0.052) - T(p_i)
              = ln(p_i + 0.052 + 0.05) - ln(p_i + 0.05)
sigma_eff_i   = max(sigma_i, sigma_floor_i)
z_floor_i     = (T(participant_pause_i) - mu_i) / sigma_eff_i
```

Apply this floor to **pause features only**, independently at every boundary. Do not insert 0.052 directly as a sigma in log units. Keep reference centres, participant measurements, word mappings and uncertainty masks unchanged. Round z to the same four significant digits as v1, then use its unchanged detection logic.

## Frozen settings and isolation

- The implementation accepts a config flag, `pause_sigma_floor_s`; missing/disabled defaults OFF. The sensitivity configuration sets it to exactly `0.052`. A regression test must establish byte-identical v1 output when the flag is off.
- All seven A/B thresholds remain `k = 3.5`; pause gap gates, region grouping, severity bins, containment suppression and rubric weights are unchanged.
- Use the same matching and eligibility rules, IoU cutoff and denominators as the corresponding frozen v1 results. Genuine labels use their existing localized spans and original strict same-type one-to-one IoU >=0.3 matching. Unknown take04s are excluded.
- v1 stays primary. Existing detector configuration, stored v1 analyses, all published v1 numbers, the dashboard, Space, `web/` and `deploy/` remain unchanged. Experimental results go to separate Phase 13 artifacts. No experimental result is published as a primary dashboard job.

## Predeclared execution order

1. Commit this protocol document before implementation or any sensitivity evaluation.
2. Implement the isolated config-controlled floor and regression checks; test OFF equivalence and the exact transformed ON rule.
3. Run DEV once with the flag ON. No tuning, other changes or second floor value.
4. Run TEST once, labelled **“post-hoc sensitivity check; test split previously seen with v1”**. Preserve the original A-LOSO/B cohorts, matcher, IoU rule and denominators. Use the existing v1 confidence-interval procedure wherever its results have a CI.
5. Run the six scored genuine takes (01–03 for Gettysburg and Reagan) in Mode A, plus the four current takes02/03 in Mode B against their own take01. Preserve their current localized labels and matching; reference take01 durations are not added to B denominators.
6. Report one comparison table, v1 versus v1+floor, for A-LOSO, B and genuine A/B: precision, recall, F1, CIs where v1 has them, clean alarms/min, hits/misses/false positives and flags by type. State exactly which types change and whether any non-pause flaw becomes a hit. Keep DEV diagnostic results separate from the TEST/genuine headline rows.
7. Verify primary artifacts remain unchanged; copy this report to `C:\Users\msrir\Downloads\speech-eval-report-inputs\`. Commit and push the implementation/results branch, then integrate and push main. Stop at two hours if incomplete: commit existing work and state what remains.

## Results

No experiment results are present at protocol freeze. Results will be appended after the prescribed one-shot runs, with run provenance and immutable v1 comparisons.
