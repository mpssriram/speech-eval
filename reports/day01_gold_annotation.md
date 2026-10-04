# Step 7a — human boundary annotation required

Preparation is complete; **these are unreviewed templates, not gold labels**. No bake-off results or primary aligner recommendation have been generated.

| Recording | Why selected | Candidate words |
|---|---|---:|
| gettysburg__lv_fb__orig | Highest measured LUFS among clean Gettysburg readers: -22.405 LUFS | 20 |
| jfk_rice__jfk__orig | Required government excerpt | 20 |
| reagan_challenger__reagan__orig | Required government excerpt | 20 |

Selection excludes uncertain/interpolated words and requires at least 0.15 s word duration in both aligners. Twenty unique samples span each eligible word list using a rounded fractional stride. Each candidate averages the two aligners' start/end times, then widens by 0.15 s on each side, clipped to the prepared recording. The selection and original model boundaries are frozen in `data/gold/alignment/todo/selection.json`.

## What the user must do

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
