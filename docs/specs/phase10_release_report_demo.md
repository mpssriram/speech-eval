# Phase 10 spec — Reproducible release, published dataset, report, demo video

Read `AGENTS.md` and `docs/PLAN.md` first. Requires Phases 1–9 (or their cut versions).

## Goal

Everything a judge needs: a repository that reproduces our numbers with one command, a public dataset link,
a technical report of at most 6 pages, and a 3–10 minute video.

## Step 1 — One-command reproduction (`make reproduce`)

Runs inside Docker (CPU), from published data:

1. `speecheval fetch --from-release`: download the published dataset archive (Step 2) and verify sha256s.
2. `prepare` → `align` → `features`, using the **frozen** excerpts and windows (no ASR).
3. `dataset build` (re-generates synthetic files from sources + seeds; hashes must match the published ones).
4. `evaluate final`, `validate severity`, `validate repro`. (`validate human` reuses the committed ratings CSVs.)
5. Writes `reports/reproduced/` and compares every number against `reports/phase06_results.md` and `phase07_validation.md`. It prints `REPRODUCED OK`, or a diff.

Also provide `make reproduce-quick`: one text and 3 test readers, < 15 minutes on a laptop CPU, for judges in a hurry.

Write `reports/hashes.sha256` for all generated artefacts. `make verify` re-checks them.

## Step 2 — Publish the dataset

- **Archive:** `speech-eval-dataset-v1.zip` containing:
  - source audio (FLAC),
  - synthetic audio (FLAC, hq only; 16 kHz is re-creatable),
  - transcripts, alignments, labels,
  - `dataset_index.csv`, `DATASET.md`, `LICENSES.md`,
  - consented human takes.

  If the archive is > 2 GB, split it into one archive per text.
- **Host:** Hugging Face Datasets (preferred; versioned, citable) **or** a public Google Drive folder. The link goes in the README and the report.
- **USER** creates the hosting account and uploads; Codex prepares the archives and the upload commands.
- `LICENSES.md` lists:
  - every source with its license and evidence URL;
  - the statement that derived synthetic audio inherits public-domain status;
  - the license we choose for our labels and code (recommend CC BY 4.0 for data and MIT for code; the **USER** decides).

## Step 3 — README (`README.md`)

1. One-paragraph summary + a dashboard screenshot.
2. Quickstart:
   - `git clone`, `make up` (dashboard),
   - `make reproduce-quick`,
   - `make reproduce`.
3. The architecture diagram (pipeline: prepare → align → features → reference → detect → explain → score → API/UI).
4. Results summary: the headline table from Phase 6, plus one chart.
5. The dataset link, and a summary of the dataset card.
6. Repository layout, and how to run tests.
7. Limitations (short) and a link to the report.
8. Attributions and licenses.

## Step 4 — Technical report (`docs/report/report.md` → PDF, max 6 pages)

Codex drafts the report from the phase reports. Claude edits it, and the **USER** approves. Sections and page budget:

| # | Section | Pages | Content source |
|---|---|---|---|
| 1 | Problem and approach | 0.5 | PLAN.md, track statement |
| 2 | Contrastive dataset construction | 1.25 | DATASET.md, phase03/04 reports, listening sheet |
| 3 | Features and speaker normalisation (with equations) | 0.75 | phase02 |
| 4 | Detection, temporal grounding and causal explanation | 1.0 | phase05/06 (equations for z, shrinkage, rules; example explanations) |
| 5 | Scoring rubric and its validation | 0.75 | phase07 |
| 6 | Results across settings (A-LOSO, B, C, Human) | 1.0 | phase06/07/08 tables and charts |
| 7 | Limitations and future work | 0.5 | all phases. Be specific: synthetic flaws are approximations, LibriVox reading style, English only, Mode C heuristics, small human set |
| 8 | Reproducibility and attributions | 0.25 | phase10 |

Build the PDF with `pandoc` + a LaTeX template (11 pt, A4, 2 cm margins). Check the page count automatically.

## Step 5 — Demo video (USER records; Codex prepares assets)

Codex writes `docs/video/script.md` (target 6–7 minutes) with this outline:

| Time | Segment | On screen |
|---|---|---|
| 0:00–0:30 | The problem: subjective judging, vague feedback | Title card + one sentence |
| 0:30–2:00 | The dataset: public-domain sources, 15 readers of the same text, flaw injection. Play severity 1 vs severity 5 of the same flaw. | `index.html` listening page, composition table |
| 2:00–4:00 | Live demo: upload a flawed human take, then walk through the score card, a flaw card, the explanation, and ▶ yours vs ▶ baseline | Dashboard |
| 4:00–5:00 | Results: recall-vs-severity chart, the cost of no reference, human-agreement scatter | Report charts |
| 5:00–6:00 | Real use: your pitch rehearsals, scores improving across takes (Mode B/C) | Progress chart + clips |
| 6:00–6:30 | Limitations, reproducibility (`make reproduce`), dataset link | README |

The **USER** records the screen (OBS or the Xbox Game Bar), plus a voice-over, and uploads it to YouTube as unlisted or public. The link goes in the README.

## Step 6 — Submission checklist (`docs/SUBMISSION.md`)

- [ ] Public GitHub repo; README complete; license files present.
- [ ] Dataset link works from a logged-out browser.
- [ ] `make reproduce-quick` passes on a fresh clone (tested in a new WSL folder).
- [ ] Report PDF ≤ 6 pages, in the repo and attached to the submission.
- [ ] Video link works and is 3–10 minutes long.
- [ ] Every number in the report and video matches `reports/phase06_results.md` / `phase07_validation.md`.
- [ ] Attributions present in the README, the report and the dataset.
- [ ] Repo switched from private to **public** at submission time.

## Acceptance checklist

All boxes in `docs/SUBMISSION.md` are ticked.
