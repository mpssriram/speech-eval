# Step 7a — supplied visual annotation and human spot-check

## 2026-10-06 — completed annotations received

The three TextGrids and `ANNOTATION_NOTES.md` were copied, not moved, from the user's `gold_pack/done/` to `data/gold/alignment/`, alongside `todo/`. Source/destination bytes were compared. The originals in done and todo are unchanged.

**Annotator: Claude, visual annotation from waveform/spectrogram/intensity/pitch tracks, not listened**, plus a human spot-check reported by the user. The notes list seven suggested human spot checks but provide no measured human boundaries or numerical annotation-error estimate. This is not fully human-listened gold. Independence from MFA/WhisperX is asserted by the annotator, not independently proven by the evaluation.

| Recording | Total intervals | Labelled words | Excluded trailing ? | Eligible words |
|---|---:|---:|---:|---:|
| gettysburg__lv_fb__orig | 41 | 20 | 5 | 15 |
| jfk_rice__jfk__orig | 41 | 20 | 5 | 15 |
| reagan_challenger__reagan__orig | 41 | 20 | 13 | 7 |

The 41 intervals include blank gaps, including a gap before the first word. Validation counts the 20 labelled intervals and matches labels in order, removing only a trailing ?. Unclear words are excluded from comparison. All intervals must remain finite, non-overlapping and inside the prepared audio.

Seventeen supplied intervals extend beyond the old aligner-derived template windows. They are preserved and explicitly reported, not clipped to model suggestions. Frozen numeric template labels are mapped to the full expanded transcript word span, including any index shifts. Annotation files are never rewritten for the numeric alignment fix.

Current evaluation command: `env -u PYTHONPATH ~/.local/bin/uv run speecheval evaluate alignment`. Results and limitations are in `reports/day01_aligner_bakeoff.md`. The historical template handoff below is retained for provenance, not a request for additional approval or a claim that these annotations were heard by a human.

## Historical template preparation

At preparation time these were **unreviewed templates, not gold labels**. The subsequent supplied annotations have the provenance described above.

| Recording | Why selected | Candidate words |
|---|---|---:|
| gettysburg__lv_fb__orig | Highest measured LUFS among clean Gettysburg readers: -22.405 LUFS | 20 |
| jfk_rice__jfk__orig | Required government excerpt | 20 |
| reagan_challenger__reagan__orig | Required government excerpt | 20 |

Selection excludes uncertain/interpolated words and requires at least 0.15 s word duration in both aligners. Twenty unique samples span each eligible word list using a rounded fractional stride. Each candidate averages the two aligners' start/end times, then widens by 0.15 s on each side, clipped to the prepared recording. The selection and original model boundaries are frozen in `data/gold/alignment/todo/selection.json`.

## Original annotation handoff (historical)

1. In Praat, open the prepared WAV from `\\wsl$\Ubuntu\home\sriram\speech-eval\data\audio\hq\{recording_id}.wav` and its template from `\\wsl$\Ubuntu\home\sriram\speech-eval\data\gold\alignment\todo\{recording_id}.TextGrid`.
2. Open the sound and TextGrid together in View & Edit. For each of the 20 labeled words, zoom in, listen, and inspect the waveform/spectrogram. Tighten the `gold` interval to the actual start and end of that word. The deliberately widened template is not a correct label.
3. Preserve the word labels. Save the finished file outside `todo`, to `\\wsl$\Ubuntu\home\sriram\speech-eval\data\gold\alignment\{recording_id}.TextGrid`. Repeat for all three recordings (60 words total).
4. Tell Codex when the three files are complete. Step 7b can then evaluate both aligners against those independent annotations. The user chooses `alignment.primary` after reading that report.

If reliable boundary annotation is not possible, stop here: the automatic templates must not be presented as human ground truth. Any replacement evaluation protocol requires an explicit change of scope and honest limitations.

## Reproduce preparation and checks

```powershell
wsl -d Ubuntu -- bash -lc "cd ~/speech-eval && env -u PYTHONPATH ~/.local/bin/uv run speecheval gold prepare"
wsl -d Ubuntu -- bash -lc "cd ~/speech-eval && env -u PYTHONPATH ~/.local/bin/uv run python scripts/check_gold.py"
wsl -d Ubuntu -- bash -lc "cd ~/speech-eval && scripts/test.sh -o addopts='' -q"
```

Existing manual edits are never overwritten. Preparation rejects stale inputs or modified todo templates, retaining the files for explicit resolution. Final human gold files are never written by this command.

## Verification and review

All three real templates have exactly one `gold` tier and 20 labeled intervals. All 60 intervals match the symmetric averaged/padded boundaries; eligibility exclusions, source hashes and template hashes pass. Cached preparation is byte-identical. A read-only reviewer independently confirmed the real selection and artifacts.

The review flagged missing alignment schema/identity checks. This was graded Important because misfiled or duplicated aligner output could bias the independent average. Two regressions were observed failing before the fix, then passing afterward. Full suite: 69 tests passed. No deferred review findings.

The reviewer did not assess acoustic correctness, human annotation quality, downstream bake-off/evaluation, or model pipeline behavior. Those remain outside template preparation; independent annotation and subsequent evaluation are still required. No new accuracy claim is made here.
