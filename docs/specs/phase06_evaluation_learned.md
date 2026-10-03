# Phase 6 spec — Evaluation harness, calibration, learned detector

Read `AGENTS.md` and `docs/PLAN.md` (§4 evaluation protocol) first. Requires Phase 5.

## Goal

Measure detection quality honestly, tune thresholds on **dev only**, try a learned detector, and
produce the result tables and charts that go straight into the report.

## Step 1 — Matching and metrics (`src/speecheval/evaluate.py`)

**Matching** a predicted region P to a true flaw T:

- They must have the same `type`.
- Temporal IoU = |P ∩ T| / |P ∪ T| ≥ 0.3 (`eval.iou_min` in config).
- Boundary events (pauses) are matched on time distance instead: |centre(P) − centre(T)| ≤ 0.25 s.
- Use one-to-one greedy matching by highest IoU first, so each T and P is matched at most once.

**Metrics** (per type and overall):

| Metric | Definition |
|---|---|
| Recall | matched T ÷ all T |
| Precision | matched P ÷ all P |
| F1 | harmonic mean |
| Recall by severity | recall computed separately for severity 1, 2, 3, 4, 5 (the **stress-test curve**) |
| Onset / offset error | median \|P.start − T.start\| and \|P.end − T.end\| in ms, over matched region pairs |
| Mean IoU | over matched region pairs |
| False alarms per minute | predicted regions on **clean** source recordings of the evaluated split ÷ minutes of audio |
| Type confusion | for predictions that overlap a true flaw (IoU ≥ 0.3) but with a different type: a confusion matrix |
| Severity agreement | Spearman ρ between predicted and true severity over matched pairs |

Use bootstrap 95% confidence intervals for F1 and recall: 1,000 resamples over **files**, with a fixed seed.

## Step 2 — Calibrate on dev (`speecheval calibrate`)

1. Run `analyze-batch --split dev --setting A-LOSO`.
2. For each type, sweep `k` over 1.5, 1.75, …, 3.5. Pick the `k` that maximises F1 on dev, **subject to** false alarms on clean dev sources ≤ 0.5 per minute summed over all types. If no `k` meets that, pick the most conservative one.
3. Severity bins: fit the 4 cut-points between severities on dev matched pairs by maximising Spearman ρ, subject to the bins being increasing.
4. Write the result to `configs/detector.yaml`, keeping the old values in a comment.
5. Add `reports/phase06_calibration.md` with the sweep curves.

## Step 3 — Learned detector (optional by cut line 2) (`src/speecheval/learned.py`)

- **Unit:** one participant word.
- **Inputs:** the 5 z-features for words `j-2..j+2` (25 numbers, missing → 0), plus `sentence_final`, `first_sentence`, and relative position in sentence.
- **Target:** the true flaw type covering that word (`none` + 7 types), from labels mapped onto the participant's words.
  For boundary types, label the word **after** the boundary.
- **Training data:** train-split synthetic files analysed in A-LOSO. The reference model for each train speaker excludes that speaker.
- **Model:** `sklearn.ensemble.HistGradientBoostingClassifier(random_state=0, early_stopping=False)` with fixed hyper-parameters (max_iter 300, learning_rate 0.05, max_leaf_nodes 31) and class weights balanced.
  Use one thread (`OMP_NUM_THREADS=1`) so the result is bit-reproducible.
- **Prediction:** per-word class probabilities → per-type flags at probability ≥ 0.5 → the **same** region forming, conflict rules and severity estimate as the rule detector.
  Severity still comes from z, so explanations stay number-backed.
- Save the model with `skops` or `joblib` to `models/learned_v1.joblib`, with its training-data hash.
- Run it on dev and compare against rules. Choose per type which detector to use (`configs/detector.yaml: engine: {rushing: rules|learned, ...}`), based on dev F1 only.

## Step 4 — Final test evaluation (run ONCE) — `speecheval evaluate final`

After Steps 2–3 are frozen and committed, evaluate on **test** in every setting:

1. A-LOSO (test readers of Gettysburg and O Captain),
2. B-same-speaker (JFK, Reagan),
3. Human-A (user takes vs train readers),
4. Human-B (user take02–04 vs the user's take01).

Write `reports/phase06_results.md`:

- One headline table per setting: per-type precision, recall, F1 with CIs, onset/offset error, false alarms per minute.
- **Rules vs learned** for every setting.
- Charts in `reports/img/`:
  - `recall_vs_severity_{setting}.png` (one line per type),
  - `confusion_{setting}.png`,
  - `onset_error_hist.png`.
- A paragraph per setting stating strengths and weaknesses plainly, e.g. "mumbling severity 1–2 is not detected", or "awkward_pause timing error is 40 ms".

Record the git commit hash of the evaluated code in the report header. **If code changes after this, the test evaluation must be re-run, and the report must say so.**

## Tests

- IoU on hand-made intervals; greedy one-to-one matching on a crafted case where naive matching would double count.
- The boundary-event distance rule.
- False alarms per minute on a toy example.
- Bootstrap with a fixed seed gives a fixed CI.
- Learned-model training is reproducible: two runs produce identical predictions.

## Acceptance checklist

- [ ] `configs/detector.yaml` is calibrated on dev, with the calibration report committed.
- [ ] The learned detector is trained and compared (or explicitly dropped per cut line 2, with a note).
- [ ] `reports/phase06_results.md` has all four settings, the charts, and the commit hash.
- [ ] **USER + Claude** review the results before Phase 7.
- [ ] Tests pass; `PROGRESS.md` is updated.

## Out of scope

Rubric scores (Phase 7).
