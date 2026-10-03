# speech-eval — Master plan

Track C, Multimodal AI Hackathon 2026. Team: user + Claude (specs, maths, review) + Codex (implementation).

**How to use this file:** run the phases in order. Each phase has its own spec in `docs/specs/`.
Give Codex exactly one phase at a time:

> Read AGENTS.md and docs/PLAN.md, then implement docs/specs/<phase file>. Follow its acceptance checklist. Stop when the checklist passes, or when you reach a step marked **USER**, and report.

After each phase: the user runs the acceptance checks, commits, and sends the report to Claude for review before starting the next phase.

---

## 1. Phases at a glance

| Phase | Day | Spec | Produces | Milestone (phase is done when…) |
|---|---|---|---|---|
| 1 | 1 | `day01_data_and_alignment.md` | Clean audio, verified transcripts, word timestamps, aligner choice | Word timestamps for every source recording; bake-off report |
| 2 | 2 | `phase02_features_and_docker.md` | Frame/word/sentence features, speaker normalisation, Docker skeleton | Two Gettysburg readers' curves overlaid; `docker run … pytest` passes |
| 3 | 3 | `phase03_flaw_injector.md` | 7 flaw types × 5 severities, exact labels, time maps | One file per type × severity sounds right to the user |
| 4 | 4 | `phase04_dataset_and_human.md` | Full synthetic dataset, splits, dataset card, user recordings + labels | **Dataset v1 frozen** |
| 5 | 5 | `phase05_detection_modes_ab.md` | Reference model, detector, explanations, Mode A + Mode B, CLI | **MVP:** audio in → flaw regions + explanations out |
| 6 | 6 | `phase06_evaluation_learned.md` | Evaluation harness, threshold calibration, learned detector | Test-set accuracy tables and severity curves |
| 7 | 7 | `phase07_scoring_validation.md` | Rubric scores, severity-monotonicity and human-agreement validation | Scores validated with Spearman tests |
| 8 | 7–8 | `phase08_mode_c_lite.md` | Good-speaker norms + key-moment checks (no reference needed) | Mode C runs on any speech; cost-of-no-reference measured |
| 9 | 8–9 | `phase09_api_dashboard.md` | FastAPI + React dashboard, `docker compose up` | Full demo works in the browser |
| 10 | 9–10 | `phase10_release_report_demo.md` | Reproducible release, published dataset, report, demo video | **Submitted** |

Rest: keep the afternoon of Day 7 free. If a phase finishes early, start the next one; do not add features.

## 2. Who does what in every phase

| Role | Responsibilities |
|---|---|
| **User** | Runs commands, listens to audio, records takes, hand-labels in Praat, rates recordings, makes go/no-go decisions, records the demo |
| **Claude** | Writes and revises specs, reviews Codex output and reports, debugs, owns the maths (normalisation, statistics, scoring), drafts the report |
| **Codex** | Implements specs, writes tests, runs pipelines, writes generated reports |

Steps marked **USER** in a spec are done by the user. Codex stops and reports when it reaches one.

## 3. Dependencies

```
P1 alignment ──► P2 features ──► P3 injector ──► P4 dataset ──► P5 detection ──► P6 evaluation ──► P7 scoring
                     │                                                  │                              │
                     └──► Docker skeleton (P2) ─────────────────────────┴──► P9 dashboard ◄────────────┘
                                                                        P5 ──► P8 Mode C-lite
P1–P9 ──► P10 release
```

## 4. Evaluation protocol (decided now so nothing leaks later)

A synthetic flawed file is made from one source recording. If we compared it against that same recording,
detection would be trivially easy, because any difference would be the flaw. So results are reported in
three clearly separated settings:

| Setting | Files | Reference used | What it shows |
|---|---|---|---|
| **A-LOSO** (main result) | Flawed Gettysburg and O Captain files | Distribution of *other* readers only (leave-one-speaker-out) | Expert comparison with a different speaker, the realistic case |
| **B-same-speaker** | Flawed JFK and Reagan files | The original recording of the same speaker | Rehearsal comparison (Mode B) |
| **C-no-reference** | All flawed test files | Good-speaker norms only | Cost of having no same-text reference |
| **Human** | User's own recordings | A: train-split readers; B: user's own clean take | Works on real human mistakes |

Splits are by **speaker** (Phase 4, `configs/splits.yaml`). Test speakers are never used to build reference
distributions, calibrate thresholds, or train the learned detector. Test numbers are computed once, at the end of Phase 6.

## 5. Cut lines (what to drop if late, in this order)

1. Phase 8 shrinks to: norms for speech rate and sentence-end pause only, plus a report section.
2. Phase 6 learned detector is dropped. The rule-based detector ships, and the report says so.
3. Phase 9 dashboard drops in-browser recording and the rehearsal history chart.
4. Mixed-flaw files (Phase 4) are dropped.

Never cut: Phase 1 alignment quality, Phase 4 labels, Phase 6 evaluation tables, Phase 10 reproducibility.

## 6. Contingencies (if X happens, do Y)

| If… | Then… |
|---|---|
| An aligner fails badly on the old recordings (1948/1961/1962) | Keep them only as a robustness appendix. Build the core on clean recordings. |
| A LibriVox reader read a different version of the text | Keep it; the as-spoken transcript handles it. If more than 10% of words differ, drop that reader from reference distributions. |
| PSOLA pitch flattening sounds robotic at high severity | Cap monotone at severity 4 and note it; rely on human takes for strong monotone. |
| Rushing/dragging via rubberband has audible artefacts | Lower the extremes (severity 5 = 1.8× / 0.55×) and document it. |
| The detector's recall at severity 1 is near zero | Expected and fine; severity 1 is "barely audible". Report the curve honestly. |
| False alarms on clean test readers are > 1 per minute | Raise thresholds on the dev split, or require 3+ consecutive words; re-check recall. |
| The learned detector doesn't beat rules on the test set | Ship rules; report both. |
| Behind at end of Day 5 (no MVP) | Apply cut lines 1–3 immediately. |
| Codex fails twice on the same step | Stop. Send the error to Claude, who either rewrites the step or writes that module directly. |
| Disk fills up | Generated audio is FLAC (lossless). Delete `data/flawed/**/align16k` (re-creatable) first. |

## 7. Daily routine

1. Start: `git pull`, read today's spec, start Codex on it.
2. Mid-day: run the acceptance checks done so far; send any failures to Claude.
3. End: `git add -A && git commit -m "phase N: …" && git push`. Append to `docs/specs/PROGRESS.md`.

## 8. Final deliverables (from the problem statement)

| Deliverable | Produced in |
|---|---|
| GitHub repository with code and documentation | All phases; README in Phase 10 |
| Custom dataset (paired good/flawed audio, transcripts, alignment labels), public link in README | Phases 1, 3, 4; published in Phase 10 |
| Interactive dashboard (upload, feature extraction, visual + text results) | Phase 9 |
| Technical documentation, max 6 pages (dataset construction, rubric, model, scoring) | Phase 10 |
| 3–10 min YouTube video (dataset collection, stress testing, dashboard catching deviations) | Phase 10 |
