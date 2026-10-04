# Day 1 — Step 6 alignment runs

Completed both CPU forced aligners on the final automatically reviewed transcripts. No human gold or boundary-accuracy claim is made; Step 7a has not started. `alignment.primary` remains null.

| Aligner | Version | Recordings | Runtime (s) | Jobs/threads |
|---|---|---:|---:|---:|
| mfa | 3.4.2 | 30 | 77.94 | 1 |
| whisperx | 3.7.2 | 30 | 468.177 | 1 |

MFA used english_mfa / english_us_mfa, beam 100, retry beam 400. Corpus validation found 18 OOVs; installed G2P generated all 18 supplementary pronunciations. All state and logs remain inside the project.

60 alignment/v1 JSON files and 60 TextGrids passed schema, original-word mapping, monotonic bounds, uncertainty-mask and tier checks. All 30 frozen cuts match excerpts.yaml; transcript and regenerated source-ASR provenance match sentence windows. A normal cached rerun preserves every alignment, TextGrid, frozen window and transcript byte-for-byte.

| Recording | Aligner | Words | Interpolated | OOV | Zero-duration | Uncertain |
|---|---|---:|---:|---:|---:|---:|
| gettysburg__lv_amb__orig | mfa | 271 | 0 | 0 | 0 | 0 |
| gettysburg__lv_amb__orig | whisperx | 271 | 0 | 0 | 2 | 0 |
| gettysburg__lv_dj__orig | mfa | 270 | 0 | 0 | 0 | 0 |
| gettysburg__lv_dj__orig | whisperx | 270 | 0 | 0 | 0 | 0 |
| gettysburg__lv_dl__orig | mfa | 270 | 0 | 0 | 0 | 0 |
| gettysburg__lv_dl__orig | whisperx | 270 | 0 | 0 | 1 | 0 |
| gettysburg__lv_eep__orig | mfa | 271 | 0 | 0 | 0 | 1 |
| gettysburg__lv_eep__orig | whisperx | 271 | 0 | 0 | 0 | 1 |
| gettysburg__lv_fb__orig | mfa | 270 | 0 | 0 | 0 | 1 |
| gettysburg__lv_fb__orig | whisperx | 270 | 0 | 0 | 2 | 1 |
| gettysburg__lv_jn__orig | mfa | 271 | 0 | 0 | 0 | 0 |
| gettysburg__lv_jn__orig | whisperx | 271 | 0 | 0 | 2 | 0 |
| gettysburg__lv_law__orig | mfa | 271 | 0 | 0 | 0 | 0 |
| gettysburg__lv_law__orig | whisperx | 271 | 0 | 0 | 1 | 0 |
| gettysburg__lv_lb__orig | mfa | 272 | 0 | 0 | 0 | 0 |
| gettysburg__lv_lb__orig | whisperx | 272 | 0 | 0 | 1 | 0 |
| gettysburg__lv_mas__orig | mfa | 271 | 0 | 0 | 0 | 0 |
| gettysburg__lv_mas__orig | whisperx | 271 | 0 | 0 | 0 | 0 |
| gettysburg__lv_mk__orig | mfa | 271 | 0 | 0 | 0 | 0 |
| gettysburg__lv_mk__orig | whisperx | 271 | 0 | 0 | 1 | 0 |
| gettysburg__lv_pc__orig | mfa | 271 | 0 | 0 | 0 | 0 |
| gettysburg__lv_pc__orig | whisperx | 271 | 0 | 0 | 0 | 0 |
| gettysburg__lv_rk__orig | mfa | 270 | 0 | 0 | 0 | 0 |
| gettysburg__lv_rk__orig | whisperx | 270 | 0 | 0 | 1 | 0 |
| gettysburg__lv_sa__orig | mfa | 270 | 0 | 0 | 0 | 0 |
| gettysburg__lv_sa__orig | whisperx | 270 | 0 | 0 | 2 | 0 |
| gettysburg__lv_tg__orig | mfa | 271 | 0 | 0 | 0 | 0 |
| gettysburg__lv_tg__orig | whisperx | 271 | 0 | 0 | 1 | 0 |
| gettysburg__lv_wt__orig | mfa | 271 | 0 | 0 | 0 | 0 |
| gettysburg__lv_wt__orig | whisperx | 271 | 0 | 0 | 0 | 0 |
| jfk_rice__jfk__orig | mfa | 336 | 0 | 0 | 0 | 0 |
| jfk_rice__jfk__orig | whisperx | 336 | 0 | 0 | 0 | 0 |
| o_captain__lv_apc__orig | mfa | 203 | 0 | 5 | 0 | 0 |
| o_captain__lv_apc__orig | whisperx | 203 | 0 | 0 | 2 | 0 |
| o_captain__lv_chip__orig | mfa | 202 | 0 | 5 | 0 | 0 |
| o_captain__lv_chip__orig | whisperx | 202 | 0 | 0 | 1 | 0 |
| o_captain__lv_foxits__orig | mfa | 202 | 0 | 5 | 0 | 0 |
| o_captain__lv_foxits__orig | whisperx | 202 | 0 | 0 | 0 | 0 |
| o_captain__lv_jtm__orig | mfa | 202 | 0 | 5 | 0 | 0 |
| o_captain__lv_jtm__orig | whisperx | 202 | 0 | 0 | 2 | 0 |
| o_captain__lv_mac__orig | mfa | 202 | 0 | 5 | 0 | 0 |
| o_captain__lv_mac__orig | whisperx | 202 | 0 | 0 | 0 | 0 |
| o_captain__lv_mb__orig | mfa | 202 | 0 | 5 | 0 | 0 |
| o_captain__lv_mb__orig | whisperx | 202 | 0 | 0 | 1 | 0 |
| o_captain__lv_md__orig | mfa | 202 | 0 | 5 | 0 | 0 |
| o_captain__lv_md__orig | whisperx | 202 | 0 | 0 | 0 | 0 |
| o_captain__lv_mrg__orig | mfa | 203 | 0 | 5 | 0 | 0 |
| o_captain__lv_mrg__orig | whisperx | 203 | 0 | 0 | 4 | 0 |
| o_captain__lv_rg__orig | mfa | 202 | 0 | 5 | 0 | 1 |
| o_captain__lv_rg__orig | whisperx | 202 | 0 | 0 | 2 | 1 |
| o_captain__lv_s__orig | mfa | 202 | 0 | 5 | 0 | 0 |
| o_captain__lv_s__orig | whisperx | 202 | 0 | 0 | 0 | 0 |
| o_captain__lv_sjs__orig | mfa | 202 | 0 | 5 | 0 | 0 |
| o_captain__lv_sjs__orig | whisperx | 202 | 0 | 0 | 1 | 0 |
| o_captain__lv_ss__orig | mfa | 202 | 0 | 5 | 0 | 0 |
| o_captain__lv_ss__orig | whisperx | 202 | 0 | 0 | 0 | 0 |
| o_captain__lv_th__orig | mfa | 202 | 0 | 5 | 0 | 0 |
| o_captain__lv_th__orig | whisperx | 202 | 0 | 0 | 1 | 0 |
| reagan_challenger__reagan__orig | mfa | 646 | 0 | 13 | 0 | 0 |
| reagan_challenger__reagan__orig | whisperx | 646 | 0 | 0 | 0 | 0 |

