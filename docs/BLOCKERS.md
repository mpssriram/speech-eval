# Blockers

## 2026-10-11 — V2 fresh-clone Docker rerun and image-size measurement

Docker Desktop startup failed before the Linux engine started. Backend log:
`initializing Inference manager ... Docker/run/dockerInference: The file cannot
be accessed by the system`. The endpoint is a zero-length reparse-point socket;
a recoverable rename also failed with the same access error. No factory reset,
Docker data deletion, settings rewrite or image pruning was attempted.
Both WSL `docker version` and Windows `docker.exe version` confirm no usable
daemon; `docker desktop start` did not restore it. The exact one-shot v2 result
is safely committed; a frozen reproduction will not consume another test decision.
Fresh GitHub clone path: `/tmp/speech-eval-v2-3AIBAv/clone`. Restore Docker Desktop
before rerunning `make reproduce-v2 DATA_ARCHIVE=/absolute/path/to/the/zip` there.
Live project-image/cache sizes and the complete Docker-inclusive installation
requirement cannot be measured while the daemon is unavailable; do not estimate.

## 2026-10-11 — Inherited Mode B progress limitation

V1 and v2 inference compute Mode B progress via Mode A summaries of both takes.
For a custom text without a same-text train/expert reference, this fails with
`No eligible reference readers`, even though a previous-take comparison exists.
The requested Gettysburg/Reagan takes have references. The frozen test evaluator
does not invoke this wrapper. Retained and disclosed rather than changing the
DEV-selected detector source/provenance; no claim of generic-text Mode B support.

## 2026-10-10 — Release exclusions and publication

- Legacy participant fixture `gettysburg__user__input_246ca9e90194` appears in the old input freeze but has no verified source licence or consent. Its audio, transcript, alignment and features stay out of the public archive. It is not an indexed dataset row or an input consumed by numeric reproduction. No private application uploads or human takes are packaged.
- Inactive `jfk_inaugural_1961` and unspecified `harris_vp_tbd` lack recording-specific verified rights evidence and are excluded. Eleanor Roosevelt and Obama entries are inactive and outside the measured release; neither is packaged.
- Archive hosting/upload remains a user action. The URL is intentionally `UPLOAD_URL_PENDING`; local import must work without publishing or creating an account.

## 2026-10-10 — Item 4: genuine user recordings are not available yet

- Fresh read-only inspection of `/home/sriram/speech-eval/data/human/raw/` found no files: no `{text_id}__user__takeNN.wav` and no `notes.md`. Neither `data/human/CONSENT.md` nor a consent file under `raw/` exists.
- The user is recording later. Human-take analysis, intended-flaw/slip checks, annotation and independent human agreement cannot proceed without the actual recordings, notes and consent. Licensed browser/runtime fixtures are explicitly not substitutes for user takes.
- The instruction truncation is resolved: full item B and `codex_tasks_C_D_E.md` are now available. Actual recordings, notes and consent remain pending; no recording, label, consent or rating was fabricated.

## 2026-10-07 — Docker and Linux Node are unavailable in the current WSL session

- `docker --version` returned the WSL integration message: Docker command could not be found in this distro. No Docker reinstall or system changes were attempted.
- `command -v node` found no Linux Node executable; the only `npm` path is the Windows installation under `/mnt/c/Program Files/nodejs/`. Do not run project builds on Windows.
- API source and project-only Python dependencies can proceed; Docker equivalence and the React build require the existing Docker integration/Linux build runtime to be available. Do not claim those checks pass.
- Release resolution on 2026-10-10: Docker Desktop WSL integration is available (Engine 29.1.3, Compose 2.40.3-desktop.1). A separate temporary clone built the dashboard with Linux Node inside its pinned image, served the real API/UI on port 8080, passed 200 container tests and three browser tests, and reproduced all Phase 6/7/8 report numbers and ten host/container analysis hashes. Host Linux Node is still absent but is not required by this flow. Evidence: `reports/docker_verification.json`.

## 2026-10-10 — Public dataset archive and raw reconstruction are still pending

