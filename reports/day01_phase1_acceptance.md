# Phase 1 acceptance audit

Engineering implementation and promotion are complete only if the automated checks below pass. Full human/quality acceptance is NOT claimed. Latest user authorization permits independent later-phase engineering while these risks stay visible.

| Item | Status | Evidence |
|---|---|---|
| Licensed source manifest and raw hashes | PASS | 30 sources: 15 Gettysburg, 13 O Captain, JFK and Reagan; SHA256 verified |
| Prepared audio formats and durations | PASS | 60 mono PCM16 WAVs: 44.1 kHz / 16 kHz |
| Three LibriVox listening spot-checks | PENDING | Frozen ASR-anchor cuts are available; no human listening check claimed |
| JFK excerpt | PASS | 157.632 s; frozen sentence-bounded excerpt from Phase 1 ASR-anchor audit; anchor present |
| Automatic transcript audit replacing Step 5b | PASS | Historical original-candidate audit: 64 APPLY_B, 18 KEEP_A, 3 UNSURE; number rendering changed without claiming new human/acoustic truth |
| Both aligners produced valid current JSON | PASS | 60 alignment/v1 outputs match transcript words, masks and provenance |
| Bake-off, primary selection and promotion | PASS | MFA selected by user; all 60 promoted artifacts byte-identical to primary |
| Step 8 QA report | PASS | 30 rows; 12 flagged recordings |
| Human Praat spot-check of flagged alignments | PENDING | PENDING; user approval of aligner choice is not a listening/boundary check |
| Gold accuracy target | FAIL | Both aligners below 90% within 50 ms against limited visual reference; explicit risk, not silently passed |
| Cached prepare and primary alignment hash rerun | PASS | Audio, manifests, alignments, windows and transcripts byte-identical |
| Pytest isolation/cache placement | PASS | .pytest_work/ and .pytest_cache/ ignored outside data/.cache; make test removes PYTHONPATH and disables external plugins |
| Full test suite | PASS | make test with inherited ROS PYTHONPATH: 88 tests passed; exit 0 |
| Progress summary | PASS | Current dated summary in docs/specs/PROGRESS.md |

Human spot-checks and the visual-gold quality target are NOT silently passed. Automated later-phase engineering is authorized while these limitations remain visible.
