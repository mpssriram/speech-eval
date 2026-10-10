# Licensed dataset release and numerical reproduction

Date: 2026-10-10. All test-set reruns here are **reproductions**, not tuning,
recalibration or a second model-selection evaluation. Detector, scoring and
reference code/configuration remain frozen. No human audio or ratings are invented.

## Archive

Archive: `data/release/speech-eval-dataset-v1.zip` (not committed to Git).
Two Linux Python 3.11 builds, including a rebuild after importer/builder review,
produce byte-identical archives:

```text
a41a18482a72107e449d9562d106a94193f90b8a4e11718bdbfdf746e374a23b  speech-eval-dataset-v1.zip
a41a18482a72107e449d9562d106a94193f90b8a4e11718bdbfdf746e374a23b  speech-eval-dataset-v1-repeat.zip
```

| Measurement | Value |
|---|---:|
| Archive bytes | 7,586,867,457 |
| Uncompressed payload bytes | 7,778,915,360 |
| Payload files, each SHA-256 pinned | 13,812 |
| Audio payloads including original/derived formats | 2,206 |
| Indexed recordings (counting each variant once) | 1,103 |
| Indexed hours (not counting duplicate rates/raw downloads) | 36.26268833333334 |
| Original recordings | 30 |
| Injected recordings | 1,073 |
| Gettysburg original readers | 15 |
| O Captain original readers | 13 |
| JFK originals | 1 |
| Reagan originals | 1 |
| Train speakers / rows | 18 / 684 |
| Dev speakers / rows | 4 / 152 |
| Test speakers / rows | 7 / 266 |
| Excluded speakers / rows | 1 / 1 |

Counts/durations come from the archived `data/manifest/dataset_index.csv`, not
physical duplicate audio file counts. Per-file sizes, hashes and audio source
associations are in committed `data/release/inventory.json` and the ZIP's matching
`release_manifest.json`. Original raw hashes are independently checked against
`data/manifest/raw_files.csv` before packaging.

## Rights and exclusions

The [LibriVox rights statement](https://librivox.org/pages/public-domain/)
establishes US public-domain status of its volunteer recordings. The
[JFK item](https://www.jfklibrary.org/asset-viewer/archives/jfkwha-127-002)
lists Public Domain copyright status. Reagan's tape PP6028B is in the
[presidential audio inventory](https://www.reaganlibrary.gov/archives/whca-presidential-audio-collection-1981-89);
the [WHCA collection rights page](https://www.reaganlibrary.gov/archives/audiovisual/white-house-communications-agency)
identifies its audiotape collection as public domain. The separate video rights
statement is not used. Evidence was read automatically, not claimed as a human
legal review; rights outside the USA may differ.

The legacy unverified participant fixture `gettysburg__user__input_246ca9e90194`
and its metadata are excluded, although the historical freeze enumerated them.
It is not an indexed dataset row or consumed by these numerical reproductions.
Inactive/unverified sources, application uploads and unconsented human takes are
excluded. Full exclusions and pending publication are in `docs/BLOCKERS.md`.

## Import and verification

`scripts/fetch_data.py` uses only the Python standard library inside Docker. It
supports `--from-local`, otherwise downloads the checksum-pinned URL in
`configs/dataset.yaml`. The URL is intentionally `UPLOAD_URL_PENDING` until the
user uploads this exact archive. An installed dataset is rehashed before reuse.
The importer rejects corrupt outer/inner hashes, unexpected/duplicate/unsafe
members, symlinks and differing existing files. It verifies the whole payload
before installation and publishes files atomically without overwrite; a killed
import can be retried. Raw files are not modified.

The final source checkpoint passed 219 Python tests, including an actual SIGKILL/retry
regression and a local HTTP download test. No host Python packages or model
caches are needed by the Docker reproduction commands.

## Fresh GitHub clone

Verification in `/tmp/speech-eval-github-Ly6MDl`, cloned directly from
`https://github.com/mpssriram/speech-eval.git` and fast-forwarded from the first
checkpoint `44e5755` to the tested release harness `f35585a`.
Only the release ZIP is mounted read-only from the development checkout; no
restoration script, source cache or host environment is copied. Commands:

```sh
make reproduce-quick DATA_ARCHIVE=/absolute/path/speech-eval-dataset-v1.zip
make reproduce
# Then repeat both commands with the installed, reverified dataset.
make reproduce-quick
make reproduce
```

Initial import verified all 13,812 files and installed 7,730 missing files;
existing identical tracked metadata was preserved. A first full attempt stopped
at the historical Phase 7 input gate: it included the unverified legacy fixture.
The release-only harness now explicitly exempts that exact fixture's paths and
verifies every other historical input, original audit SHA, detector implementation,
rubric and scorer/validator source SHA. It temporarily supplies this narrow
validation gate to the unchanged Mode C evaluator, then restores the original
gate even on failure. No omitted bytes are invented or claimed verified. This is
a post-hoc release-bookkeeping adapter, **not** a detector/threshold change.

The final clone's container suite passed all 219 tests. First completed scientific
run: quick 11.829 seconds / 114 rows; full 225.204 seconds / 266 rows. The initial
post-import quick attempt also passed (20.113 seconds). The full run reproduced
all 284 numeric literals in the original Phase 6/7/8 reports, seven cold CPU
source feature bundles and the ten published two-run host/container analyses.
It evaluated the same 175 eligible Mode C files without changing eligibility.

Both completed runs printed `REPRODUCED OK`; all 563 scientific outputs matched
SHA-256 byte-for-byte: five regenerated report/metric files and 558 analysis JSONs.
The sorted analysis hash manifest has SHA-256
`c7f31377a48ad71595c5dda4ca985b5076688a740205322f35c3931f665e8fb3`.
Every individual analysis hash is preserved in
`data/release/reproduction_hashes.json`. The two run times:

| Reproduction | Run 1 seconds | Run 2 seconds | Rows |
|---|---:|---:|---:|
| Quick, one text and three test readers | 11.829 | 11.954 | 114 |
| Full published Phase 6/7/8 numbers | 225.204 | 223.142 | 266 |

Stable output hashes, identical in both runs:

```text
ea1f85f862117810fd1d84d0e6c4a23012d8dbf94e9cbe635c736408a274fcaa  quick.json
e11412e9c0a6ccae4b0e4a556ed3d857bb73e61441bf0ae22733d3223ca95749  full.json
8d2abac937904461bf7ed1dddf26a31d0d45568f06d3eff1a5cb6fccd6003b2f  phase06_results.md
7a9c891ead95f3ab63a1fbdec796efd7900946cbfe5e53e0dab1e24a0771fd0c  phase07_validation.md
9c491b9a1958519a3579ef50761e617a7338606c77e9652c1e76ac7dc712b397  phase08_mode_c.md
```

Runtime/elapsed-time files are deliberately not byte-identity targets. First
image/model download/build and archive import are separate from these numerical
run times; the post-import CPU quick computation is comfortably below 15 minutes.

This reproduces published Phase 6/7/8 numerical results from frozen measurements,
including cold CPU source feature extraction. It does not claim to rerun the
historical full-source ASR/manual excerpt decisions or to establish human
agreement. Public upload and genuine human input remain separate user actions.
