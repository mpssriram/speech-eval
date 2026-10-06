# Spec progress

## 2026-10-07 — Phase 1 engineering close-out, explicit quality limitations

The user selected MFA and subsequently authorized autonomous continuation into later phases. Human spot-check is PENDING: the previous "reported spot-check" claim was incorrect and has been corrected. Supplied Claude visual annotations were not listened to; no human boundary-error estimate exists.

The report separates gold coverage (37 words / 74 edges) from corpus coverage (30 recordings / 7,678 transcript words). Baseline OOV=84 is repeated transcript-word occurrences with a base-dictionary-missing token, from 18 unique forms; none of those forms is in the 37 scored words. Baseline already used temporary G2P pronunciations. Two actual installed CPU MFA G2P runs generated identical raw hashes and identical canonical committed dictionaries (38 pronunciation variants). The custom supplement plus installed base dictionary gives zero OOV occurrences; rerunning MFA on all 30 leaves every gold mean/median start/end/pooled metric unchanged. Adopted as default, with dictionary SHA validation and artifact-bound non-worsening acceptance required before ordinary use/promotion. Candidate experiments cannot promote.

MFA is now alignment.primary and all 30 JSON/TextGrid pairs are promoted. Step 8 QA exists with all flags retained; human Praat/listening checks remain PENDING. Signed errors, in-sample per-edge median-bias residuals, per-recording and lexical stop-initial breakdowns, and paired stratified-word bootstrap (10,000; seed 20261007) are implemented. Conditional bootstrap intervals do not model annotation uncertainty or generalize across readers. Raw pooled medians remain 52 ms MFA versus 72 ms WhisperX; both still fail 90% within 50 ms against this small visual reference. No accuracy improvement is claimed from making G2P reproducible.

88 tests passed after test-first changes and one final code-review fix pass. The review identified missing artifact-bound adoption gating: rejection/stale-evidence regression RED then GREEN. Deferred Minor: heterogeneous paired/stratified bootstrap unit regression; actual implementation was reviewed as correct. Pytest basetemp/TMPDIR now use ignored .pytest_work outside data/.cache; old owned pytest work was moved recoverably to .pytest_work/legacy. Full source-preserving prepare/cache hash checks passed. Final refreshed bake-off determinism and final acceptance evidence are recorded in the report/JSON after their runs finish; no result is inferred from an in-progress run.

Final executions finished: both aligners' two fresh-process three-recording JSON hash pairs are identical; MFA remains recommended. All automated acceptance rows pass, the three LibriVox listening checks and flagged-boundary human checks remain PENDING, and the visual-gold accuracy target remains FAIL. Current checks include the final 88-test inherited-ROS run, accepted dictionary evidence and identical cached prepare/alignment/bake-off hashes. This is engineering closure with quality limitations, not full human acceptance.

Reproduce: `env -u PYTHONPATH ~/.local/bin/uv run speecheval evaluate alignment`; `speecheval align --promote`; `speecheval report alignment`; `env -u PYTHONPATH ~/.local/bin/uv run python scripts/check_bakeoff.py`; `env -u PYTHONPATH ~/.local/bin/uv run python scripts/check_phase1.py`; `make test`. A new dictionary experiment uses `speecheval align --aligner mfa --dictionary-experiment` then `scripts/compare_custom_dictionary.py`; only accepted, hash-matching evidence permits default adoption/promotion. Phase 1 engineering can feed Phase 2 under the user's waiver, but full human/quality acceptance is not claimed.

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

## 2026-10-04 — Calibrated local acoustic verification (Step 5b)

