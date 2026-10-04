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

## 2026-10-04 — Automatic acoustic verification replaces USER Step 5b

The user superseded the listening-review requirement. The previous entry is historical; no human review is claimed.

- Implemented `speecheval transcripts verify` for all 85 frozen listen-list items. Candidate A is the original local transcript sentence; B substitutes the ASR variant. CPU wav2vec2 emissions and CTC likelihood summed over all monotonic paths are scored per frame, with evaluation mode, one thread, fixed seed and deterministic PyTorch settings. Multi-line edits use the contiguous affected sentence span.
- At the requested 0.05 nats/frame margin: 6 APPLY_B edits across five recordings, 17 KEEP_A and 62 UNSURE. One applied edit also has independent-ASR agreement (LIKELY_REAL). Agreement does not bypass the acoustic margin. All 85 pairs have finite scores; no impossible alignment was used to justify deleting text.
- Median B-minus-A score is +0.017185 nats/frame; p10 is -2.712631, p90 +0.047313, and range -3.934342 to +0.211645. The threshold is provisional, not calibrated accuracy or proof of correct speech. Boundary insertions remain model preferences, not human confirmation.
- Preflight exposed 12 O Captain clips trimmed at a repeated first-stanza ending. Fixed the ending tie-break and regenerated prepared audio from unchanged raw files. All 30 current transcripts have sentence-window JSON; the audit preserves the exact candidate texts and windows used for scoring.
- Verification evidence: 46 fast tests pass, including inherited ROS-style PYTHONPATH isolation. Two independent uncached CPU model runs on a real sentence produced byte-identical emissions and identical candidate scores matching the stored audit. A repeated verifier run is checked for byte-identical reports, transcripts, windows and audit artefacts.
- Audit and distribution are in `reports/day01_acoustic_verification.md` and `data/review/acoustic_verification.json`; the original listen list records automatic decisions. Corrected full-poem audio exposes additional differences: the refreshed diff report contains 221 groups, not all acoustically verified. The 62 UNSURE items remain unresolved; no transcript was labeled human-reviewed. Phase 1 is not complete; Steps 5c onward remain pending.

Reproduce in WSL:

```bash
cd /home/sriram/speech-eval
env -u PYTHONPATH ~/.local/bin/uv run speecheval transcripts verify
make test
./scripts/test.sh
```

The verifier freezes its inputs before applying edits, reuses deterministic evidence on rerun, and rejects changed inference settings, model, scored audio or audited output transcripts rather than silently overwriting applied decisions.
