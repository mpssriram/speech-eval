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



## Results — post-hoc sensitivity check; test split previously seen with v1

Completed one DEV run (152 files), one TEST run (190 A-LOSO + 76 B-same-speaker files), and one genuine run (six distinct scored takes: six A comparisons and four B current-take comparisons). No floor search, threshold tuning, realignment or feature extraction. The same retained measurements/reference centres and localized labels were used. v1 stays primary; these comparisons do not replace any published v1 number.

Synthetic matching is exactly the frozen v1 evaluator: same type, greedy one-to-one IoU >=0.3 for non-pauses; for pause types, the existing centre-distance <=0.25 s eligibility rule is retained. Genuine matching is its original primary rule: same-type greedy one-to-one **strict IoU >=0.3 for every type**. Neither cohort’s policy was changed to imitate the other. Uncertain truth/prediction exclusions and clean-control/current-duration denominators are retained.

The synthetic v1 metrics and 95% recall/F1 intervals reproduced the stored Phase 6 JSON exactly. CIs for v1+floor use the same file-level bootstrap: 1,000 resamples, NumPy default_rng seed 20261001, percentile 2.5/97.5. This treats files as sampling units, as v1 did; edited files from the same speaker are correlated, so it is not a speaker-level generalization interval. Precision has no published v1 CI. Genuine v1 has no published CIs, so none are invented here.

Flags-by-type cells use the fixed order **R / D / Mo / Q / Mu / AP / MP** = rushing / dragging / monotone / too_quiet / mumbling / awkward_pause / missing_pause. Hit/miss/FP counts use the corresponding frozen matcher, not a new human judgement.

| Cohort | Version | Files / labels | Precision | Recall (95% CI where available) | F1 (95% CI where available) | Clean alarms/min | Hits / misses / FP | Flags by type: R/D/Mo/Q/Mu/AP/MP |
|---|---|---:|---:|---|---|---:|---|---|
| TEST A-LOSO | v1 | 190 / 205 | 0.1246 | 0.4000 [0.3285, 0.4706] | 0.1900 [0.1556, 0.2235] | 1.3412 | 82 / 123 / 576 | 8/5/130/7/14/180/314 |
| TEST A-LOSO | v1+floor | 190 / 205 | 0.1387 | 0.3951 [0.3235, 0.4660] | 0.2053 [0.1680, 0.2448] | 1.1177 | 81 / 124 / 503 | 8/5/130/7/14/106/314 |
| TEST B-same-speaker | v1 | 76 / 82 | 0.0181 | 0.3902 [0.2889, 0.4940] | 0.0345 [0.0256, 0.0447] | 0.0000 | 32 / 50 / 1739 | 4/51/5/3/5/1390/313 |
| TEST B-same-speaker | v1+floor | 76 / 82 | 0.0333 | 0.3659 [0.2651, 0.4744] | 0.0611 [0.0439, 0.0791] | 0.0000 | 30 / 52 / 870 | 4/51/5/3/5/519/313 |
| Genuine A | v1 | 6 / 13 | 0.0494 | 0.3077 | 0.0851 | 8.6450 | 4 / 9 / 77 | 7/3/0/0/0/16/55 |
| Genuine A | v1+floor | 6 / 13 | 0.0556 | 0.3077 | 0.0941 | 7.8933 | 4 / 9 / 68 | 7/3/0/0/0/7/55 |
| Genuine B | v1 | 4 / 13 | 0.0476 | 0.2308 | 0.0789 | N/A | 3 / 10 / 60 | 0/1/1/0/0/34/27 |
| Genuine B | v1+floor | 4 / 13 | 0.0667 | 0.2308 | 0.1034 | N/A | 3 / 10 / 42 | 0/1/1/0/0/16/27 |

Genuine A clean alarms/min uses only the two declared natural take01 controls (2.660500 minutes). They are recorder-declared clean, not independently validated. Its all-six-take FP/min changes from 9.624679 to 8.499717, using 8.000267 current-take minutes. Genuine B has no clean current-take controls; clean alarms/min is N/A. Its FP/current-minute changes from 11.236446 to 7.865512, using 5.339767 minutes. Own take01 is used as B’s reference and its duration is not added. Take04s remain excluded.

