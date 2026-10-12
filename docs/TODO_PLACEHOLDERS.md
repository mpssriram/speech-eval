# Unfilled draft placeholders

These are missing evidence, not zero-valued results. Authoring used the supplied
README/report/video drafts. Numeric substitutions come only from `reports/*.md`.
Some unsupported claims were replaced by explicit pending prose rather than
leaving a misleading sentence around a blank number.

| Original placeholder | Why not filled / action |
|---|---|
| `{{disk_gb}}` | Resolved measured image + archive + unpacked payload snapshot: 32.170019620 GB in reports/reproduction_disk_usage.json. Clean-build peak remains unmeasured; no minimum is inferred. |
| `{{dataset_url}}` | Resolved: verified new main Drive ID in configs/dataset.yaml. Owner-confirmed human-takes link also configured; old folder retired, replacement folder optional. |
| `{{author name}}` | Resolved: Sriram MPS, IIT Mandi, with assistance from Claude (Anthropic) and Codex (OpenAI). |
| `{{video_url}}` | Video recording/publication not supplied. |
| `{{example_explanation}}` | Resolved by the explicitly requested verbatim correct-hit example from analysis 86964ad39ead in report section 4, with file ID and measured values. |
| `{{rho_severity}}`, `{{pct_nonincreasing}}` | No single aggregate defined/reported. Replaced with exact per-type Phase7 table. |
| `{{n_human_takes}}` | Resolved: eight recorder-confirmed consented takes, separate release. |
| `{{n_raters}}`, `{{n_clips}}` in rated-clips claim | No real rater responses. Planned twelve clips are not twelve rated clips; minimum requested raters is not an observed count. |
| `{{rho_hh}}`, `{{rho_sh}}`, `{{rho_sh_ci}}` | No actual independent ratings; current agreement script does not estimate CIs. |
| `{{f_c}}` | Phase8 does not report aggregate C F1; no value derived under report-only substitution rule. C paired table uses reported precision/recall/alarms. |
| `{{p_h}}`, `{{r_h}}`, `{{f_h}}`, `{{fa_h}}` | Genuine hit/miss/FP and FP/min counts now reported in Phase10 and report section 7.1; independent annotation remains absent. |
| `{{spotcheck_result}}` | No human listening/boundary spot-check supplied; no numerical annotation-error estimate. |
| `{{p_rate}}`, `{{r_rate}}`, `{{z}}` | No exact live-demo explanation values in supplied reports. Read actual UI during demo, or add genuinely measured evidence to an authorised existing result report. |
| `{{r_sev45}}` | No reported pooled severity-4/5 recall. Do not read an invented aggregate off the chart. |
| `{{n_flags_take1}}`, `{{k}}`, `{{n_flags_takek}}` | No genuine own pitch-rehearsal sequence/results. Replaced with explicitly labelled engineering workflow segment. |

## Filled evidence map

| Draft fields | Source |
|---|---|
| repo_url, n_files=1103 indexed variants, n_hours=36.26268833333334, n_gettysburg=15, n_ocaptain=13, train/dev/test=18/4/7; quick/full run times, scientific output identity | reports/reproducibility.md |
| mfa_median_ms=52.0, wx_median_ms=72.0, n_unclear=23 | reports/day01_aligner_bakeoff.md |
| commit=aaf1832fe24a193d4c90f9e7a2ff9537b753335c, A/B precision/recall/F1/CI/alarms, matched onset/offset | reports/phase06_results.md |
| selected k=3.50, severity bins and dev severity rho | reports/phase06_calibration.md |
| per-type severity rho/non-increasing/constant counts; host n_repro=10/10 | reports/phase07_validation.md |
| p_c=0.020, r_c=0.179, fa_c=4.159; paired reference recall=0.324 (not Phase6 A recall 0.400) | reports/phase08_mode_c.md |
| browser demo overall=9.4, regions=2, phrase playback evidence | reports/phase09_ui.md |
| eight genuine takes, recorder-confirmed labels, hits/misses/FP and live explanations | reports/phase10_human_takes.md; data/human/evaluation.json; reports/human_hit_demo.json |

Formal owner grants are now in LICENSE (MIT code) and LICENSE-DATA (CC BY 4.0
labels, annotations, docs and consented recordings). Source audio remains public
domain per source. Both archive links are configured; the remaining publication item is
the recorded video. No independent rater data or spot-check is invented.
