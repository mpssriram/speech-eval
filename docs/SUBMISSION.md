# Submission checklist — 2026-10-12

**Video URL: PENDING — insert the published 3–10 minute demo video link before submission.**
[Precomputed demo on Hugging Face](https://huggingface.co/spaces/SriramMPS/Speech-Evalutaion). Stored v1 results and audio playback; uploads are disabled.
## Download releases

[Main dataset archive](https://drive.google.com/file/d/1rDbbPMKORv0nnQ-QnmbrQXIg1mqktvTm/view)
was downloaded in full anonymously with gdown 5.2.0 on 2026-10-12 and matches
the local release by exact size and SHA256. The old Drive folder is retired;
an optional replacement folder URL has not been supplied.

| File | Exact bytes | SHA256 | Download |
|---|---:|---|---|
| speech-eval-dataset-v1.zip | 7,586,867,457 | `a41a18482a72107e449d9562d106a94193f90b8a4e11718bdbfdf746e374a23b` | Main link above; Drive ID `1rDbbPMKORv0nnQ-QnmbrQXIg1mqktvTm` |
| speech-eval-human-takes-v1.zip | 62,520,905 | `33e8e0e80a562dfc40e828f6ef1d9ff5285cf24ae543b5dbb7b6ff31377658bd` | [Human takes](https://drive.google.com/file/d/1mKosHQuSM9WXM-x6HUyDOZRhACzDwIgP/view?usp=drive_link); owner-confirmed exact upload |

[Human-takes archive](https://drive.google.com/file/d/1mKosHQuSM9WXM-x6HUyDOZRhACzDwIgP/view?usp=drive_link) is owner-confirmed as the exact prepared ZIP.
Remote re-download/verification was skipped at the owner's request. The size and
SHA256 above pin the expected release; future fetches retain all integrity checks.
The main ZIP is immutable and contains no new human takes. Human takes are a
separate optional release; the scientific corpus and frozen results stay fixed.

```sh
make reproduce-quick   # anonymous Drive download, checksum verification, CPU Docker
make reproduce
# Import the optional consented human takes:
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
# Browser-download fallback for the separate human archive:
uv run python scripts/fetch_data.py --from-local /absolute/path/speech-eval-dataset-v1.zip \
  --with-human-takes --human-from-local /absolute/path/speech-eval-human-takes-v1.zip
```

Drive may impose quotas or a confirmation page. Browser downloads still undergo
the same size/SHA256/member checks; do not replace the pinned hash to accept a
different file. Evidence: `reports/drive_download_probe.json` and
`reports/human_release_verification.json` (local packaging) and
`reports/human_drive_owner_confirmation.json` (publication).

## Checks

- [x] Release download metadata, exact byte sizes and SHA256 pins published.
- [x] New main Drive archive downloaded fully and matched by exact size/SHA256; internal inventory also verified.
- [x] Owner confirmed exact human-takes upload; link published. Remote re-download/check waived by owner.
- [ ] Verify both browser links from a logged-out browser at submission time.
- [ ] Confirm repository is public at submission time.
- [ ] Record/publish a 3–10 minute video and supply its working link.
- [x] Final PDF regenerated: six A4 pages, repeated bytes identical, every page inspected.
- [x] Author Sriram MPS, IIT Mandi, with assistance from Claude (Anthropic) and Codex (OpenAI); MIT code and CC BY 4.0 data/docs/recordings; consent retained.

Prior fresh-clone CPU Docker quick/full reproduction and repeated 563 scientific
hash checks are recorded in `reports/reproducibility.md`; the published numbers
are frozen, not retuned for release. Remaining human agreement and alignment
spot-check limitations are explicit in NEXT.md and the report.

Final verification: 312 host tests passed; frozen code/config/audio/consent and
main ZIP unchanged. Disk snapshot: 32,170,019,620 bytes for retained tools image,
one archive and unpacked payload; clean-build peak remains unmeasured.
Both direct archive links are configured; the old folder is retired.
