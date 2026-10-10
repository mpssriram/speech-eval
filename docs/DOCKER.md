# CPU dashboard and numerical reproduction

Run from a Linux/WSL checkout with Docker Desktop's WSL integration enabled:

```sh
docker compose up --build
# dashboard + same-origin API: http://localhost:8080
```

`make up` is the same command. `make down` stops this stack without deleting data.
Only the dashboard proxy is published, bound to localhost. Nginx serves client-side
`/results/<id>` routes and forwards API/audio range requests to FastAPI. Startup
waits for API health. The image includes ffmpeg, Rubber Band, SoX, Python 3.11,
the locked Python dependencies, and MFA 3.4.2 with its three English models.
MFA's existing runtime paths are preserved inside the image, not assumed to exist
on the host. CUDA is hidden; the pinned CUDA-capable Torch build runs on CPU.
Models are downloaded from the official pinned [acoustic v3.1.0](https://github.com/MontrealCorpusTools/mfa-models/releases/tag/acoustic-english_mfa-v3.1.0),
[US dictionary v3.1.0](https://github.com/MontrealCorpusTools/mfa-models/releases/tag/dictionary-english_us_mfa-v3.1.0)
and [US G2P v3.0.0](https://github.com/MontrealCorpusTools/mfa-models/releases/tag/g2p-english_us_mfa-v3.0.0)
assets and checked against `docker/mfa_models.sha256`. Build-time version discovery
does not require GitHub API credentials.

The initial image download/build is substantial and is **not** included in the
15-minute numerical quick-run budget. No corpus audio or personal files are baked
into either image. The API stores jobs/uploads in the mounted `data/` directory.
Known texts use their canonical transcript for new audio in every mode; supplying
an as-read transcript overrides it. Own-speech Mode C requires a pasted transcript.
The API does not require an unused automatic-ASR model cache. Standalone CLI ASR
and end-to-end raw reconstruction are not included in this packaging claim.
An empty clone can serve the dashboard, but actual analysis requires the prepared
reference corpus and measurement provenance.

## Licensed release import

Audio/Parquet and release ZIPs are intentionally ignored by Git. The release URL
in `configs/dataset.yaml` is pending the user's upload. Until then use the built
archive, not the unpublished development checkout:

```sh
make reproduce-quick DATA_ARCHIVE=/absolute/path/speech-eval-dataset-v1.zip
make reproduce DATA_ARCHIVE=/absolute/path/speech-eval-dataset-v1.zip
# Or import only, with no host Python:
mkdir -p reports/reproduced
docker compose run --rm --build --no-deps \
  --volume /absolute/path/speech-eval-dataset-v1.zip:/dataset-release.zip:ro \
  tools python scripts/fetch_data.py --from-local /dataset-release.zip
```

Both reproduction targets run `fetch-data` first. Once all installed files verify,
no download is needed. After publication fill only the URL in dataset.yaml; the
archive SHA and committed inventory pin the content. `--from-local` verifies the
same outer SHA, complete inventory and all payload SHA-256s. Unsafe ZIP paths,
symlinks, duplicates and differing existing files are rejected before installing
anything. Identical existing files (including immutable raw audio) are untouched.

The archive includes licensed raw originals, indexed prepared/synthetic audio,
transcripts, alignments, time maps, labels, feature bundles and frozen reference/
evaluation provenance. It excludes models, environments, application uploads,
unconsented human takes and an unverified legacy participant fixture. Rights and
source associations are in `data/release/licences.json` and `inventory.json`.
The LibriVox public-domain statement applies to the USA, not every jurisdiction.
For maintainers: `python scripts/build_release.py` deterministically rebuilds the
archive from the measured corpus without changing any detector/scoring settings.

## Commands

```sh
make test             # pytest in the CPU image, no real corpus required
make test-host        # existing local uv pytest workflow
make reproduce-quick  # Gettysburg: lv_sa, lv_tg, lv_wt; all their test variants
make reproduce        # every numeric claim in Phase 6, 7 and Mode C reports
```

Both reproduction commands actually run detection and the seeded bootstrap from
measured features. They re-extract held-out source feature bundles from audio on
CPU into scratch and require all five generated files to match their published
SHA-256s. Training inputs for references/pooled scales remain train-only; the quick
test subset is exactly one text and three readers. The quick result must match
the committed measured subset in `reports/reproduction_quick_expected.json` and
finish in less than 900 seconds.

Every tools Make target creates its output directory as the invoking user before
starting Docker. The output bind mount refuses to auto-create a missing host
directory, preventing root-owned artifacts from blocking later reproduction.

The full command recomputes A-LOSO and B-same-speaker metrics/CIs, all five-severity
score series, the DEV alarm guard, and two-run identities for all ten published
reproducibility files. It also reruns the unchanged Mode C evaluator and requires
all its comparison/norm/spread evidence to match. CPU analysis bytes must also
match their committed host hashes. It regenerates the reports and compares **every numeric
literal**, including counts, CI endpoints and the worked scoring example. Missing
inputs or the first differing field/number cause a nonzero exit. Evidence goes to
`reports/reproduced/`; success prints `REPRODUCED OK`.

This is numerical reproduction from the frozen measured dataset, not a claim of
end-to-end raw download/ASR reconstruction. Publication of the built archive still
requires its user-provided URL. Human
agreement remains pending genuine recordings, consent, labels and independent
ratings; there are no human numbers to reproduce yet.

## Verified fresh-clone run

On 2026-10-10, the stack was built and started from a separate temporary Git clone
with locally restored measured inputs, not the development checkout/environment.
The CPU image passed all 200 Python tests. A second empty clone, with no measured
inputs restored, passed 199 tests with one real-corpus integration test skipped;
its output directory belonged to the invoking user (UID/GID 1000), not root.
The Chromium suite passed all three
tests through `http://localhost:8080`, including actual audio playback/seeking,
Modes A/B/C and the isolated fake-device recording lifecycle. The five UI PNGs
were refreshed from the production proxy.

Quick reproduction took 12.779 seconds for 114 variants belonging to the three
Gettysburg test readers. Full reproduction took 239.969 seconds: all Phase 6/7/8
numeric report claims matched, as did all ten published two-run analysis hashes
across host/container and the seven cold CPU source feature bundles. HTTP probes
confirmed the SPA route, four available texts, health and 100-byte `206` audio
range responses. A new licensed 30-word excerpt was CPU-aligned through the API,
separately from the prepared-fixture UI path. This is not a human recording.
That short excerpt alone does not establish full-length latency.
The same licensed excerpt also completed own-speech Mode C with its supplied
transcript in 33.328 seconds, producing six guideline checks and no baseline.

Machine evidence is in `reports/docker_verification.json`. The original Phase 7
report retains its historical pending-Docker statement; the new evidence resolves
that check without editing its frozen inputs. Git metadata is not baked into the
image, so `/api/health` honestly returns `git_commit: null`; the verification
artifact records the tested clone commit and image identities instead.

After the fresh-clone run, the main checkout's production CPU image also analyzed
a new 120.000-second licensed Gettysburg clip (271 supplied as-read words) in
50.568 seconds, including upload and one-second status polling. The initial job
was queued/running, not a reused completed job; its input hash differs from the
prepared source. This meets the Phase 9 two-minute/<60-second target for this one
sample. [Full-length latency evidence](../reports/full_length_latency.json) records
the input hashes, analysis ID, image identity and CPU runtime. It is not a user
recording, human review or a latency guarantee for every recording/machine.