- Reassessed all 85 original candidates from the original pre-verification text, including the six earlier edits. Local total CTC scores replace sentence-averaged scores; the old audit/report are preserved for comparison.
- Regenerated all 12 repaired full-source large-v3 caches, 15 affected medium.en dispute clips, and final sentence windows. All 30 raw hashes and frozen cuts are consistent with the manifests; all 60 prepared WAV formats/durations are valid. Cut changes and hashes are in the report and `data/review/asr_regeneration.json`.
- Exactly 300 fixed-seed controls: 100 phonetic substitutions, 100 deletions and 100 insertions, sampled proportionally to eligible words across all 30 recordings. Previously uncertain words are excluded. Three-way ASR agreement is only a proxy label, not human ground truth; unprompted full-recording medium.en context was needed for one reader.
- Final margin: 2.425378476083314 total nats, in-sample fake acceptance 6/300 = 2%. Decisions: 64 applied, 18 kept, 3 uncertain. Uncertain final word indices are one each for `gettysburg__lv_eep__orig`, `gettysburg__lv_fb__orig`, and `o_captain__lv_rg__orig`; the other 27 masks are empty. Automatic markers are `# reviewed: auto-acoustic-calibrated`, not human review.
- The report includes the true-minus-fake histogram, threshold lines, all decisions, per-recording controls/masks and limitations. Replayed historical normalization on identical inputs confirms 178 -> 177 groups (JFK 6 -> 5); no review item was dropped.
- A preliminary mixed-process cache failed fresh-model consistency by ~0.002 nats and was preserved, then superseded by isolated CPU workers with explicit backend settings. Two fresh uncached models now have identical emissions/scores matching the audit. Seeded control replay is exact, 100 phonetic distances were checked, all masks/windows match final transcript hashes, and 60 tests pass. Step 5c and Step 6 are next; stop before Step 7a.

Reproduce inside WSL: `env -u PYTHONPATH ~/.local/bin/uv run speecheval transcripts verify`, `env -u PYTHONPATH ~/.local/bin/uv run python scripts/check_calibration.py`, `make test`.

## 2026-10-04 — Step 5c complete

Re-ran `env -u PYTHONPATH ~/.local/bin/uv run speecheval transcripts diff`: 163 current groups across 30 recordings. All files are listed as auto-acoustic-calibrated (not human), with remaining differences shown. New differences beyond the original 85 are not claimed verified. Review classification has a regression test; 60 tests pass. Continue with both forced aligners, then stop before Step 7a.

## 2026-10-04 — Step 6 complete; STOP before Step 7a

Both CPU forced aligners completed all 30 recordings: MFA 3.4.2 (77.940 s, fixed one job; 18 OOV pronunciations generated) and WhisperX 3.7.2 (468.177 s, one thread). All 60 alignment/v1 JSON and 60 TextGrids passed schema, original-word mapping, monotonic bounds, tier and uncertainty-mask checks. Both map 7,671 words. MFA has no zero-duration entries; WhisperX has 28, retained and disclosed for later QA rather than assigning invented durations. No interpolated entries in either run.

All 30 frozen cuts match excerpts.yaml; windows match final transcript and source-ASR hashes. Cached both-aligner reruns are byte-identical for alignments, TextGrids, windows and transcripts. A read-only review found a frozen-window overwrite bug and a minor stale hardlink hazard; failing regression tests preceded both fixes. Full suite: 62 passed, including inherited ROS PYTHONPATH isolation. Fresh calibration seed/inference checks also passed again.

Final calibration remains margin 2.425378476083314 total nats; 6/300 = 2% in-sample proxy false acceptance; 64 applied / 18 kept / 3 uncertain. One uncertain word each in gettysburg lv_eep, gettysburg lv_fb, and O Captain lv_rg; zero in the other 27. Three-way ASR agreement is not human ground truth. Reports: `reports/day01_acoustic_verification.md` and `reports/day01_alignment_runs.md`. `alignment.primary` remains null, no gold has been prepared, and Phase 1 as a whole remains incomplete until the later bake-off/QA steps.

## 2026-10-04 — Step 7a templates prepared; STOP for USER annotation

User said continue. Implemented `speecheval gold prepare` with frozen provenance and no manual-file overwrites. Selected clean highest-LUFS Gettysburg reader lv_fb (-22.405), JFK and Reagan. Each has 20 symmetric averaged/padded candidate intervals in `data/gold/alignment/todo`, not human gold. Uncertain/interpolated words are excluded; both aligners must place each word for at least 0.15 s. Rounded fractional stride spans all eligible words, with the selection method disclosed.

Real artifact verification and byte-identical cached preparation passed. Independent read-only review confirmed all 60 candidates. Two failing identity regressions preceded the schema/identity safeguard fix; full suite 69 passed. Preparation never runs evaluation or chooses a primary aligner. User must annotate the 60 boundaries in Praat and save the three final TextGrids outside todo. Detailed handoff: `reports/day01_gold_annotation.md`. Phase 1 remains incomplete.

Reproduce inside WSL: `env -u PYTHONPATH ~/.local/bin/uv run speecheval gold prepare`, `env -u PYTHONPATH ~/.local/bin/uv run python scripts/check_gold.py`, `scripts/test.sh -o addopts='' -q`.

