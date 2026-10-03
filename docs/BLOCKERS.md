# Blockers

## 2026-10-03 — JFK Rice audio download

- Expected file: `data/raw/jfk_rice_1962.mp3`
- Source page: <https://www.jfklibrary.org/asset-viewer/archives/jfkwha-127-002>
- Tried `curl` with default and browser user agents; both received HTTP 403 / a Cloudflare verification page.
- Tried the source page in a real browser; it remained at Cloudflare's "Performing security verification" screen. Automated CAPTCHA or security-challenge bypass was not attempted.
- Action needed: download the public-domain MP3 manually from the source page and save it at the expected path.

## 2026-10-03 — O Captain collection count differs from spec

- The Internet Archive item `o_captain_librivox` currently exposes 13 distinct VBR MP3 readings, while the Day 1 spec says 12.
- No licensed reading was silently discarded; all 13 are retained. This makes the expected total 30 recordings when the two government files are present (currently 29 because JFK is blocked).
