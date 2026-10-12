# Submission checklist — 2026-10-12

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

## Checks

- [x] Release download metadata, exact byte sizes and SHA256 pins published.
- [x] Main Drive transport checked anonymously (partial); full local archive/payload verification.
- [ ] Upload the correct separate human takes ZIP and verify its replacement link.
- [ ] Verify both browser links from a logged-out browser at submission time.
- [ ] Confirm repository is public at submission time.
- [ ] Record/publish a 3–10 minute video and supply its working link.
- [ ] Regenerate final PDF (at most six pages) after all metadata updates.
- [x] Author Sriram MPS, IIT Mandi, with assistance from Claude (Anthropic) and Codex (OpenAI); MIT code and CC BY 4.0 data/docs/recordings; consent retained.

Prior fresh-clone CPU Docker quick/full reproduction and repeated 563 scientific
hash checks are recorded in `reports/reproducibility.md`; the published numbers
are frozen, not retuned for release. Remaining human agreement and alignment
spot-check limitations are explicit in NEXT.md and the report.