## Reproduce

Run from Windows, always entering the WSL checkout:

```powershell
wsl -d Ubuntu -- bash -lc "cd ~/speech-eval && env -u PYTHONPATH ~/.local/bin/uv run speecheval align --aligner both"
wsl -d Ubuntu -- bash -lc "cd ~/speech-eval && env -u PYTHONPATH ~/.local/bin/uv run python scripts/check_alignment.py"
wsl -d Ubuntu -- bash -lc "cd ~/speech-eval && scripts/test.sh -q"
```

Use `--force` only to explicitly replace frozen sentence windows and rerun both aligners. Ordinary reruns reject changed input provenance. Cached reuse is byte-identical; this does not claim two independent full alignment runs are bit-identical.

## Read-only review and limitations

The review found a frozen-window overwrite bug. Regression tests now protect existing/manual boundaries and reject stale transcript/ASR/cut/padding provenance; only missing windows are created without --force. A stale MFA corpus hardlink is also replaced when the prepared audio inode changes. Both tests were observed failing before the fixes and passing afterward.

Minor deferred robustness issues: per-word interpolation flags are dropped by the shared schema, although warnings remain (none of the 30 original calibration alignments was interpolated); MFA installation lookup is specific to this user. Neither affected these runs. The reviewer declined to judge human transcript truth, boundary accuracy without gold, or generalization of the proxy calibration false-acceptance rate. Final WhisperX artifacts were checked by the execution script after the review finished.

Both aligners map all 7,671 transcript words. MFA has no zero-duration or interpolated entries. WhisperX has 28 zero-duration entries after overlap repair (listed above); they remain in JSON, but cannot be represented as nonzero TextGrid intervals. They require later boundary QA, not invented durations. Neither aligner has interpolated entries in this run.

Three-way ASR agreement remains a proxy, not human ground truth. Uncertain words are propagated for exclusion downstream; alignment completion does not resolve them. Stop before Step 7a.