- Git intentionally excludes audio and Parquet. No published dataset archive URL/checksum exists in the project; an external clone cannot download an unpublished release.
- Fresh-clone Docker verification used `scripts/restore_local_data.py` to copy only the frozen measured inputs/provenance from the prepared local checkout. It copied no host environment, ASR models or application state.
- `make reproduce-quick` and `make reproduce` successfully recompute the frozen numeric evaluation from these measurements. They do not claim full raw download/ASR/excerpt-window reconstruction. That separate Phase 10 release flow still needs a published licensed archive with checksums and its raw-regeneration work; no new hosting account or personal-data publication was attempted.
- Release resolution: a licensed checksum-pinned archive is now built under `data/release/`; Docker fetch/import runs before both reproduction targets. `reports/reproducibility.md` records the new GitHub-clone verification. Only hosting and filling its URL remain pending; this release intentionally reproduces frozen measurements rather than historical raw ASR/manual excerpt decisions.

## 2026-10-07 — User takes are not present in the WSL project

- Read-only inspection of `data/human/raw/` found no files, including no `notes.md` or `CONSENT.md`.
- User reports the takes exist. Requested their actual location; do not fabricate recordings, labels, or consent. Synthetic calibration/evaluation can continue independently.
- Resolved location ambiguity: the user subsequently confirmed the takes have not been recorded yet. Actual human audio, notes, labels and consent are still pending.

## 2026-10-04 — Repeated O Captain ending selected too early (resolved)

- Acoustic-verification preflight found 12 prepared clips ending after the first stanza. The original matcher chose the first highest-scoring instance of the repeated last six words.
- The ending matcher now chooses the last occurrence on a score tie. Full-source ASR was reused to repair the 12 cuts and regenerate both prepared WAV rates; all raw audio remains unchanged.
- Original listen-list items are frozen in `data/review/verification_input.json`. Apparent missing stanzas are scored against the corrected full poem audio, not treated as evidence for deleting transcript text.

## 2026-10-03 — JFK Rice audio download (resolved)

- Expected file: `data/raw/jfk_rice_1962.mp3`
- Source page: <https://www.jfklibrary.org/asset-viewer/archives/jfkwha-127-002>
- Tried `curl` with default and browser user agents; both received HTTP 403 / a Cloudflare verification page.
- Tried the source page in a real browser; it remained at Cloudflare's "Performing security verification" screen. Automated CAPTCHA or security-challenge bypass was not attempted.
- Resolved: the user supplied `JFKWHA-127-002-AU_WR.mp3`; it was copied to the expected WSL path and validated with `ffprobe` (44.1 kHz mono, 1068.513 seconds).

## 2026-10-03 — O Captain collection count differs from spec

- The Internet Archive item `o_captain_librivox` currently exposes 13 distinct VBR MP3 readings, while the Day 1 spec says 12.
- No licensed reading was silently discarded; all 13 are retained. There are now 30 recordings, including both government files; JFK is resolved.

## 2026-10-04 — Automated opening of local review page

- `data/review/index.html` is generated and references the prepared WAVs with relative paths.
- The browser tool rejected its `file://wsl.localhost/Ubuntu/home/sriram/speech-eval/data/review/index.html` URL because the tool permits only HTTP/HTTPS protocols.
- Open `\\wsl$\Ubuntu\home\sriram\speech-eval\data\review\index.html` manually in a browser. No server or protocol workaround was used.

## Item B — genuine take analysis inputs

- No requested WAVs, notes.md or consent have been supplied in data/human/.
## Item C — independent rating responses

The blind pack and agreement script are available, but no actual independent
rater responses exist. Collect separate CSVs from real raters; blank forms and
temporary unit-test ratings cannot establish system–human or inter-rater agreement.
## Item E — publication and unsupported draft claims

README/report/video drafts were read successfully from the supplied Windows
folder. Measured numbers have been copied only from result Markdown reports.
Actual takes/ratings, human alignment spot-check, publication author, archive URL,
video URL, disk requirement and exact numeric explanation examples remain pending;
all unresolved draft fields are in docs/TODO_PLACEHOLDERS.md. The proposed MIT
code / CC BY 4.0 annotation grants lack formal owner licence files. No grants,
human-performance claims, pitch progress or rater confidence intervals were invented.
