# Speech-Eval

**Finds speech delivery flaws: what went wrong, where it happened, and why.**

Speech-Eval compares a reading with a reference reading of the same text, word by word. It marks the exact words and seconds where pace, pitch, loudness, clarity or pausing go off, and explains every flag with the measured numbers. Built for **Track C: Contrastive Speech Analytics & Temporal Flaw Grounding** of the Multimodal AI Hackathon 2026.

| | |
|---|---|
| 🎬 **Demo video** | https://youtu.be/bbhAc6iyl7E |
| 🌐 **Public demo** (precomputed) | [huggingface.co/spaces/SriramMPS/Speech-Evalutaion](https://huggingface.co/spaces/SriramMPS/Speech-Evalutaion) |
| 📄 **Technical documentation** (6 pages) | [docs/report/report.pdf](docs/report/report.pdf) · [technical appendix](docs/report/technical-appendix.pdf) |
| 🗂️ **Dataset** (7.59 GB, SHA-256 pinned) | [Google Drive: speech-eval-dataset-v1.zip](https://drive.google.com/file/d/1rDbbPMKORv0nnQ-QnmbrQXIg1mqktvTm/view) |
| 🎙️ **Consented human takes** | [Google Drive: speech-eval-human-takes-v1.zip](https://drive.google.com/file/d/1mKosHQuSM9WXM-x6HUyDOZRhACzDwIgP/view?usp=drive_link) |

![Gettysburg take02 compared with take01 (Mode B): the planned awkward pause at 29.90–31.47 s, "larger | sense", is flagged at the exact words](reports/img/ui_results.png)

> *The planned 1.57 s pause inside "larger | sense" is found at exactly 29.90–31.47 s. The explanation shows the measured value, the reference value and how far apart they are.*

---

## What it does

- **Seven flaw types:** rushing, dragging, monotone, too quiet, mumbling, awkward pause, missing pause.
- **Three comparison modes:**

  | Mode | Compared with | Use it for |
  |---|---|---|
  | **A** | Expert readers of the same text | Strongest comparison; spreads come from real readers |
  | **B** | Your own earlier take | Rehearsal: what changed since last time |
  | **C** | Sentence norms from training speakers | No same-text reference; tips are heuristic and **not scored** |

- **Grounded explanations:** every flag has its words, start/end time, the measured value, the reference value and a z-score, e.g. *"you paused 1.57 s between 'larger' and 'sense', where your previous take had no pause."*
- **Dashboard:** a score card (pace, pitch, pauses, volume, clarity), the waveform with each flag drawn at its real width, filters by flaw type, a clickable transcript, and **Yours / Baseline** playback of the same words.

## How it works

```text
audio ─► convert + trim ─► words (given or ASR) ─► MFA forced alignment
      ─► per-word features in 3-word windows ─► compare with the same word in the reference
      ─► robust z-scores ─► flagged regions + pause events ─► explanations + score card
```

1. **Align:** the Montreal Forced Aligner gives every word a start and end time. It was chosen in a bake-off: 52 ms median boundary error, versus 72 ms for WhisperX.
2. **Measure:** syllable rate, pitch variation in semitones (relative to the speaker's median), loudness relative to the speaker's median, a 2–6 kHz vs 0–2 kHz clarity ratio, and the pause before each word. The relative measures make the comparison **speaker-agnostic**.
3. **Compare:** robust z = (T(x) − μ) / σ, with the median μ and spread s = 1.4826 × MAD of the reference readers. With few readers, σ² = (n·s² + 5·σ²_pool) / (n + 5), so a single reference still gives a usable spread.
4. **Flag:** |z| ≥ 3.5 (chosen on development speakers only). At least 3 flagged words in a sentence form a region. Pauses must also be physically noticeable: an awkward pause lasts ≥ 0.45 s; a missing pause is ≤ 40% of a reference pause of ≥ 0.3 s.
5. **Explain and score:** fixed numeric templates, with no LLM. Category score = 10 − Σ severity × (share of speech) × 10.

Every formula is derived step by step in the [technical appendix](docs/report/technical-appendix.pdf), Section A.

## Dataset

No public dataset marks delivery flaws with exact times, so we built one with **known flaw positions**.

- **1,103 recordings, 36.3 hours:** 30 public-domain originals (Gettysburg Address, 15 LibriVox readers; *O Captain! My Captain!*, 13 readers; Kennedy at Rice; Reagan after Challenger) plus 1,073 edited versions.
- **The good/bad gradient:** 7 flaw types × 5 severities, inserted at word-aligned positions with a fixed seed: speed ×1.15–2.0, pitch range kept 70–8%, gain −3 to −18 dB, inserted pauses 0.6–3.0 s, shortened pauses, and low-pass 3.5–1.3 kHz.
- **Split by speaker:** 18 train / 4 dev / 7 test. Test voices never choose a threshold.
- **Labels:** every edit has an exact time map; 13,812 files, each SHA-256 pinned.
- **Real recordings:** 8 consented takes by the author (CC BY 4.0), with 13 planned flaws whose positions were frozen before detection.

Details: [dataset card](docs/DATASET.md).

## Results (frozen v1, test speakers, evaluated once)

| Setting | Files | Precision | Recall [95% CI] | F1 [95% CI] | Clean alarms/min |
|---|---:|---:|---|---|---:|
| A-LOSO (expert readers) | 190 | 0.125 | **0.400** [0.328, 0.471] | 0.190 [0.156, 0.223] | 1.341 |
| B-same-speaker (own original) | 76 | 0.018 | 0.390 [0.289, 0.494] | 0.035 [0.026, 0.045] | 0.000 |

- **Best:** awkward-pause recall **0.90**; mumbling F1 **0.65** with no clean alarms. **Worst:** rushing recall 0.17.
- **Author's real takes:** all 4 planned pause flaws were found in Mode A; none of the 9 planned non-pause flaws produced a matching region.
- **Why mostly pause flags:** a near-zero reference pause spread turns tiny timing differences into huge z-scores. A **pre-registered 52 ms timing floor** removed 74–871 awkward-pause flags, but found no new non-pause flaws, so v1 stays primary. See [Phase 13](reports/phase13_pause_floor.md).

![Recall against injected severity](reports/img/recall_vs_severity_A-LOSO.png)

More: [Phase 6 results](reports/phase06_results.md) · [calibration](reports/phase06_calibration.md) · [scoring checks](reports/phase07_validation.md) · [Mode C](reports/phase08_mode_c.md) · [real takes](reports/phase10_human_takes.md).

## Quickstart

Requires **Git, Make and Docker** (with Compose). Python, Node, MFA and all models run inside Docker.

```sh
git clone https://github.com/mpssriram/speech-eval.git
cd speech-eval
make reproduce-quick   # downloads the dataset from Drive, verifies every SHA-256, runs the quick check (CPU)
make up                # starts the dashboard at http://localhost:8080
make reproduce         # reproduces all published benchmark numbers (CPU)
make test              # full Python test suite in Docker
```

Then open **http://localhost:8080**, click **Upload a recording**, choose a WAV, and pick the text and mode.

**If Drive asks for confirmation or hits a quota:** download the ZIP in a browser, then run:
```sh
make reproduce-quick DATA_ARCHIVE=/absolute/path/speech-eval-dataset-v1.zip
```

**Optional consented human takes:** `uv run python scripts/fetch_data.py --with-human-takes`

| Measured | Value |
|---|---|
| Quick reproduction (computation) | ≈ 12 s on CPU |
| Full reproduction | ≈ 225 s on CPU |
| Fresh clone → download → verify → quick check | 2,214 s total |
| Disk needed | ≈ 32.2 GB (16.8 GB image + 7.6 GB archive + 7.8 GB unpacked), plus extraction scratch |

Direct Docker Compose commands: [docs/DOCKER.md](docs/DOCKER.md).

## Reproducibility and honesty

- **Byte-identical:** a fresh clone reproduced **563 of 563** benchmark outputs exactly; two builds of the dataset archive have the same SHA-256 (`a41a1848…e374a23b`).
- **Decided before looking:** thresholds were chosen on dev speakers only; protocols were committed before each later run; one-shot markers block repeat test runs.
- **Post-hoc work is labelled:** the v2 detector and the pause floor are marked "test split previously seen with v1".
- **Static public demo, on purpose:** the Hugging Face Space serves the frozen results (38/38 files byte-identical to the report). It never uploads anyone's voice and can't drift from the published numbers. Live analysis needs MFA, Praat and a 16.8 GB image, so it runs locally with Docker.

## Repository layout

```text
src/speecheval/   features, flaw injection, references, detector, scoring
api/              FastAPI service and job runner
web/              React/Vite dashboard
deploy/hf-static/ static Hugging Face demo build
configs/          frozen flaws, splits, detector, rubric, release URL/SHA-256
data/             manifests and metadata (audio is git-ignored; download via make)
reports/          frozen results and reproduction evidence
docs/             technical report, dataset card, guides
```

## Limitations

- Synthetic edits approximate real flaws; they are not human judgements of quality.
- **Low precision** (0.125 in Mode A, 0.018 in Mode B), and the dev clean-alarm guard was not met (1.777/min vs ≤ 0.5).
- **No independent listener ratings yet.** The [rating pack](docs/RATING_PACK.md) is ready, with zero responses. No AI or self-ratings were used.
- The aligner's reference boundaries were placed visually (by Claude, without listening); no human spot-check was done.
- Real takes: one speaker, 13 recorder-confirmed labels. English read speech only. Mode C is heuristic.

<details>
<summary>Engineering notes</summary>

- **Plotly bundle-size warning:** Vite warns about chunk size. It's harmless and doesn't affect results.
- **Interpolation flag:** interpolated words are reported in the `warnings` list (`{type: interpolated, word: i}`), not as a per-word field.
- **MFA paths:** the Docker image supplies fixed compatibility paths for the pinned MFA models. Use the Docker workflow on other machines.
- `/api/health` reports the checkout commit, or `null` if unknown. Set `SPEECHEVAL_GIT_COMMIT` to override.

</details>

## Licence and credits

- **Code:** [MIT](LICENSE). **Labels, docs and the author's recordings:** [CC BY 4.0](LICENSE-DATA), with [recording consent](data/human/CONSENT.md).
- **Reader audio:** US public domain (LibriVox, JFK Library, Reagan Library). [Evidence](data/release/licences.json).
- **Author:** Sriram MPS, IIT Mandi, with assistance from Claude (Anthropic) and Codex (OpenAI).
- **Tools:** Montreal Forced Aligner, Praat (Parselmouth), librosa, CMU Pronouncing Dictionary, WhisperX, wav2vec 2.0. Thanks to the LibriVox volunteer readers.
Source audio retains its public-domain status per source. These grants were
explicitly authorised by the owner on 2026-10-12.
