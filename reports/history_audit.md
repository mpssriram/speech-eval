# Full Git history audit — 2026-10-13

**Status: STOPPED / not cleared for making the repository public.**
The user was notified that historical private workstation paths and excluded
legacy-upload metadata remain. No history rewriting, deletion, filter-repo,
force push or detector/report edit was performed. Items 12–14 may continue;
publication requires the owner's review and decision about these findings.

## Scope and method

Audited HEAD `7611bb97f9c623f700a5f11efc5eae9ac3afaf8d` and all reachable refs: refs/heads/main, refs/remotes/origin/main.
`git rev-list --objects --all` and `git log --all --name-only --no-renames` cover
**85 commits**, **8729 objects**, **8006 unique blobs**,
**7779 historical paths**, **208,021,043 raw blob bytes**.
This includes removed and modified historical files, not only HEAD.
Every reachable blob was read with `git cat-file --batch`; no match value was
printed. Candidate secrets would be reported only by kind, blob/path/line and
one-way fingerprint. Script: `scripts/audit_history.py`.

Checks include OpenAI/Hugging Face/GitHub/AWS/Google/Slack token patterns, private
keys, non-placeholder credential literals, historical `.env` names, the private
Linux/Windows user paths specified by the task, excluded legacy upload identity,
audio/video extensions and blob sizes. Pattern scanning is a heuristic audit,
not proof that arbitrary secrets cannot exist; compressed PDF/image/embedded
payloads are not exhaustively decoded or OCRed. The item stops on the findings
below rather than claiming a complete clearance.

## Findings

| Check | Finding |
|---|---|
| Recognisable API keys/tokens/private keys | **0 candidates detected** by the listed raw-byte patterns |
| Historical `.env` / `.env.*` files | **0 paths** |
| Private absolute workstation paths | **108 unique historical blobs**, across **51 paths** — owner review required |
| Excluded legacy upload identifier | **25 historical blobs**, across **9 paths** — metadata and generated artefacts retained |
| Audio/video files | **14 unique blobs**, all newly authorised `deploy/hf-static/public/audio/*.mp3` playback files; no historical legacy WAV/MP3 payload detected |
| Blobs over 10 MiB / 100 MiB | **0 / 0**; largest blob **3,986,956 bytes** |
| Release ZIPs / raw recordings | No tracked release ZIP/raw-audio payload in the reachable history |

Private paths appear in historical dataset shard provenance and human ASR drafts,
as well as scripts, scientific sources and documentation. Some paths in the
Dockerfile, MFA model identity and tests are intentional compatibility paths.
These are still disclosed here, rather than silently exempted or altered:
changing frozen producer paths would violate the packaging task's constraints.
Examples: `data/human/asr_drafts/gettysburg__user__take01.json`,
`data/manifest/dataset_shards/gettysburg__lv_dj__orig.json`,
`src/speecheval/align/mfa.py`, `docker/mfa_models.sha256`, `README.md`, `Dockerfile`.
Full blob IDs and paths are in `reports/history_audit_evidence.json`.

The excluded fixture is `gettysburg__user__input_246ca9e90194`. Its alignment and
analysis artefacts remain reachable, even though its unverified audio is absent
from Git and the licensed release. Some mentions intentionally document its
exclusion. Historical paths containing the identifier:

- `data/alignment/gettysburg__user__input_246ca9e90194.TextGrid`
- `data/alignment/gettysburg__user__input_246ca9e90194.json`
- `data/analyses/b6f935a82ff5.json`
- `data/review/detector_v2_test.json`
- `data/review/final_evaluation.json`
- `docs/BLOCKERS.md`
- `reports/reproducibility.md`
- `src/speecheval/reproduce.py`
- `tests/test_dataset_release.py`

No additional unlicensed audio payload was found. The 14 current demo MP3s have
source hashes in `deploy/hf-static/AUDIO_SOURCES.js`, source-level public-domain
evidence for institutional/LibriVox originals, and CC BY 4.0 consent for genuine
user takes. Synthetic derivatives use the same licensed source recordings.
This does not convert the excluded fixture's unknown licence into a grant.
Code has MIT and the owner's docs/labels/takes have CC BY 4.0; source audio keeps
its source-specific US public-domain status. This is an engineering inventory,
not independent legal review of every historical paragraph or screenshot.

## Owner decision before public visibility

Review whether to retain disclosed compatibility/provenance paths and legacy
exclusion evidence, or authorise a carefully scoped history-cleanup plan.
Do not make the repo public until this review is resolved. No rewrite is
currently authorised, and the audit does not recommend touching scientific
values or overwriting frozen datasets.

```sh
python3 scripts/audit_history.py
```

The pinned audit snapshot precedes its own audit-report commit and subsequent
packaging documentation. Re-running scans those later commits too; counts will
naturally increase when findings are quoted in the audit evidence.
