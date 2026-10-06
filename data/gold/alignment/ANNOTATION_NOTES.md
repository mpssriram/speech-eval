# Gold word-boundary annotation notes (Step 7a)

Annotator: Claude (visual annotation from waveform + wideband spectrogram + intensity/pitch tracks; audio was NOT listened to).
Human check: the user spot-checks 7 words in Praat (list below); the mean absolute boundary difference is the gold's own error estimate.
Independence: boundaries were read only from the acoustic signal and the as-spoken transcript. No MFA / WhisperX output was used.

Counts: 60 words, 23 labelled with a trailing `?` (uncertain, to be EXCLUDED from the aligner comparison):
- gettysburg__lv_fb__orig: 5 uncertain (that?, fitting?, can?, these?, earth.?)
- jfk_rice__jfk__orig: 5 uncertain
- reagan_challenger__reagan__orig: 13 uncertain (older, noisier recording)

Format: each TextGrid has ONE interval tier "gold" with 41 intervals (gaps are empty, word intervals carry the original word text, with `?` appended when uncertain). Interval count is 41, not 40, because the first word does not start at 0 s.

Findings to pass on:
1. Digits in the as-spoken transcripts ("35", "48", also "10,000", "24", "19", "45", "40") are spoken as number words ("thirty-five", "forty-eight"). Aligners cannot align digits (OOV / <unk>), so the as-spoken text should spell them out. The gold intervals for "35" and "48" cover the whole spoken number.
2. Several aligner boxes in words.csv do not match the acoustics well (for example "35": box 0.007-0.664 vs spoken "thirty-five" 0.23-1.06 s). This is expected to show up in the bake-off.

Suggested human spot-check words (clear, no `?`), time = my boundaries:
- gettysburg #2 "this" 5.610-5.865
- gettysburg #9 "consecrate" 45.31-45.99
- gettysburg #18 "nation," 96.20-96.86
- jfk #10 "shattered" 77.94-78.40
- jfk #17 "Some" 130.75-131.10
- reagan #8 "truths." 89.885-90.31
- reagan #17 "Drake" 207.56-207.88
