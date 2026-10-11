# Blind speech-delivery ratings — about 15 minutes

You need headphones or speakers, the 12 FLAC clips in this folder, and
`rating_form.csv`. Work on your own. Do not look at the repository, answer key,
system scores or anyone else's answers. Replay clips if useful. Judge how the
speaker delivers the words, not the topic or whether you agree with it.

1. Open `rating_form.csv` in a spreadsheet or text editor. Leave the column
   names, clip names and row order unchanged. Play each matching FLAC file in
   CSV order with an audio player that supports FLAC.
2. Choose an anonymous ID, such as `rater07`, and put it in `rater_id` on every
   completed row. Do not put your real name in the form.
3. Put one overall delivery score in `overall`: **1 very poor, 2 poor,
   3 acceptable, 4 good, 5 excellent**. Every completed row needs this score.
4. In `flaw_type`, write `none` if you hear no delivery flaw. Otherwise use
   only the exact labels below. In `flaw_time_s`, give the approximate time
   in seconds from the beginning of that clip where you hear the flaw.
   For `none`, leave the time empty.

| Exact label | What to listen for |
|---|---|
| `rushing` | Words delivered too quickly |
| `dragging` | Words delivered too slowly |
| `monotone` | Too little pitch variation |
| `too_quiet` | Delivery too quiet |
| `mumbling` | Unclear articulation |
| `awkward_pause` | A pause that breaks a phrase unnaturally |
| `missing_pause` | No pause where a break is needed |

If you hear several types, separate them with semicolons and give one time
for each in the same order: `rushing;too_quiet` and `3.2;8.0`. Do not use commas
inside these cells. Do not combine `none` with a flaw. You can decline the
task or skip a clip rather than guess. For a skipped clip, KEEP `clip` unchanged
and leave the other four fields empty. If you hear a flaw but cannot name it
after replaying, skip that clip; do not use `none` to mean unsure.

Save a separate **CSV** named `ratings_<your_id>.csv`, for example
`ratings_rater07.csv`. Check that it still has the five original column names
and 12 clip rows, not a spreadsheet-only file. Return that CSV to the person
who sent you this pack, through the same channel. Do not overwrite the blank
form or another person's answers; do not modify or return the audio files.

Only independent human responses will be used for agreement. AI-generated
ratings and the recorder's own ratings are not independent rater data.
