# Phase 10 recording script - eight genuine takes

Supersedes the old scripts. Numbers are one-based `sentence_units(text, False)`, including semicolon/colon splits. Read all printed units; do not speak numbers/bars. Mode A: all takes. Mode B: 02/03 vs own 01. No C take.

Quiet room; same mic about 30 cm from your mouth; no music/fan. Make and listen to your own 10-second test for clipping/hum. Record each take once; keep going through slips and note them. No detector tuning on any take.

## Gettysburg - canonical sentences 1-10, full text

Reading source: `data/transcripts/canonical/gettysburg.txt`, never `gettysburg__lv_fb__orig.txt`.

1. Four score and seven years ago our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated to the proposition that all men are created equal.
2. Now we are engaged in a great civil war, testing whether that nation, or any nation so conceived and so dedicated, can long endure.
3. We are met on a great battle-field of that war.
4. We have come to dedicate a portion of that field, as a final resting place for those who here gave their lives that that nation might live.
5. It is altogether fitting and proper that we should do this.
6. But, in a larger sense, we can not dedicate -- we can not consecrate -- we can not hallow -- this ground.
7. The brave men, living and dead, who struggled here, have consecrated it, far above our poor power to add or detract.
8. The world will little note, nor long remember what we say here, but it can never forget what they did here.
9. It is for us the living, rather, to be dedicated here to the unfinished work which they who fought here have thus far so nobly advanced.
10. It is rather for us to be here dedicated to the great task remaining before us -- that from these honored dead we take increased devotion to that cause for which they gave the last full measure of devotion -- that we here highly resolve that these dead shall not have died in vain -- that this nation, under God, shall have a new birth of freedom -- and that government of the people, by the people, for the people, shall not perish from the earth.

**Gettysburg takes:** 01 best natural delivery. 02 rushing in 4; two-second awkward_pause in 6 at `in a larger | sense`; too_quiet (trail off) at the end of 8. 03 monotone in 2; mumbling in 7; missing_pause between 8 and 9. Everything else normal in 02/03. 04 choose three different supported flaw types and immediately note which/where.

## Reagan - canonical splitter units 1-17 only

Reading source: `data/transcripts/canonical/reagan_challenger.txt`. Start at "Ladies and gentlemen"; STOP after "They had a hunger to explore the universe and discover its truths." Do not continue into "They wished to serve".

1. Ladies and gentlemen, I'd planned to speak to you tonight to report on the state of the Union, but the events of earlier today have led me to change those plans.
2. Today is a day for mourning and remembering.
3. Nancy and I are pained to the core by the tragedy of the shuttle Challenger.
4. We know we share this pain with all of the people of our country.
5. This is truly a national loss.
6. Nineteen years ago, almost to the day, we lost three astronauts in a terrible accident on the ground.
7. But we've never lost an astronaut in flight;
8. we've never had a tragedy like this.
9. And perhaps we've forgotten the courage it took for the crew of the shuttle.
10. But they, the Challenger Seven, were aware of the dangers, but overcame them and did their jobs brilliantly.
11. We mourn seven heroes:
12. Michael Smith, Dick Scobee, Judith Resnik, Ronald McNair, Ellison Onizuka, Gregory Jarvis, and Christa McAuliffe.
13. We mourn their loss as a nation together.
14. For the families of the seven, we cannot bear, as you do, the full impact of this tragedy.
15. But we feel the loss, and we're thinking about you so very much.
16. Your loved ones were daring and brave, and they had that special grace, that special spirit that says, ``Give me a challenge, and I'll meet it with joy.''
17. They had a hunger to explore the universe and discover its truths.

**Reagan takes:** 01 best natural delivery. 02 rushing in 10; two-second awkward_pause in 16 at `were | daring and brave`; too_quiet (trail off) at the end of 15. 03 monotone in 6; mumbling in 9; missing_pause between 14 ("For the families...") and 15 ("But we feel..."). Everything else normal in 02/03. 04 choose three different supported flaw types and immediately note which/where.

## Files, transcripts and truthful notes

Save readable WAVs in `data/human/raw/`; use each listed transcript basename with `.wav`. Only these eight WAV names are discovered; do not rename MP3/M4A to WAV. Raw rate/channels/bit depth: no fixed requirement (stereo/16 kHz tested). Conversion: mono PCM16/44.1 kHz, MFA 16 kHz, no gain normalisation. Upload: positive duration, <=600 s and <=25 MiB. Required edge silence: NOT SPECIFIED; trim padding up to 0.25 s.

**YOU write these eight as-spoken files after recording**, using the canonical words plus your actual slips/omissions/repetitions. Keep punctuation; remove numbering/bars/headers. No lv_fb deviations are inherited. The driver expands numbers; the pipeline writes `data/transcripts/as_spoken/{text_id}__user__input_<hash>.txt` from your supplied text for MFA.

- `data/human/transcripts/gettysburg__user__take01.txt`
- `data/human/transcripts/gettysburg__user__take02.txt`
- `data/human/transcripts/gettysburg__user__take03.txt`
- `data/human/transcripts/gettysburg__user__take04.txt`
- `data/human/transcripts/reagan_challenger__user__take01.txt`
- `data/human/transcripts/reagan_challenger__user__take02.txt`
- `data/human/transcripts/reagan_challenger__user__take03.txt`
- `data/human/transcripts/reagan_challenger__user__take04.txt`

**Notes:** `data/human/raw/notes.md`: fenced `json` block, `takes` dictionary, every supplied WAV basename without extension, `flaws` list and `slips`. Declare empty flaws explicitly. FORMAT EXAMPLE ONLY:

```json
{"takes":{"gettysburg__user__take01":{"flaws":[],"slips":"none"},"gettysburg__user__take02":{"flaws":[{"type":"rushing","sentence":4}],"slips":"describe actual slips"}}}
```

Each flaw uses a supported `type` plus positive integer `sentence`, or finite raw-time `start`/`end` with `0 <= start < end <= raw duration`. Use actual pause times for precise labels; sentence notes are approximate intentions. Phase10 notes: NO severity. Separate `human.annotation_labels` imports: `type:severity`, 1-5 required. Types: rushing, dragging, monotone, too_quiet, mumbling, awkward_pause, missing_pause.

**Consent:** YOU write nonempty `data/human/CONSENT.md` only if you agree: "I, <your name>, agree that my recordings may be published under CC BY 4.0." Wording is not validated; no consent is created for you.

**Pause check:** both gaps are inside one unit, with no punctuation between adjacent words. Human matching has no punctuation gate: same type, primary IoU >=0.3; historical pause-centre <=0.25 s reported separately. Detector comparison needs adjacent mapped words, not guaranteed flags. Synthetic injection rejects `larger | sense,` due to the following comma; it is NOT the human matcher.

