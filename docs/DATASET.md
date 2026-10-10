# Speech-Eval dataset card

Release: `speech-eval-dataset-v1.zip`, built and verified 2026-10-10.
Purpose: English speech **delivery** stress testing and temporal grounding,
not content assessment, accent grading or a validated perceptual-quality scale.
Public upload is pending. The exact archive can already be imported locally;
see [reproduction evidence](../reports/reproducibility.md) and [Docker guide](DOCKER.md).
The archive is **not in Git**. Until its owner uploads it and fills the URL in
`configs/dataset.yaml`, a fresh clone requires the separately supplied ZIP via
`make reproduce-quick DATA_ARCHIVE=/absolute/path/speech-eval-dataset-v1.zip`.
A clone alone cannot manufacture or download the unpublished corpus.

## Sources, rights and attribution

| Text / source | Original recordings | Attribution and evidence |
|---|---:|---|
| Gettysburg Address | 15 | Abraham Lincoln text; LibriVox 150th-anniversary volunteer-reader collection, [catalogue](https://archive.org/details/gettysburgaddress_150anniv_1311_librivox), [LibriVox rights](https://librivox.org/pages/public-domain/) |
| O Captain! My Captain! | 13 | Walt Whitman text; LibriVox volunteer readers, [catalogue](https://archive.org/details/o_captain_librivox), [LibriVox rights](https://librivox.org/pages/public-domain/) |
| JFK Rice University address | 1 | John F. Kennedy Presidential Library, item JFKWHA-127-002, [item rights: Public Domain](https://www.jfklibrary.org/asset-viewer/archives/jfkwha-127-002) |
| Reagan Challenger address | 1 | Ronald Reagan Presidential Library, WHCA audiotape PP6028B / 7087577, [audio item](https://www.reaganlibrary.gov/archives/audio/remarks-president-reagan-during-address-nation-space-shuttle-challenger-oval-office), [collection rights](https://www.reaganlibrary.gov/archives/audiovisual/white-house-communications-agency), [audio inventory](https://www.reaganlibrary.gov/archives/whca-presidential-audio-collection-1981-89) |

Public-domain evidence applies in the **USA**. It was checked by reading primary
institutional pages automatically, not by an independent human legal review.
Rights elsewhere may differ. Reagan **audio** rights are used; separately
restricted WHCA video is not included. Internet Archive is a host, not a blanket
licence for everything on the site.

Per-recording identifiers, download URLs, hashes, reader slugs and durations:
`data/manifest/sources.yaml` and `raw_files.csv`. Release-specific evidence:
`data/release/licences.json`; every audio member maps to its approved source in
`inventory.json`. Unverified/inactive sources, the legacy participant fixture,
application uploads and unconsented voice data are excluded; [blockers](BLOCKERS.md)
name the exact cases. Code and annotation/documentation licence grants are not
invented by this card; formal repository licence files remain an owner decision.

## Counts and duration

The unit is an **indexed recording variant**, not each physical sample-rate copy.
The archived index has **1,103 recordings / 36.26268833333334 hours**:
30 original sources and 1,073 injected variants. Raw full downloads and duplicate
sample-rate files are not counted again. This includes the single clipped source
retained for audit but excluded from generation and evaluation.

| Text | Indexed variants | Indexed hours | Original prepared hours |
|---|---:|---:|---:|
| Gettysburg | 570 | 20.191151666666666 | 0.530258888888889 |
| O Captain | 457 | 11.773672222222222 | 0.3340641666666667 |
| JFK Rice excerpt | 38 | 1.6662786111111112 | 0.04378666666666667 |
| Reagan Challenger | 38 | 2.631585833333333 | 0.06920222222222222 |

These are sums of `duration_s / 3600` from `data/manifest/dataset_index.csv`;
original prepared hours include only `kind=source` rows. Durations describe
prepared excerpts, not full historical source speeches. Each of 29 eligible
originals has 35 single-effect variants (seven types × five severities) and
two three-effect mixed variants. The excluded `o_captain__lv_rg__orig` has no
synthetic derivatives because of clipped source samples.

The release physically contains 2,206 audio members: 30 raw downloads,
30 prepared HQ originals, and both HQ/alignment-rate versions of 1,073 generated
files. Overall payload: 13,812 files; archive size 7,586,867,457 bytes. Inventory
hashes bind all contents, including frozen measurement provenance. This is a
frozen experimental release, not a large independent-speaker benchmark.

## Flaws, severity and labels

| Type | Controlled edit | Severity 1 → 5 parameter |
|---|---|---|
| rushing | Pitch-preserving rubberband time stretch | speed 1.15, 1.30, 1.50, 1.75, 2.00 |
| dragging | Pitch-preserving rubberband time stretch | speed 0.87, 0.77, 0.67, 0.58, 0.50 |
| monotone | PSOLA pitch-range compression | retained range 0.70, 0.50, 0.35, 0.20, 0.08 |
| too_quiet | Flat/trailing gain envelope | −3, −6, −9, −12, −18 dB |
| awkward_pause | Phrase-internal room-tone insertion | 0.6, 1.0, 1.5, 2.2, 3.0 seconds |
| missing_pause | Shorten an existing gap | retained fraction 0.70, 0.50, 0.30, 0.15, 0 |
| mumbling | Zero-phase low-pass plus gain reduction | cutoff 3500, 2800, 2200, 1700, 1300 Hz; gain −1 dB per severity |

Parameters, seed, placement constraints and crossfades are in `configs/flaws.yaml`.
Severity is an **edit-strength level**, not a human-rated severity category.
Single effects cover each severity equally per eligible source. Counting mixed
files by their maximum severity, the synthetic row counts are: level 1: 203;
2: 204; 3: 212; 4: 221; 5: 233. This is not a count of individual flaw instances.

Labels are generated from actual edit placement and piecewise-linear time maps,
expressed in the **flawed** timeline: type, severity, start/end seconds,
inclusive word indices and edit parameters. Oracle alignments are transported
for label construction/QA only. Detectors consume separately produced **real
MFA alignments** and features, not oracle boundaries. Edit labels tell us where
an operation occurred; audible/perceptual boundaries and acoustic spillover are
not guaranteed to coincide exactly.

Original transcripts are canonical-to-as-spoken variants with acoustic-model
verification and explicit unresolved word masks. Written numbers are expanded
with mappings retained. Automatic verification is not human listening. Masked
words and dependent uncertain evidence are excluded from reference statistics
and evaluation; see [transcript audit](../reports/day01_acoustic_verification.md).

## Frozen speaker splits

| Split | Speakers / rows | Speaker slugs |
|---|---:|---|
| Train | 18 / 684 | Gettysburg: lv_amb, lv_dj, lv_dl, lv_eep, lv_fb, lv_jn, lv_law, lv_lb, lv_mas, lv_mk; O Captain: lv_apc, lv_chip, lv_foxits, lv_jtm, lv_mac, lv_mb, lv_md, lv_mrg |
| Dev | 4 / 152 | lv_pc, lv_rk, lv_s, lv_sjs |
| Test | 7 / 266 | lv_sa, lv_tg, lv_wt, lv_ss, lv_th, jfk, reagan |
| Excluded | 1 / 1 | lv_rg (source clipping) |

`configs/splits.yaml` is authoritative. All derivatives remain with their source
speaker. Mode A populations and pooled spreads, and Mode C norms, use clean
train sources only. Thresholds/severity bins were selected on dev only; the test
evaluation is frozen. Mode B's JFK/Reagan test pairs deliberately use their own
original as a within-speaker rehearsal reference; this is not a train population
or use of test speakers for calibration. The published Mode C comparison uses
different sentence/type matching and eligibility from Phase6; do not combine
their aggregate metrics as if they were a single identical benchmark.
The [Mode C results](../reports/phase08_mode_c.md) specify supported-type
eligibility and sentence-level matching for that paired comparison.

## Formats and layout

- Immutable original MP3 downloads: `data/raw/`, SHA-256 in raw manifest.
- Prepared HQ sources: mono PCM16 WAV at 44.1 kHz; no gain normalisation.
- Synthetic audio: lossless mono PCM16 FLAC at 44.1 kHz and 16 kHz.
- Alignment: `alignment/v1` JSON and TextGrid; seconds, inclusive final word index,
  real aligner/model versions, warnings and uncertain-word masks.
- Labels: `labels/v1` JSON, source `synthetic`, seconds rounded to milliseconds.
- Features: frame/word/window/sentence Parquet plus speaker-statistics JSON.
- Time maps: `data/flawed/timemaps/`; oracle alignments: `data/alignment/oracle/`;
  frozen producer/config/measurement
  audits under `data/review/` and `data/.cache/dataset/` as included by inventory.

The release includes HQ originals needed by frozen numerical reproduction; it
does not promise every historical intermediate or raw-to-ASR rerun. Additional
16 kHz source WAVs can be regenerated for alignment from licensed originals.

## Human data and rating pack

**No genuine user takes are included.** `data/human/CONSENT.md` and the requested
WAVs are absent. The synthetic workflow-verification JSON is engineering evidence,
not a human recording or human result. This excludes new user takes, not the
licensed volunteer/historical human speech
that constitutes the original source corpus. Future analysis requires explicit consent,
as-spoken transcripts and intended notes; [human workflow](HUMAN_TAKES.md).
Even after consent, a new human release requires explicit packaging/provenance;
the frozen archive does not silently grow.

The [blind rating pack](RATING_PACK.md) is a separately reproducible convenience
sample of licensed train-source excerpts. It is not counted again as independent
dataset recordings. Actual independent ratings remain pending; no synthetic
rating substitutes or human-agreement claim are supplied.

## Known limitations and intended use

- Synthetic operations approximate delivery problems; their strength/label timing
  is not independently validated perception. Flaws in genuine speech co-vary.
- LibriVox reading style is not an ideal-oratory standard. Few texts, historical
  microphones and selected speakers limit generalisation; English-only features
  and syllable lookup are not accent-fairness evidence.
- Visual word reference was annotated by Claude without listening. The human
  spot-check is pending, and model independence was asserted, not independently
  established. Small unclear-word-excluded samples cannot support exact word-onset
  truth; [alignment bake-off](../reports/day01_aligner_bakeoff.md).
- Pitch/loudness normalisation reduces voice/microphone offsets but cannot remove
  all speaker/domain differences. Clarity is a spectral proxy, not intelligibility.
- The dev clean-alarm guard failed; low precision and non-monotonic score series
  are disclosed in [Phase6](../reports/phase06_results.md) and
  [Phase7](../reports/phase07_validation.md). No threshold was changed afterwards.
- Mode C is a weaker sentence-norm prototype; unsupported flaw types and key-moment
  heuristics are explicitly labelled. Rubric scores are designed penalties, not
  validated perceptual ratings or causal proof.
- Reproduction demonstrates frozen numerical/byte identity in the tested pinned
  CPU environment, not universal bit identity on every platform/model release.
