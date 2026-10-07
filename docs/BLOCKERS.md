# Blockers

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
