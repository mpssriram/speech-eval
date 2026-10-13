# Speech-Eval submission — 2026-10-13

Author: **Sriram MPS, IIT Mandi**. Assistance: Claude (Anthropic), Codex (OpenAI).
Track C: Contrastive Speech Analytics & Temporal Flaw Grounding.

| Submission asset | Location / status |
|---|---|
| Repository | https://github.com/mpssriram/speech-eval — make public after the history audit is reviewed |
| Precomputed demo | https://huggingface.co/spaces/SriramMPS/Speech-Evalutaion — anonymously verified, stored v1 results and playback; uploads disabled |
| Video URL | **PENDING — insert the published 3–10 minute demo video link before submission** |
| Final report PDF | **`docs/report/speech-eval-report.pdf` — PENDING: insert the final PDF Claude provides** |
| Current report for reference | [docs/report/report.pdf](report/report.pdf), with [source](report/report.md); preserved unchanged by this packaging task |

## Dataset downloads

| Archive | Exact bytes | SHA256 | Drive link |
|---|---:|---|---|
| speech-eval-dataset-v1.zip | 7,586,867,457 | `a41a18482a72107e449d9562d106a94193f90b8a4e11718bdbfdf746e374a23b` | [Main dataset](https://drive.google.com/file/d/1rDbbPMKORv0nnQ-QnmbrQXIg1mqktvTm/view) |
| speech-eval-human-takes-v1.zip | 62,520,905 | `33e8e0e80a562dfc40e828f6ef1d9ff5285cf24ae543b5dbb7b6ff31377658bd` | [Human takes](https://drive.google.com/file/d/1mKosHQuSM9WXM-x6HUyDOZRhACzDwIgP/view?usp=drive_link) |

The main archive was downloaded fully and verified anonymously on 2026-10-12.
The human archive is an owner-confirmed exact upload; remote re-download/check
was waived by the owner. Every future fetch still verifies the pinned size,
SHA256 and payload inventory. The main archive is immutable and separate from
the optional genuine-takes archive. Source-level US public-domain evidence,
CC BY 4.0 genuine-take consent and release scope are in [DATASET.md](DATASET.md).

## How to run

Requires Git, Make, Docker Engine/Desktop and Compose. Runtime Python, Node and
MFA/model dependencies are packaged in Docker. Use two terminals for the server:

```sh
git clone https://github.com/mpssriram/speech-eval.git
cd speech-eval
make reproduce-quick   # download main archive from Drive, verify, then CPU quick check
make up                # foreground server; http://localhost:8080
# In another terminal, from the same checkout:
make reproduce         # frozen Phase 6/7/8 numerical reproduction, CPU
make test              # complete Python suite inside Docker
```

If Drive imposes a quota or confirmation page, download the main ZIP in a browser
and supply it read-only through the Make wrapper:

```sh
make reproduce-quick DATA_ARCHIVE=/absolute/path/speech-eval-dataset-v1.zip
make reproduce DATA_ARCHIVE=/absolute/path/speech-eval-dataset-v1.zip
# Equivalent importer when host Python dependencies are installed:
uv run python scripts/fetch_data.py --from-local /absolute/path/speech-eval-dataset-v1.zip
```

This preserves all size/SHA256/member checks. [DOCKER.md](DOCKER.md) contains direct
Compose equivalents. The Space is a precomputed demo; it never analyses uploads.

## Verification and disk

- Complete host Python suite: **314 passed** in the verified pre-packaging run.
  The final fresh-clone Drive quick check passed in **2,214.006 s** total
  (**18.913 s** numerical computation). Docker verified **313 + 1** cases
  across the full pre-import suite and the one optional post-import regression.
  Timings are recorded in
  [reports/reproducibility.md](../reports/reproducibility.md).
- Static demo: **2 Node tests**, **3 production Playwright tests** locally and
  **3 on the public Space**; all 19 views play. **38/38** hosted JSON files match
  original stored bytes. [Deployment checks](../reports/deploy_check.md).
- Frozen reproduction: prior fresh-clone quick/full Docker runs matched **563/563**
  scientific output hashes. Those historical runs remain in reproducibility.md;
  the final fresh-clone quick run also matched its pinned scientific JSON exactly.
- Measured retained reproduction footprint: **32,170,019,620 bytes**
  (**32.170019620 decimal GB / 29.961 GiB**): tools/API image **16,804,236,803**,
  main ZIP **7,586,867,457**, unpacked payload **7,778,915,360**. This excludes web
  image, build cache, staging/scratch, optional human takes and unrelated tools.
  Allow additional space for download/extraction staging and image builds;
  clean-install peak/minimum is **unmeasured**, so this is not a complete minimum
  disk requirement. [Measurement](../reports/reproduction_disk_usage.json).

## Disclosed limitations

- **No independent ratings**; no human correlation/agreement claim. AI or recorder
  self-ratings are not independent rater data.
- **No human alignment spot-check**. Claude placed visual boundaries without
  listening; automatic checks are not human listening or annotation review.
- **Low precision** and a failed dev clean-alarm guard. Frozen v1 A-LOSO precision
  is **0.125**; B-same-speaker precision is **0.018**. Successful demo examples are
  selected illustrations, not evidence of broad reliability.
- Labels and as-spoken words on genuine takes are **recorder-confirmed**, not
  independently annotated. Spontaneous take04s are excluded from scored human
  A/B comparisons and displayed descriptively, including their Mode C views.
- Synthetic edits approximate flaws; rubric penalties are not a validated
  perceptual scale. English-only proxies do not establish accent fairness;
  Mode C is heuristic and has no invented same-text baseline.
- Code/configuration, thresholds, scores and published scientific results remain
  frozen. Current report source and PDF were not edited or rebuilt by this task.

Before submission: supply video/final PDF, resolve any history-audit findings,
make the repository public, check all links in a private/logged-out window,
and submit. [Owner actions](../NEXT.md), [history audit](../reports/history_audit.md).
