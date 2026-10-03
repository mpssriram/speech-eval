# Phase 7 spec — Rubric scores and their validation

Read `AGENTS.md` and `docs/PLAN.md` first. Requires Phase 6 (frozen detector).

## Goal

Turn detected flaws into reproducible rubric scores (0–10 per category, plus overall), and **prove** the scores behave sensibly with three tests.

## Step 1 — Rubric (`src/speecheval/score.py`, `configs/rubric.yaml`)

```yaml
categories:
  pace:    {types: [rushing, dragging],             kind: duration}
  pitch:   {types: [monotone],                      kind: duration}
  volume:  {types: [too_quiet],                     kind: duration}
  clarity: {types: [mumbling],                      kind: duration}
  pauses:  {types: [awkward_pause, missing_pause],  kind: event}
weights:   {pace: 0.25, pitch: 0.25, pauses: 0.20, volume: 0.15, clarity: 0.15}
duration_weight: 10.0      # penalty = severity * (region_duration / total_speech_duration) * duration_weight
event_penalty: 0.4         # penalty = severity * event_penalty, per pause event
```

For each category c:

- **Duration categories:** `penalty_c = Σ_r severity_r × (dur_r / D) × duration_weight`.
  D = total speech duration (first word start to last word end).
- **Event categories:** `penalty_c = Σ_e severity_e × event_penalty`.
- `score_c = clamp(10 − penalty_c, 0, 10)`, rounded to 1 decimal.
- `overall = Σ_c weight_c × score_c`, computed from the **rounded** category scores, then rounded to 1 decimal.
- All rounding uses `decimal.Decimal` with `ROUND_HALF_UP`. Python's `round()` rounds 9.25 down to 9.2, which looks like a bug to users.

Worked example for the report: one severity-3 rushing region covering 10% of the speech gives pace = 10 − 3 × 0.10 × 10 = **7.0**.

Weights are a documented design choice; the report states why. Pace and pitch weigh most because they dominate perceived delivery, and the weights are configurable. Do not claim the weights come from an external standard unless the user provides one.

Store scores in the analysis JSON under `scores` (AGENTS.md §6.4). Scores are a pure function of the regions, so they are fully reproducible.

## Step 2 — Validation test 1: severity monotonicity (`speecheval validate severity`)

For every test-split source and every flaw type, take the 5 single-flaw files (severity 1–5) and their category score:

- Spearman ρ between severity and score. A perfect result is ρ = −1: higher severity, lower score.
- Report the median ρ per type, and the % of (source, type) series that are non-increasing.
- Chart: `reports/img/score_vs_severity.png`, the mean category score ± SD at each severity, one line per type.

## Step 3 — Validation test 2: agreement with human listeners (`speecheval validate human`)

**3a. Codex builds a blind rating pack.**

- Choose 18 recordings with a fixed seed:
  - 6 clean test sources,
  - 8 synthetic test files spread over types and severities (2–5),
  - 4 human takes.
- Copy them to `data/rating_pack/` with anonymous names `clip_01…clip_18` in a shuffled order. The mapping is stored in `data/rating_pack/key.json`; raters must not open it.
- Write `data/rating_pack/ratings_template.csv` with columns `rater, clip, pace, pitch, pauses, volume, clarity, overall`, each a score from 1 to 10.
- Write `data/rating_pack/instructions.md` with a one-paragraph definition of each category and an anchor: "10 = like a skilled public speaker, 1 = severely flawed".

**3b. USER** + at least 2 other people rate all clips **independently**, without seeing system scores. Save files as `ratings_{rater}.csv`.

**3c. Codex computes:**

- Inter-rater agreement per category: mean pairwise Spearman ρ between raters, plus Krippendorff's α (interval).
- System vs humans: Spearman ρ between the system score and the mean human score, per category and overall, with a bootstrap 95% CI.
- `reports/phase07_validation.md` with these tables, plus a scatter plot of system overall vs mean human overall.
- Interpretation rule for the report: if system–human ρ is close to the human–human ρ, the system agrees with people about as well as people agree with each other.

## Step 4 — Validation test 3: reproducibility (`speecheval validate repro`)

1. Analyse the same 10 files twice on the host, and once inside Docker (CPU).
2. Compare the analysis JSON hashes.
3. Report any mismatch with a diff of the first differing field.

The target is 10/10 identical in all three runs.

- If host GPU vs Docker CPU differ **only** because of the aligner, that's a finding to report.
- Fix it by making MFA (CPU) the only aligner used in the analysis path.

## Tests

- The worked example gives exactly 7.0.
- Clamping at 0 and 10.
- Overall weighting arithmetic.
- An empty region list gives all categories 10.0.

## Acceptance checklist

- [ ] Scores appear in every analysis JSON.
- [ ] The severity-monotonicity report and chart are done.
- [ ] **USER**: the rating pack has been rated by ≥ 3 people; the agreement report is done.
- [ ] Reproducibility is 10/10, or the mismatch is explained and fixed.
- [ ] Tests pass; `PROGRESS.md` is updated.

## Out of scope

Mode C (Phase 8), UI (Phase 9).