## 2026-10-06 — supplied Step 7a annotations; Step 7b complete; STOP after report

Latest user instruction supersedes earlier promotion/QA requests: stop after the bake-off report. Phase 1 is not yet closed; primary promotion and Step 8 remain pending. No Phase 2 work was started.

- Copied (not moved) three TextGrids and ANNOTATION_NOTES.md from gold_pack/done into data/gold/alignment, next to todo. The annotator is Claude, visually using waveform/spectrogram/intensity/pitch, without listening, plus a human spot-check reported by the user. The notes contain no actual human boundary measurements or measured error estimate. This is a limited supplied reference, not fully human-listened gold; independence is asserted by the annotator, not proven by this evaluation.
- Each supplied grid has 41 total intervals including gaps and 20 labelled words. Excluded trailing question marks: Gettysburg lv_fb 5, JFK 5, Reagan 13; 37 words / 74 boundaries remain. Labels, bounds, ordering and non-overlap pass. Seventeen intervals extend beyond old template boxes and are flagged but retained within recording bounds, not clipped to model suggestions. Supplied files and todo originals remain byte-identical.
- Spelled every remaining numeric body token in JFK, Reagan and O Captain lv_apc, preserving punctuation/comments. This includes all seven requested examples, C-1/F-1 digit portions, 25, 390 and 2006. All 30 normalized token sequences are unchanged. Archived original texts/masks/windows, committed complete old-to-new word-span mappings, remapped mask hashes/indices, regenerated the three affected windows and reran diffs (163 groups). Raw audio, ASR caches, cuts and the other 27 frozen windows are unchanged. Historical calibrated acoustic evidence remains historical, not falsely relabelled as verification of the expanded text.
- Reran both aligners on all 30 current transcripts: MFA CPU one job 143.179 s; WhisperX CPU one thread 767.813 s. All 60 JSON/TextGrid pairs match the current texts/masks/windows and valid timing schema. MFA has 0 interpolated words and 84 OOV word occurrences; WhisperX has 0 interpolated words and 0 emitted OOV warnings (character-based alignment, not equivalent lexical dictionary coverage).
- Two additional real fresh-process runs per aligner on the three gold recordings produced identical JSON SHA256 pairs for all three: MFA 53.417 / 53.183 s, WhisperX 82.378 / 80.104 s. Hardware: Intel Core Ultra 9 275HX, WSL Ubuntu 24.04, CPU only. Exact hashes, per-word errors and environment/model fingerprints are committed with the audit.

| Aligner | Start median / mean ms | End median / mean ms | Pooled median ms | Boundaries within 20 / 50 ms |
|---|---:|---:|---:|---:|
| MFA | 61.000 / 74.541 | 38.000 / 66.081 | 52.000 | 13.514% / 48.649% |
| WhisperX | 134.000 / 143.243 | 45.000 / 108.486 | 72.000 | 16.216% / 39.189% |

Recommendation: MFA by lower pooled median (20 ms difference, so the tie-break is not needed). **Both fail the 90%-within-50-ms target**, explicitly recorded as risks. Small selected visual reference, 23 unclear-word exclusions and unquantified spot-check quality limit interpretation. Recommendation does not establish general accuracy. `alignment.primary` remains null and nothing was promoted, consistent with the requested report-only stop.

Verification: `make test` with ROS-style PYTHONPATH inherited passed 80/80; the Makefile removes it and disables external plugins. `scripts/check_bakeoff.py` verified all raw hashes, supplied files/HQ audio/todo bytes, current mappings/masks, all 30 frozen cuts and window provenance, 60 JSON/TextGrids, 12 actual determinism outputs and report arithmetic. Cached alignment and bake-off reruns are byte-identical. Test-first implementation and one final code-review fix pass added stale-dataset, complete-migration and model/environment-cache safeguards; no review findings remain deferred for this step.

Reproduce in WSL:

```bash
cd /home/sriram/speech-eval
env -u PYTHONPATH ~/.local/bin/uv run speecheval evaluate alignment
env -u PYTHONPATH ~/.local/bin/uv run python scripts/check_bakeoff.py
make test
```

Use `speecheval evaluate alignment --force` for four new actual determinism passes. `check_gold.py` and `check_alignment.py` are historical pre-annotation checks; their no-gold/unchanged-original-text assumptions no longer describe this stage. Use the current check above. Reports: reports/day01_gold_annotation.md and reports/day01_aligner_bakeoff.md. STOP here.
