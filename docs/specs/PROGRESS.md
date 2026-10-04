# Spec progress

## 2026-10-04 — Phase 1, paused at USER Step 5b

- Steps 1–5a are implemented: 30 licensed sources (15 Gettysburg, 13 O Captain, JFK and Reagan), canonical transcripts, frozen ASR, prepared mono PCM16 WAVs at 44.1 kHz and 16 kHz, and editable as-spoken drafts. JFK is resolved and its sentence-bounded excerpt is 157.632 seconds long.
- Pre-review triage fetches all five Gettysburg manuscripts from Abraham Lincoln Online and freezes their text with source URLs. Bliss remains selected for each of the 15 readers: no alternative meets the required improvement of at least three token edits. Every reader's five distances and applied version are in `data/manifest/transcript_versions.yaml`.
- Configured spelling, apostrophe, number and compound equivalences classify 78 edit groups as IGNORE; phonetic/string similarity classifies 14 as LIKELY_ASR. Independent WhisperX medium.en CPU ASR, beam 5, transcribed 85 LISTEN clips. Exact normalized context agreement promotes 32 to LIKELY_REAL; 53 remain LISTEN. All 85 remain in the human listen list. There are 177 groups after fixing numeric tokenization, compared with the original 178.
- The full audit, frozen independent-ASR evidence, listen list and static local review page are committed. Existing `# reviewed: yes` transcripts are preserved. No recording is automatically marked reviewed.
- Added Makefile and executable test wrapper, both removing inherited PYTHONPATH and disabling external pytest plugin autoload. Documented commands use the same isolation. CLI warns about non-empty PYTHONPATH. The O Captain split spec now allocates all readers remaining after dev/test to train (nine with 13 eligible readers).
- Verification: 36 tests pass, including a ROS-style inherited PYTHONPATH run, reviewed-file preservation, cache reuse, manuscript threshold, equivalences, single-row Markdown formatting for poem excerpts and safe relative audio links. Repeated triage reused all 85 secondary-ASR results and preserved identical hashes for the drafts, five manuscript files, reports, manifest and review artefacts. Only the public-domain speech texts are retained from the source page.

Reproduce in WSL:

```bash
cd /home/sriram/speech-eval
env -u PYTHONPATH ~/.local/bin/uv run speecheval transcripts triage
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 env -u PYTHONPATH ~/.local/bin/uv run pytest
make test
```

USER Step 5b is next: open `\\wsl$\Ubuntu\home\sriram\speech-eval\data\review\index.html` manually, listen to the 85 items, record decisions in `reports/day01_listen_list.md`, edit as-spoken transcripts only for actual speech differences, and add `# reviewed: yes` after each recording is reviewed. The browser tool cannot open file-protocol URLs; this is logged in `docs/BLOCKERS.md`. Steps 5c onward remain pending.
