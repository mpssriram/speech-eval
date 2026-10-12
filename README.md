# speech-eval: speech delivery analytics with temporal flaw grounding

Speech-Eval flags **what** differs in delivery, **where** it happens and **why**:
measured pace, pitch, loudness, clarity and pauses compared with a reference.
It supports rushing, dragging, monotone, too quiet, mumbling, awkward pause and
missing pause. Built for Track C of the Multimodal AI Hackathon 2026.
This is an experimental delivery benchmark, not a validated judgment of speaking
quality. The dev clean-alarm guard failed; genuine human validation is pending.

![Genuine Gettysburg take02 versus own take01, Mode B](reports/img/ui_results.png)

This screenshot uses the recorder's genuine take02 in frozen v1 Mode B against
take01, not a LibriVox smoke-test upload. The selected declared awkward pause is
29.90-31.47 s at larger|sense. [Screenshot provenance](reports/human_ui_verification.json).

Waveform intervals use the legend colours and their actual start/end widths.
Hover a coloured interval for its type/time label; Tab then Enter/Space selects
it by keyboard. Labels are not printed inside narrow regions, so they cannot
overlap or wrap. [Desktop/mobile checks](reports/waveform_ui_verification.json).

## Quickstart

```sh
git clone https://github.com/mpssriram/speech-eval.git
cd speech-eval
# Download the public checksum-pinned release (archive is not in Git):
make reproduce-quick
make up                 # foreground server; run in a second terminal, http://localhost:8080
make reproduce          # frozen Phase 6/7/8 numbers in Docker, CPU
make test               # Python tests inside Docker
```

