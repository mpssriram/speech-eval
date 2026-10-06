# Day 1 aligner bake-off

Annotator: **Claude**, visually from waveform/spectrogram/intensity/pitch, **without listening**, plus a human spot-check reported by the user. This is not fully human-listened gold. The notes suggest seven spot-check words but contain no human boundary measurements or measured annotation-error estimate. Independence from MFA/WhisperX is asserted by the annotator, not independently established by this evaluation.

## Validation and exclusions

| Recording | Total intervals | Labelled words | Excluded ? | Excluded transcript uncertainty | Scored | Outside old template |
|---|---:|---:|---:|---:|---:|---:|
| gettysburg__lv_fb__orig | 41 | 20 | 5 | 0 | 15 | 5 |
| jfk_rice__jfk__orig | 41 | 20 | 5 | 0 | 15 | 7 |
| reagan_challenger__reagan__orig | 41 | 20 | 13 | 0 | 7 | 5 |

All labelled intervals match the frozen template labels after removing only a trailing ?. Blank gaps do not count as annotated words. Bounds are finite, ordered, non-overlapping and inside the same prepared audio. Seventeen supplied boundaries extend outside old model-derived boxes; they are flagged and retained, never clipped or changed. The 41-interval grids are copied unchanged.

## Error table

| Aligner | Start median ms | Start mean ms | End median ms | End mean ms | Pooled median ms | ≤20 ms % | ≤50 ms % | Interpolated words /30 | OOV words /30 | Deterministic 3/3 | Hardware |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| mfa | 61.0 | 74.541 | 38.0 | 66.081 | 52.0 | 13.514 | 48.649 | 0 | 84 | True | CPU |
| whisperx | 134.0 | 143.243 | 45.0 | 108.486 | 72.0 | 16.216 | 39.189 | 0 | 0 | True | CPU |

Threshold percentages above pool start/end boundaries. OOV counts count actual word occurrences, not unique dictionary entries.

| Aligner | Starts within 20 ms % | Starts within 50 ms % | Ends within 20 ms % | Ends within 50 ms % |
|---|---:|---:|---:|---:|
| mfa | 13.514 | 37.838 | 13.514 | 59.459 |
| whisperx | 8.108 | 18.919 | 24.324 | 59.459 |

Measured hardware: Intel Core Ultra 9 275HX, 24 logical CPUs visible in WSL Ubuntu 24.04. Both aligners use CPU with one inference thread/job; the RTX 5080 GPU is not used for this comparison.

## Runtime and independent determinism

| Aligner | Recorded dataset alignment runtime s | Gold rerun 1 s | Gold rerun 2 s |
|---|---:|---:|---:|
| mfa | 143.179 | 53.417 | 53.183 |
| whisperx | 767.813 | 82.378 | 80.104 |

Two independent fresh Python processes actually rerun each installed aligner on the three annotated recordings, with fixed CPU settings. Runtime is measured separately from deterministic JSON; exact per-recording SHA256 pairs are below.

| Aligner | Recording | Run 1 SHA256 | Run 2 SHA256 |
|---|---|---|---|
| mfa | gettysburg__lv_fb__orig | 7d9a7f5a2455ea5ae0aeeea8bbeb9df379f9c75fef7f4b3a149d90c955d01c86 | 7d9a7f5a2455ea5ae0aeeea8bbeb9df379f9c75fef7f4b3a149d90c955d01c86 |
| mfa | jfk_rice__jfk__orig | d4cd775aa37916388544f716fb59c9b68e099ba3bb5b27ef2507ad7a22354482 | d4cd775aa37916388544f716fb59c9b68e099ba3bb5b27ef2507ad7a22354482 |
| mfa | reagan_challenger__reagan__orig | 658c1964365541097412fddba0da2fc20c6bf969d8fbe43268056c851a1bd551 | 658c1964365541097412fddba0da2fc20c6bf969d8fbe43268056c851a1bd551 |
| whisperx | gettysburg__lv_fb__orig | 977c9bfbaee28f97d3cac7398008ce1292a701ae7a74e0c2dd68190d50872e9c | 977c9bfbaee28f97d3cac7398008ce1292a701ae7a74e0c2dd68190d50872e9c |
| whisperx | jfk_rice__jfk__orig | 0fc2c927f4064a8e357ce0d19b12bb8feeff27911610909ea3e6b7fd46644c35 | 0fc2c927f4064a8e357ce0d19b12bb8feeff27911610909ea3e6b7fd46644c35 |
| whisperx | reagan_challenger__reagan__orig | cce01dd076ff7c2e9550efa8e22d3b178fec2231697cb49cb5f41b6f4664e32d | cce01dd076ff7c2e9550efa8e22d3b178fec2231697cb49cb5f41b6f4664e32d |

## Recommendation and risks

Recommended: **mfa** under the specified pooled median rule; when medians differ by less than 10 ms, deterministic CPU aligners win the tie, with MFA preferred if both qualify. This report does not set alignment.primary or promote files.
- RISK: mfa has 48.649% within 50 ms, below 90%.
- RISK: whisperx has 39.189% within 50 ms, below 90%.

## Limits and reproducibility

Only 37 of 60 visually annotated words are potentially scorable after 23 question-mark exclusions; this is a small selected sample, especially Reagan (7 words). Unclear-word exclusion creates selection bias. Human spot-check extent/error is not quantified, no inter-annotator study was done, and visual annotation without listening may miss acoustic ambiguity. Results compare models against this supplied reference, not an established human error-free ground truth.

Numeric transcript rendering was changed for alignment. Original bodies, hashes, old-to-new word spans and number edits are preserved in data/review/number_expansion.json and before_number_expansion/. Frozen templates and gold labels were NOT rewritten. Numeric gold labels map to the complete expanded word span, not just its first token. ASR, audio, raw recordings and frozen cuts are unchanged; affected diffs/windows/alignments were regenerated.

Reproduce inside WSL: `env -u PYTHONPATH ~/.local/bin/uv run speecheval evaluate alignment`. Cached evidence is tied to current audio/transcript/window/config/gold/code hashes. `--force` reruns all four real inference passes. Full scoring rows and per-edge metrics: data/review/alignment_bakeoff.json.