### What changed

- **TEST A-LOSO:** removed flags awkward_pause=74; added flags none. Retained spans with changed pause z/severity: awkward_pause=67, missing_pause=1. Newly matched labels: none; lost matched labels: awkward_pause=1.
- **TEST B-same-speaker:** removed flags awkward_pause=871; added flags none. Retained spans with changed pause z/severity: awkward_pause=519, missing_pause=313. Newly matched labels: none; lost matched labels: awkward_pause=2.
- **Genuine A:** removed flags awkward_pause=9; added flags none. Retained spans with changed pause z/severity: awkward_pause=7, missing_pause=35. Newly matched labels: none; lost matched labels: none.
- **Genuine B:** removed flags awkward_pause=18; added flags none. Retained spans with changed pause z/severity: awkward_pause=16, missing_pause=27. Newly matched labels: none; lost matched labels: none.

**No non-pause flaw becomes a hit.** Rushing, dragging, monotone, too_quiet and mumbling retain identical detected regions, evidence, severities and per-type matched labels in every file. Only awkward_pause and missing_pause evidence can change. In these completed runs, all removed detections are awkward_pause; missing_pause intervals/counts are unchanged, although their z/severity can decrease. The pause floor does not solve the genuine non-pause misses. It reduces some false alarms but sacrifices synthetic pause recall; it does not establish improved perceptual validity or justify replacing v1.

### DEV result and provenance

DEV A-LOSO (the original calibration cohort): v1 P/R/F1 = 0.094136/0.371951/0.150246, H/M/FP = 61/103/587; floor P/R/F1 = 0.092736/0.365854/0.147965, H/M/FP = 60/104/587. Both have clean alarms/min 1.777393. The unchanged floor was not selected or adjusted in response to DEV. Institutional JFK/Reagan B benchmark sources are TEST-only, so no invented DEV B benchmark is included.

Protocol was committed before implementation/results: `17a15e4`. Implementation and tests were committed before one-shot runs: `ae38269`. Eight new floor tests passed; the worktree suite passed **344 tests with 1 existing dataset-dependent skip**. Every eligible file also passes OFF table-byte identity and exact non-pause region identity. The primary code/config/reference/stored-analysis/report hash snapshot is verified before and after each run. Source feature provenance is checked; retained genuine producer artifacts are verified against their existing hashes without regenerating them in another runtime.

Machine-readable metrics, per-type results, all per-file predictions/matches, newly/lost matched labels and input hashes: `phase13_dev.json`, `phase13_test.json`, `phase13_human.json`. Exclusive `phase13_*_started.json` markers prevent a second run; no overwrite/retry flag is provided. Bootstrap resampling is performed on the single retained prediction sets, not repeated detector runs.

The flag belongs to the separate `speecheval.pause_floor` experimental path and `configs/pause_floor_sensitivity.yaml`. Missing/null/zero disables it. The primary `pipeline.py`, `detect.py`, `reference.py`, detector/rubric YAML and normal CLI are unchanged, so their default outputs and analysis identities remain byte-identical. No dashboard, Space, `web/`, `deploy/` or primary published v1 result is changed by this branch.

Commands used once from the experimental worktree (with the existing installed v1 environment/data):

```sh
PYTHONPATH=$PWD/src /home/sriram/speech-eval/.venv/bin/python scripts/run_pause_floor_sensitivity.py dev --data-root /home/sriram/speech-eval
PYTHONPATH=$PWD/src /home/sriram/speech-eval/.venv/bin/python scripts/run_pause_floor_sensitivity.py test --data-root /home/sriram/speech-eval
PYTHONPATH=$PWD/src /home/sriram/speech-eval/.venv/bin/python scripts/run_pause_floor_sensitivity.py human --data-root /home/sriram/speech-eval
python scripts/report_pause_floor_sensitivity.py
```

These evaluation commands are recorded for provenance; existing one-shot markers intentionally reject reruns. The report renderer reads completed results only and can be rerun without evaluation. All work completed within the two-hour timebox.