Runtime dependencies are inside Docker/Compose: no host Python, Node, MFA or
model installation. Shell examples also use Git and Make; direct Compose
equivalents are in [Docker instructions](docs/DOCKER.md). First image/model
downloads and import are separate from numerical run time. Measured quick:
11.829 / 11.954 seconds; full: 225.204 / 223.142 seconds in the tested CPU
environment, not a universal laptop bound. [Fresh-clone proof](reports/reproducibility.md).
Disk measurement (2026-10-11): the current development checkout plus external
UV/MFA environment/models uses **57,456,644,096 allocated bytes (57.456644096 GB)**.
Docker Desktop's two non-sparse VHDX files total **39,405,486,080 bytes** for
**all Docker projects**. Combined measured snapshot: **96,862,130,176 bytes
(96.862130176 GB)**, not this project's fresh-install minimum. Historical caches,
two archive copies and the host GPU environment are included. The exact
Docker-inclusive fresh-install/peak-build requirement is **NOT MEASURED**:
Docker currently fails to start, so project image/layer/cache attribution and
fresh import cannot be measured. No requirement is estimated.
[Component measurements and method](docs/DATASET.md#measured-disk-footprint),
[machine evidence](reports/disk_usage.json), [blocker](docs/BLOCKERS.md).

`make up` defaults to the checkout commit for image metadata; an explicit
`SPEECHEVAL_GIT_COMMIT` environment/Make value overrides it. For
direct Compose, first run `export SPEECHEVAL_GIT_COMMIT=$(git rev-parse HEAD)`;
the `GIT_COMMIT` build arg is stored as `SPEECHEVAL_GIT_COMMIT`. `/api/health`
prefers an actual checkout HEAD, otherwise this build/runtime value. Without
either source it still reports `null` honestly, never an invented commit.

## Download releases

[Main dataset archive](https://drive.google.com/file/d/18wOjIvKjvabN2hnUUH8y2k1I7dpOYDxV/view)
and [release folder](https://drive.google.com/drive/folders/140b1eGAVj7u0Tm0Q97Q5eNCA-fRt0-LI)
are shared as "Anyone with the link" by the owner. Anonymous gdown main-file
transport was checked with a 1 MiB ZIP response; full SHA256 was checked locally.

| File | Exact bytes | SHA256 | Download |
|---|---:|---|---|
| speech-eval-dataset-v1.zip | 7,586,867,457 | `a41a18482a72107e449d9562d106a94193f90b8a4e11718bdbfdf746e374a23b` | Main link above; Drive ID `18wOjIvKjvabN2hnUUH8y2k1I7dpOYDxV` |
| speech-eval-human-takes-v1.zip | 62,520,905 | `33e8e0e80a562dfc40e828f6ef1d9ff5285cf24ae543b5dbb7b6ff31377658bd` | Correct local file prepared; replacement upload required |

The supplied takes file is a dataset-sized ZIP rather than this human release;
its link is excluded from download metadata. Upload the exact local
`data/release/speech-eval-human-takes-v1.zip`, then provide its new Drive ID.
The main ZIP is immutable and contains no new human takes. Human takes are a
separate optional release; the scientific corpus and frozen results stay fixed.

```sh
make reproduce-quick   # anonymous Drive download, checksum verification, CPU Docker
make reproduce
# Optional takes, once a verified replacement upload is configured:
uv run python scripts/fetch_data.py --with-human-takes
```

Downloader: [gdown](https://github.com/wkentaro/gdown), pinned to 5.2.0 in
pyproject.toml/uv.lock. File IDs are used instead of downloading Drive HTML.
Every archive and payload hash is checked before installation; conflicting
existing files are refused. Optional takes do not enter `make reproduce` metrics.

Manual fallback: open the main link in a browser, click Download and save the ZIP,
then run `make reproduce DATA_ARCHIVE=/absolute/path/speech-eval-dataset-v1.zip`.
With host Python dependencies installed, the equivalent import is:

```sh
uv run python scripts/fetch_data.py --from-local /absolute/path/speech-eval-dataset-v1.zip
# The prepared human ZIP is usable now without a public upload:
uv run python scripts/fetch_data.py --from-local /absolute/path/speech-eval-dataset-v1.zip \
  --with-human-takes --human-from-local /absolute/path/speech-eval-human-takes-v1.zip
```

Drive may impose quotas or a confirmation page. Browser downloads still undergo
the same size/SHA256/member checks; do not replace the pinned hash to accept a
different file. Evidence: `reports/drive_download_probe.json` and
`reports/human_release_verification.json`.

## Three modes

| Mode | Reference | Use |
|---|---|---|
| A: same text | Train-reader distribution; institutional texts have a single original | Known-text comparison, not an ideal-speaker standard |
| B: rehearsal | Your own earlier completed take of the same words | Per-flaw change, not automatically validated improvement |
| C-lite | Train-speaker sentence norms; labelled key-moment heuristics | New-speech prototype, weaker and not every flaw type |

Upload a WAV and select text/mode. Supply actual as-spoken words for slips,
excerpts and arbitrary Mode C speech. A/B phrase playback requires the same words
in the baseline; C has no invented same-text baseline. [Browser proof](reports/phase09_ui.md).

## How it works

```text
audio -> format conversion/energy trim -> supplied or automatic words -> real MFA
      -> frames/words/windows/sentences -> speaker-relative features
      -> reference deviations -> regions/events -> numeric templates -> rubric -> API/UI
```

No LLM or sampling in scoring. JSON byte identity is verified for the pinned CPU
pipeline, not every platform/automatic-ASR configuration. [Technical report](docs/report/report.md),
[six-page PDF](docs/report/report.pdf).

## Dataset

The frozen release contains **1,103 indexed variants / 36.26268833333334 hours**:
30 originals and 1,073 injected recordings. Duplicate rates/raw downloads are not
counted again. Original readers: 15 Gettysburg, 13 O Captain, plus JFK and Reagan.
One clipped source is audit-only; eligible originals have seven effects at five
severities and mixed variants. Seeded labels/time maps describe controlled edits,
not independent perceptual truth. Detection uses real MFA, not oracle alignment.

Speakers stay separate across splits. A/C populations use train only; B test pairs
deliberately compare an edited JFK/Reagan take with their own original.
[Dataset card](docs/DATASET.md), [rights and archive proof](reports/reproducibility.md).

## Results

Copied from [frozen Phase6](reports/phase06_results.md); synthetic labels, not
human speaking-quality judgments:

| Setting | Files | Precision | Recall | F1 [95% CI] | Clean alarms/min |
|---|---:|---:|---:|---|---:|
| A-LOSO | 190 | 0.125 | 0.400 | 0.190 [0.156, 0.223] | 1.341 |
| B-same-speaker | 76 | 0.018 | 0.390 | 0.035 [0.026, 0.045] | 0.000 |

Dev clean-alarm guard **not met**: 1.777 alarms/min versus ≤0.5. Low precision
and misses are limitations. Learned detector was not trained. [Calibration](reports/phase06_calibration.md).

![Recall versus severity](reports/img/recall_vs_severity_A-LOSO.png)

Mode C's separate sentence/type comparison uses 175 eligible files: reference
recall 0.324 versus C 0.179. Do **not** compare directly with the Phase6 word-region
aggregate. [Mode C eligibility/results](reports/phase08_mode_c.md).

Scores were checked for monotonicity and reproducibility, **not yet against human
raters**. Constant/non-monotonic series are disclosed in [Phase7](reports/phase07_validation.md).
Fresh GitHub-clone Docker reproduction matched all 563 scientific outputs
byte-for-byte twice; [scope and hashes](reports/reproducibility.md).

## Human takes and blind ratings

The eight-take workflow is ready but genuine recordings, consent, notes and
as-spoken transcripts are absent. A real-MFA synthetic smoke check is strictly
workflow evidence and missed its injected region; no tuning followed.
[Instructions](docs/HUMAN_TAKES.md), [Phase10](reports/phase10_human_takes.md).

The twelve-clip [rating pack](docs/RATING_PACK.md) and agreement script are ready.
Distribute only `data/rating_pack/`, never the private key or repository.
Actual independent responses/human correlations remain pending.

## Repository layout

```text
src/speecheval/   deterministic features, edits, references, detector, scoring
api/             FastAPI and real job runner
web/             React/Vite dashboard
configs/         locked flaws, splits, detector, rubric, release URL/SHA
data/            manifests, metadata, git-ignored audio; blind/private pack separated
reports/         frozen results, authorised workflow/reproduction evidence
docs/            dataset card, technical report, guides, blockers
```

## Limitations and attributions

Known **Plotly bundle-size warning**: Vite warns that the bundled chart library
exceeds its chunk-size advisory. It is harmless for correctness: it is not a
build error and does not change audio, detections or scores. It can increase
initial download/parse time. Accepted browser checks are linked above; no refactor
or warning suppression is applied.

Retained interpolation-flag schema limitation: the mapper temporarily sets
`interpolated: true` on words, but the validated Word schema omits that extra
field. The persistent `warnings` entry `{type: interpolated, word: i}` survives
and drives the API's interpolation guard. Consumers must read that warning list,
not assume a per-word flag. A characterization test records this behavior;
the frozen aligner/schema was not changed.

Retained MFA portability limitation: participant model identity uses
`/home/sriram/Documents/MFA/pretrained_models`, with the existing conda path
`/home/sriram/miniforge3`. The Dockerfile deliberately supplies those compatibility
paths. A differently named host account is not automatically supported; use the
documented Docker workflow. No post-test producer-path change was made.

Synthetic edits approximate real flaws; LibriVox readers are not ideal orators;
English-only proxies do not establish accent fairness; Mode C is heuristic.
Claude annotated the visual alignment reference without listening; no human
spot-check was done. Human agreement was not measured: no independent raters
were available; no AI or self-ratings were used. Rubric scores are designed
penalties, not a validated perceptual scale or causal proof. [Next actions](NEXT.md).

Audio has source-specific public-domain evidence **in the USA**, not a blanket
worldwide licence. [Evidence](data/release/licences.json), [card](docs/DATASET.md).
Author: **Sriram MPS, IIT Mandi, with assistance from Claude (Anthropic) and Codex (OpenAI)**.
Code: [MIT](LICENSE). Labels, annotations, docs and the author's recordings:
[CC BY 4.0](LICENSE-DATA), with original [recording consent](data/human/CONSENT.md).
Source audio retains its public-domain status per source. These grants were
explicitly authorised by the owner on 2026-10-12.
