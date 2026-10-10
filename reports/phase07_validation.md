# Phase 7 scoring validation

Scores are deterministic penalties, not a validated perceptual scale. Configurable design weights: pace/pitch 0.25 each, pauses 0.20, volume/clarity 0.15 each; pace/pitch are emphasized because of their perceived delivery importance, not an external standard. Decimal ROUND_HALF_UP is used, with overall computed from rounded category scores.

Worked example: severity-3 rushing over 10% of speech gives pace = 10 − 3×0.10×10 = 7.0.

## Severity monotonicity

| Type | Complete series | Median Spearman | Non-increasing % | Constant series |
|---|---:|---:|---:|---:|
| awkward_pause | 7 | -0.8660254037844386 | 85.71428571428571 | 3 |
| dragging | 7 | -0.7071067811865475 | 71.42857142857143 | 2 |
| missing_pause | 7 | -0.7071067811865475 | 100.0 | 4 |
| monotone | 7 | -0.7071067811865475 | 28.571428571428573 | 0 |
| mumbling | 7 | -0.8944271909999157 | 71.42857142857143 | 0 |
| rushing | 7 | -0.7071067811865475 | 71.42857142857143 | 1 |
| too_quiet | 7 | -0.7071067811865475 | 85.71428571428571 | 3 |

Constant series have undefined Spearman; non-increasing alone does not demonstrate sensitivity.
Incomplete five-severity series excluded: 0.

![Score vs severity](img/score_vs_severity.png)

## Reproducibility

Actual two-run host byte identity: 10/10.
PENDING Phase 9 CPU image test; host-only evidence is not cross-environment proof

## Independent human agreement

PENDING: actual user takes and independent ratings from at least three raters. No inter-rater alpha, system–human correlation or confidence interval can be claimed yet.
