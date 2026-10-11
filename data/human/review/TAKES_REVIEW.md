# Eight takes: recorder review required

Historical review sheet: superseded by the recorder's explicit chat confirmation
on 2026-10-12. Do not require/edit CONFIRMED markers here. The active fixed rules
and supplied notes are in CONFIRMED_PROTOCOL.md and ../raw/notes.md; generated
transcripts follow the recorder's canonical/ASR rule, not independent listening.

ASR is a suggestion, not ground truth. No listening, annotation confirmation or ratings are claimed.
Reference columns come only from canonical files, never lv_fb. Bold marks a WORD difference suggested by ASR, not a confirmed slip; punctuation/case-only differences are ignored.
Word spans below are one-based REFERENCE whitespace-word indices excluding punctuation-only tokens, not final as-spoken/MFA indices or measured flaw boundaries.

## How to finish

For each take: listen yourself, correct its editable transcript block (keep repetitions/slips and intended sentence punctuation), and replace `flaws: null` with your actual delivery-flaw list. Use `[]` only if you explicitly mean no delivery flaws. Unspecified is not clean.
Supported types: rushing, dragging, monotone, too_quiet, mumbling, awkward_pause, missing_pause. Notes severity is not required. For localized pauses/trailing phrases, raw seconds are more precise than a whole-sentence label.
Example FORMAT only, not your annotation: {"type":"awkward_pause","start":12.3,"end":14.3}. Alternatively use {"type":"rushing","sentence":4}, with one-based numbering from your CORRECTED transcript, not necessarily the canonical numbering below.
Edit the slips field too. Only after reviewing both transcript and notes, write a line containing exactly `CONFIRMED` under that take. Do not confirm an unknown flaw list. Tell Codex when done; it can then transfer ONLY your confirmed text/notes to `data/human/transcripts/{take_id}.txt` and `data/human/raw/notes.md` and validate before real MFA.
Actual consent already exists in `data/human/CONSENT.md`; no CC BY publication grant is inferred. Nothing here overwrites consent, notes or transcripts. The PDF is a plan, not evidence that a flaw was performed.

Sentence numbering uses the real `sentence_units` splitter: each `.`, `!`, `?`
or `;` ends a unit; a colon ends a unit when followed by whitespace and an
uppercase letter. Closing quote marks belong to that unit. Reagan's semicolon
and "heroes:" therefore split units. ASR punctuation is only a guess: correct
it too. Do not insert ellipses to represent a pause, as they create extra units.
If corrected wording changes numbering, use actual raw-time spans or ask Codex
to print the corrected splitter numbering before using sentence-based notes.

The per-take notes blocks below are review forms, NOT direct validator inputs.
After confirmation, remove `take_id` from each block and combine them as a
dictionary keyed by that ID, inside one `takes` object in the FIRST fenced JSON
block in `data/human/raw/notes.md`. Format skeleton only, intentionally invalid
until completed (do not copy null/placeholder IDs as final annotations):

```json
{"takes": {"<take_id>": {"flaws": null, "slips": "your confirmed description"}}}
```

Validate WITHOUT running MFA/detection, after the confirmed inputs are saved:

```sh
cd ~/speech-eval
env -u PYTHONPATH ~/.local/bin/uv run python -c 'from pathlib import Path; from speecheval.human_takes import validate_human_inputs; cases, notes = validate_human_inputs(Path.cwd()); print("Validated takes:", len(cases))'
```

Only after validation and all requested confirmations, run the existing Phase10
driver with the live dashboard at port 8080:

```sh
env -u PYTHONPATH ~/.local/bin/uv run python scripts/analyze_human.py --base-url http://localhost:8080 --dashboard-url http://localhost:8080
```

That existing driver is v1 only; separately labelled frozen v2 output still
requires the requested workflow extension. Do not claim this command runs v2.
The spontaneous 04/08 wording below is the latest recorder chat clarification;
the earlier prose notes file has not been edited or silently completed.

Gettysburg uses all 10 canonical units. Reagan uses units 1–17, from "Ladies and gentlemen" through "discover its truths." Confirm what you actually recorded if different.

## Sources

`data/transcripts/canonical/gettysburg.txt`; `data/transcripts/canonical/reagan_challenger.txt`; unconfirmed `data/human/asr_drafts/*.txt`; actual prose `data/human/raw/notes.md`; recorder chat clarification; supplied nine-page recording sheet (planned instructions only).

## gettysburg__user__take01 (global take 01)

Status: NOT CONFIRMED

Raw recording: `data/human/raw/gettysburg__user__take01.wav`
ASR source SHA256: `ce00ef11bd36dce90f982be33e724d3fdc502bd5ba9e443a06af8b821a4b7a61`

### Recorder-reported notes (not inferred from ASR)

> For take 01: slips are repeating near the government. There are some repetiton of words in it.

Reported phrase locations in the reference (NOT confirmed as-spoken spans):

- "government": canonical unit 10, reference words 256–256. Description is recorder-reported; not an automatically assigned delivery-flaw label.

### PDF plan ONLY — confirm what actually happened

The PDF planned a natural reading; your reported slips remain separate. Natural intent is not confirmed absence of delivery flaws.

### Reference next to ASR suggestions

Automatic word matching assigns the ASR excerpt to a reference unit; row grouping itself may be wrong. Use the complete editable draft below as the transcription source to correct.

| Canonical unit | Canonical reference (bold differences) | Unconfirmed ASR guess (bold differences) |
|---:|---|---|
| 1 | Four score and seven years ago our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated to the proposition that all men are created equal. | Four score and seven years ago, our fathers brought forth on this continent a new nation conceived in liberty and dedicated to the proposition that all men are created equal. |
| 2 | Now we are engaged in a great civil war, testing whether that nation, or any nation so conceived and so dedicated, can long endure. | Now we are engaged in a great civil war testing whether that nation or any nation so conceived and so dedicated can long endure. |
| 3 | We are met on a great battle-field of that war. | We are met on a great battlefield of that war. |
| 4 | We have come to dedicate a portion of that field, as a final resting place for those who here gave their lives that **that** nation might **live.** | We have come to dedicate a portion of that field as a final resting place for those who here gave their lives that **the** nation might **leave.** |
| 5 | It is **altogether** fitting and proper that we should do this. | It is **all** **to** **get** **a** fitting and proper that we should do this. |
| 6 | But, in a larger sense, we **can** **not** dedicate -- we **can** **not** **consecrate** -- we **can** **not** hallow -- this ground. | But in a larger sense, we **cannot** dedicate, we **cannot** **concentrate,** we **cannot** hallow this ground. |
| 7 | The brave men, living and dead, who **struggled** here, have **consecrated** it, far above our poor power to add or detract. | The brave men, living and dead, who **struggle** here, have **concentrated** it far above our poor power to add or detract. |
| 8 | The world will little note, nor long remember what we say here, but it can never forget what they did here. | The world will little note nor long remember what we say here, but it can never forget what they did here. |
| 9 | It is for us the living, rather, to be dedicated here to the unfinished work which they who **fought** here have thus far so nobly advanced. | It is for us, the living, rather to be dedicated here to the unfinished work which they who **brought** here have thus far so nobly advanced. |
| 10 | It is rather for us to be here dedicated to the great task remaining before us -- that from **these** **honored** dead we take increased devotion to that cause for which they gave the last full measure of devotion -- that we here highly **resolve** that **these** dead shall not **have** **died** in vain -- that this nation, **under** God, shall have a new birth of freedom -- and that government of the people, by the people, for the people, shall not perish from the earth. | It is rather for us to be here dedicated to the great task remaining before us, that from **this** **honor** dead we **can** take increased devotion to that cause for which they gave the last full measure of devotion, that we here highly **receive** that **this** dead shall not **die** in vain, that this nation **and** **the** God shall have a new birth of freedom, and that government of the people by the people for the people shall not perish from the earth. |

### Editable as-spoken transcript — correct this yourself

```text
Four score and seven years ago, our fathers brought forth on this continent a new nation conceived in liberty and dedicated to the proposition that all men are created equal. Now we are engaged in a great civil war testing whether that nation or any nation so conceived and so dedicated can long endure. We are met on a great battlefield of that war. We have come to dedicate a portion of that field as a final resting place for those who here gave their lives that the nation might leave. It is all to get a fitting and proper that we should do this. But in a larger sense, we cannot dedicate, we cannot concentrate, we cannot hallow this ground. The brave men, living and dead, who struggle here, have concentrated it far above our poor power to add or detract. The world will little note nor long remember what we say here, but it can never forget what they did here. It is for us, the living, rather to be dedicated here to the unfinished work which they who brought here have thus far so nobly advanced. It is rather for us to be here dedicated to the great task remaining before us, that from this honor dead we can take increased devotion to that cause for which they gave the last full measure of devotion, that we here highly receive that this dead shall not die in vain, that this nation and the God shall have a new birth of freedom, and that government of the people by the people for the people shall not perish from the earth.
```

### Editable actual notes — null MUST be replaced before confirmation

```json
{
  "take_id": "gettysburg__user__take01",
  "flaws": null,
  "slips": "For take 01: slips are repeating near the government. There are some repetiton of words in it."
}
```

Confirmation line: leave blank until you have checked everything.

---

## gettysburg__user__take02 (global take 02)

Status: NOT CONFIRMED

Raw recording: `data/human/raw/gettysburg__user__take02.wav`
ASR source SHA256: `90e35bc2cb622fa56d391201b3bf5983c91486d3d515f02fb6ce1a3d3ccf762b`

### Recorder-reported notes (not inferred from ASR)

> For take 02 :  slip in (or) in line 2. Slip in line 9 they who have fought was told but that was no correct.

Reported phrase locations in the reference (NOT confirmed as-spoken spans):

- "or": canonical unit 2, reference words 44–44. Description is recorder-reported; not an automatically assigned delivery-flaw label.
- "they who fought": canonical unit 9, reference words 180–182. Description is recorder-reported; not an automatically assigned delivery-flaw label.

### PDF plan ONLY — confirm what actually happened

- rushing: canonical unit 4, reference words 65–91. NOT confirmed as performed.
- awkward_pause: canonical unit 6, reference words 106–107, phrase-internal "larger | sense" (exact two-word boundary). NOT confirmed as performed.
- too_quiet: canonical unit 8, reference words 143–163, last few words only; exact words/times need your confirmation. NOT confirmed as performed.

### Reference next to ASR suggestions

Automatic word matching assigns the ASR excerpt to a reference unit; row grouping itself may be wrong. Use the complete editable draft below as the transcription source to correct.

| Canonical unit | Canonical reference (bold differences) | Unconfirmed ASR guess (bold differences) |
|---:|---|---|
| 1 | Four score and seven years ago our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated to the proposition that all men are created equal. | Four score and seven years ago, our fathers brought forth on this continent a new nation conceived in liberty and dedicated to the proposition that all men are created equal. |
| 2 | Now we are engaged in a great civil war, testing whether that nation, **or** any nation so conceived and so dedicated, can long endure. | Now we are engaged in a great civil war, testing whether that nation, any nation, so conceived and so dedicated can long endure. |
| 3 | We are met on a great battle-field of that war. | We are met on a great battlefield of that war. |
| 4 | We have come to **dedicate** a portion of that field, as a final resting place for those who here gave their lives **that** that nation might live. | We have come to a **dedicated** portion of that field as a final resting place for those who here gave their lives that nation might live. |
| 5 | It is altogether fitting and proper that we should do this. | It is altogether fitting and proper that we should do this. |
| 6 | But, in a larger sense, we **can** **not** dedicate -- we **can** **not** **consecrate** -- we **can** **not** hallow -- this ground. | But in a larger... sense we **cannot** dedicate we **cannot** **concentrate** we **cannot** hallow this ground |
| 7 | The brave men, living and dead, who **struggled** here, have **consecrated** it, far above our poor power to add or detract. | the brave men living and dead who **struggle** here have **concentrated** it far above our poor power to add or detract |
| 8 | The world will little note, nor long remember what we **say** here, but it can never forget what they did here. | the world will little note nor long remember what we **see** here but it can never forget what they did here |
| 9 | It is for us the living, rather, to be dedicated here to the unfinished work which they who fought here have thus far so nobly advanced. | it is for us the living rather to be dedicated here to the unfinished work which they **have** who **have** fought here have thus far so nobly advanced. |
| 10 | It is rather for us to be here dedicated to the great task remaining before us -- that **from** **these** **honored** dead we take increased devotion to that cause for which they gave the last full measure of devotion -- that we here highly **resolve** that **these** dead shall not have died in vain -- that this nation, under God, shall have a new birth of freedom -- and **that** government of the people, by the people, for the people, shall not perish from **the** earth. | It is rather for us to be here dedicated to the great task remaining before us, **from** that **this** **haunted** dead we take increased devotion to that cause for which they gave the last full measure of devotion, that we here highly **reclude** that **this** dead shall not have died in vain, that this nation under God shall have a new birth of freedom, and **the** government of the people, by the people, for the people, shall not perish from **this** earth. |

### Editable as-spoken transcript — correct this yourself

```text
Four score and seven years ago, our fathers brought forth on this continent a new nation conceived in liberty and dedicated to the proposition that all men are created equal. Now we are engaged in a great civil war, testing whether that nation, any nation, so conceived and so dedicated can long endure. We are met on a great battlefield of that war. We have come to a dedicated portion of that field as a final resting place for those who here gave their lives that nation might live. It is altogether fitting and proper that we should do this. But in a larger... sense we cannot dedicate we cannot concentrate we cannot hallow this ground the brave men living and dead who struggle here have concentrated it far above our poor power to add or detract the world will little note nor long remember what we see here but it can never forget what they did here it is for us the living rather to be dedicated here to the unfinished work which they have who have fought here have thus far so nobly advanced. It is rather for us to be here dedicated to the great task remaining before us, from that this haunted dead we take increased devotion to that cause for which they gave the last full measure of devotion, that we here highly reclude that this dead shall not have died in vain, that this nation under God shall have a new birth of freedom, and the government of the people, by the people, for the people, shall not perish from this earth.
```

### Editable actual notes — null MUST be replaced before confirmation

```json
{
  "take_id": "gettysburg__user__take02",
  "flaws": null,
  "slips": "For take 02 :  slip in (or) in line 2. Slip in line 9 they who have fought was told but that was no correct."
}
```

Confirmation line: leave blank until you have checked everything.

---

## gettysburg__user__take03 (global take 03)

Status: NOT CONFIRMED

Raw recording: `data/human/raw/gettysburg__user__take03.wav`
ASR source SHA256: `a30e650e96541f843742299684d8e68c031b7647d9752ae25d8e9e588886af21`

### Recorder-reported notes (not inferred from ASR)

> For take 03: Slowed near have thus far in the voice. Died was not prounced properly

Reported phrase locations in the reference (NOT confirmed as-spoken spans):

- "have thus far": canonical unit 9, reference words 184–186. Description is recorder-reported; not an automatically assigned delivery-flaw label.
- "died": canonical unit 10, reference words 239–239. Description is recorder-reported; not an automatically assigned delivery-flaw label.

### PDF plan ONLY — confirm what actually happened

- monotone: canonical unit 2, reference words 31–54. NOT confirmed as performed.
- mumbling: canonical unit 7, reference words 122–142. NOT confirmed as performed.
- missing_pause: canonical unit 8, reference words 143–163, join into unit 9. NOT confirmed as performed.

### Reference next to ASR suggestions

Automatic word matching assigns the ASR excerpt to a reference unit; row grouping itself may be wrong. Use the complete editable draft below as the transcription source to correct.

| Canonical unit | Canonical reference (bold differences) | Unconfirmed ASR guess (bold differences) |
|---:|---|---|
| 1 | Four score and seven years ago our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated to the proposition that all men are created equal. | Four score and seven years ago, our fathers brought forth on this continent a new nation conceived in liberty and dedicated to the proposition that all men are created equal. |
| 2 | Now we are engaged in a great civil war, testing whether that nation, or any nation so conceived and so dedicated, can long endure. | Now we are engaged in a great civil war testing whether that nation or any nation so conceived and so dedicated can long endure. |
| 3 | We are met on a great battle-field of that war. | We are met on a great battlefield of that war. |
| 4 | We have come to dedicate a portion of that field, as a final resting place for those who here gave their lives that **that** nation might live. | We have come to dedicate a portion of that field as a final resting place for those who here gave their lives that **the** nation might live. |
| 5 | It is altogether fitting and proper that we should do this. | It is altogether fitting and proper that we should do this. |
| 6 | But, in a larger sense, we **can** **not** dedicate -- we **can** **not** **consecrate** -- we **can** **not** hallow -- this ground. | but in a larger sense, we **cannot** dedicate, we **cannot** **concentrate,** we **cannot** hallow this ground. |
| 7 | The brave men, living and dead, who struggled here, have **consecrated** **it,** **far** **above** **our** poor power to add **or** **detract.** | The brave men, living and dead, who struggled here, have **concentrated** **its** **hard** **work** **or** poor power to add **to** **this** **track.** |
| 8 | The world will little note, nor long remember what we say here, but it can never forget what they did here. | The world will little note nor long remember what we say here, but it can never forget what they did here. |
| 9 | It is for us the living, rather, to be dedicated here to the unfinished work which they who fought here have thus far so nobly advanced. | It is for us, the living, rather to be dedicated here to the unfinished work which they, who fought here, have thus **so** far so nobly advanced |
| 10 | It is rather for us to be here dedicated to the great task remaining before us -- that from **these** **honored** dead we take increased devotion to that cause for which they gave the last full measure of devotion -- that we here highly **resolve** that these dead shall not have died **in** **vain** -- that this nation, under God, shall have a new birth of freedom -- and that government of the people, by the people, for the people, shall not perish from the earth. | it is rather for us to be here dedicated to the great task remaining before us that from **this** **haunted** dead we take increased devotion to that cause for which they gave the last full measure of devotion that we here highly **receive** **you** that these dead shall not have died **remain** that this nation under god shall have a new birth of freedom and that government of the people by the people for the people shall not perish from the earth |

### Editable as-spoken transcript — correct this yourself

```text
Four score and seven years ago, our fathers brought forth on this continent a new nation conceived in liberty and dedicated to the proposition that all men are created equal. Now we are engaged in a great civil war testing whether that nation or any nation so conceived and so dedicated can long endure. We are met on a great battlefield of that war. We have come to dedicate a portion of that field as a final resting place for those who here gave their lives that the nation might live. It is altogether fitting and proper that we should do this. but in a larger sense, we cannot dedicate, we cannot concentrate, we cannot hallow this ground. The brave men, living and dead, who struggled here, have concentrated its hard work or poor power to add to this track. The world will little note nor long remember what we say here, but it can never forget what they did here. It is for us, the living, rather to be dedicated here to the unfinished work which they, who fought here, have thus so far so nobly advanced it is rather for us to be here dedicated to the great task remaining before us that from this haunted dead we take increased devotion to that cause for which they gave the last full measure of devotion that we here highly receive you that these dead shall not have died remain that this nation under god shall have a new birth of freedom and that government of the people by the people for the people shall not perish from the earth
```

### Editable actual notes — null MUST be replaced before confirmation

```json
{
  "take_id": "gettysburg__user__take03",
  "flaws": null,
  "slips": "For take 03: Slowed near have thus far in the voice. Died was not prounced properly"
}
```

Confirmation line: leave blank until you have checked everything.

---

## gettysburg__user__take04 (global take 04)

Status: NOT CONFIRMED

Raw recording: `data/human/raw/gettysburg__user__take04.wav`
ASR source SHA256: `6f3b8245aa63d01b41d2edb4e0264bc79fc64ee53724f7507fbd8bab73c1ff71`

### Recorder-reported notes (not inferred from ASR)

> in take 04 and take 08 it is a mixed one that is the problem like i went with the flow

Spontaneous mixed reading, following the flow. Supported types and locations: UNSPECIFIED. No three-flaw plan or clean label is assigned.

Reported phrase locations in the reference (NOT confirmed as-spoken spans):

No specific phrase locations supplied.

### PDF plan ONLY — confirm what actually happened

No fixed performed types or locations are assigned.

### Reference next to ASR suggestions

Automatic word matching assigns the ASR excerpt to a reference unit; row grouping itself may be wrong. Use the complete editable draft below as the transcription source to correct.

| Canonical unit | Canonical reference (bold differences) | Unconfirmed ASR guess (bold differences) |
|---:|---|---|
| 1 | Four score and seven years ago our fathers brought forth on this continent, a new nation, conceived in Liberty, and dedicated to the proposition that all men are created equal. | Four score and seven years ago, our fathers brought forth on this continent a new nation conceived in liberty and dedicated to the proposition that all men are created equal. |
| 2 | Now we are engaged in a great civil war, testing whether that nation, or any nation so conceived and so dedicated, can long endure. | Now we are engaged in a great civil war testing whether that nation or any nation so conceived and so dedicated can long endure. |
| 3 | We are met on a great battle-field of that war. | We are met on a great battlefield of that war. |
| 4 | We have come to dedicate a portion of that field, as a final resting place for those who here gave their lives that **that** nation might live. | We have come to dedicate a portion of that field as a final resting place for those who here gave their lives that **the** nation might live. |
| 5 | **It** is altogether fitting and proper that we should do this. | is altogether fitting and proper that we should do this |
| 6 | But, in a **larger** sense, we **can** **not** dedicate -- we **can** **not** **consecrate** -- we **can** **not** hallow -- this **ground.** | but in a **large** sense we **cannot** dedicate we **cannot** **concentrate** we **cannot** hallow this **crowd** |
| 7 | The brave men, living and dead, who struggled here, have **consecrated** it, far above our poor power to **add** **or** detract. | the brave men living and dead who struggled here have **concentrated** it far above our poor power to **arrow** detract |
| 8 | The world will little **note,** nor long remember what we **say** here, but it can never forget what they did here. | the world will little **know** nor long remember what we **see** here but it can never forget what they did here |
| 9 | It is for us the living, rather, to be dedicated here to the unfinished work which they who fought here have thus far so nobly advanced. | it is for us the living rather to be dedicated here to the unfinished work which they who fought here have thus far so nobly advanced |
| 10 | It is rather for us to be here dedicated to the great task remaining before us -- that from **these** **honored** dead we take increased devotion to that cause for which they gave the **last** full measure of devotion -- that we here highly resolve that **these** dead shall not have died in vain -- that this nation, under God, shall have a new birth of freedom -- and that government of **the** people, by the people, for the people, shall not perish from the earth. | It is rather for us to be here. Dedicated to the great task. Remaining before us. That from **this** **haunted** dead. We take increased devotion. To that cause for which they gave. The full measure of devotion. That we here highly resolve. That **this** dead shall not have died in vain. That this nation under God. Shall have a new birth of freedom. And **the** **government.** That government of **that** people. By the people. For the people shall not perish from the earth. |

### Editable as-spoken transcript — correct this yourself

```text
Four score and seven years ago, our fathers brought forth on this continent a new nation conceived in liberty and dedicated to the proposition that all men are created equal. Now we are engaged in a great civil war testing whether that nation or any nation so conceived and so dedicated can long endure. We are met on a great battlefield of that war. We have come to dedicate a portion of that field as a final resting place for those who here gave their lives that the nation might live. is altogether fitting and proper that we should do this but in a large sense we cannot dedicate we cannot concentrate we cannot hallow this crowd the brave men living and dead who struggled here have concentrated it far above our poor power to arrow detract the world will little know nor long remember what we see here but it can never forget what they did here it is for us the living rather to be dedicated here to the unfinished work which they who fought here have thus far so nobly advanced It is rather for us to be here. Dedicated to the great task. Remaining before us. That from this haunted dead. We take increased devotion. To that cause for which they gave. The full measure of devotion. That we here highly resolve. That this dead shall not have died in vain. That this nation under God. Shall have a new birth of freedom. And the government. That government of that people. By the people. For the people shall not perish from the earth.
```

### Editable actual notes — null MUST be replaced before confirmation

```json
{
  "take_id": "gettysburg__user__take04",
  "flaws": null,
  "slips": "in take 04 and take 08 it is a mixed one that is the problem like i went with the flow"
}
```

Confirmation line: leave blank until you have checked everything.

---

## reagan_challenger__user__take01 (global take 05)

Status: NOT CONFIRMED

Raw recording: `data/human/raw/reagan_challenger__user__take01.wav`
ASR source SHA256: `c11a0b49052ce7ce73e445398dba66ce737beb7d0789bac0be498da6e5c91cb6`

### Recorder-reported notes (not inferred from ASR)

> For take 05: Pronunciation near Terrible and truths is bad and near that special spirit it was told as the or it was later corrected

Reported phrase locations in the reference (NOT confirmed as-spoken spans):

- "terrible": canonical unit 6, reference words 88–88. Description is recorder-reported; not an automatically assigned delivery-flaw label.
- "truths": canonical unit 17, reference words 237–237. Description is recorder-reported; not an automatically assigned delivery-flaw label.
- "that special spirit": canonical unit 16, reference words 211–213. Description is recorder-reported; not an automatically assigned delivery-flaw label.

### PDF plan ONLY — confirm what actually happened

The PDF planned a natural reading; your reported slips remain separate. Natural intent is not confirmed absence of delivery flaws.

### Reference next to ASR suggestions

Automatic word matching assigns the ASR excerpt to a reference unit; row grouping itself may be wrong. Use the complete editable draft below as the transcription source to correct.

| Canonical unit | Canonical reference (bold differences) | Unconfirmed ASR guess (bold differences) |
|---:|---|---|
| 1 | Ladies and gentlemen, **I'd** planned to speak to you tonight to report on the state of the Union, but the events of earlier today have led me to change those plans. | Ladies and gentlemen, **I** **have** planned to speak to you tonight to report on the State of the Union. But the events of earlier today have led me to change those plans. |
| 2 | Today is a day for mourning and remembering. | Today is a day for mourning and remembering. |
| 3 | Nancy and I are **pained** to the **core** by the tragedy of the shuttle Challenger. | Nancy and I are **paying** to the **code** by the tragedy of the Shuttle Challenger. |
| 4 | We know we share this pain with all **of** the people of our country. | We know we share this pain with all the people of our country. |
| 5 | This is truly a **national** loss. | This is truly a **nation's** loss. |
| 6 | Nineteen years ago, almost to the **day,** we lost three astronauts in a terrible accident on the ground. | 19 years ago, almost to the **date,** we lost three astronauts in a terrible accident on the ground. |
| 7 | But **we've** never lost an astronaut in flight; | But **we** never lost an astronaut in flight. |
| 8 | **we've** never had a tragedy like this. | **We** never had a tragedy like this. |
| 9 | And perhaps **we've** forgotten the courage it took for the crew of the shuttle. | And perhaps **we** **have** forgotten the courage it took for the crew of the shuttle. |
| 10 | But they, the Challenger Seven, were aware of the dangers, but overcame **them** and did their jobs brilliantly. | But they, the Challenger 7, were aware of the dangers, but overcame and did their jobs brilliantly. |
| 11 | We mourn seven heroes: | We mourn **the** seven heroes. |
| 12 | Michael Smith, Dick **Scobee,** **Judith** **Resnik,** Ronald McNair, Ellison Onizuka, Gregory Jarvis, and **Christa** McAuliffe. | Michael Smith, Dick **Scobie,** **Junot** **Rysnik,** Ronald McNair, Ellison Onizuka, Gregory Jarvis, and **Christian** McAuliffe. |
| 13 | We mourn their loss as a nation together. | We mourn their loss as a nation together. |
| 14 | For the families of the seven, we cannot bear, as you do, the full impact of this tragedy. | For the families of the seven, we cannot bear, as you do, the full impact of this tragedy. |
| 15 | But we feel the loss, and **we're** thinking about you so very much. | But we feel the loss and **we** **are** thinking about you so very much. |
| 16 | Your loved ones were daring and brave, and they had that special grace, **that** special spirit that **says,** ``Give me a challenge, and I'll meet it with joy.'' | Your loved ones were daring and brave and they had that special grace **and** **the** special spirit that **they** **say,** give me a challenge and I'll meet it with joy. |
| 17 | They had a hunger to explore the universe and discover its **truths.** | They had a hunger to explore the universe and discover its **truth.** |

### Editable as-spoken transcript — correct this yourself

```text
Ladies and gentlemen, I have planned to speak to you tonight to report on the State of the Union. But the events of earlier today have led me to change those plans. Today is a day for mourning and remembering. Nancy and I are paying to the code by the tragedy of the Shuttle Challenger. We know we share this pain with all the people of our country. This is truly a nation's loss. 19 years ago, almost to the date, we lost three astronauts in a terrible accident on the ground. But we never lost an astronaut in flight. We never had a tragedy like this. And perhaps we have forgotten the courage it took for the crew of the shuttle. But they, the Challenger 7, were aware of the dangers, but overcame and did their jobs brilliantly. We mourn the seven heroes. Michael Smith, Dick Scobie, Junot Rysnik, Ronald McNair, Ellison Onizuka, Gregory Jarvis, and Christian McAuliffe. We mourn their loss as a nation together. For the families of the seven, we cannot bear, as you do, the full impact of this tragedy. But we feel the loss and we are thinking about you so very much. Your loved ones were daring and brave and they had that special grace and the special spirit that they say, give me a challenge and I'll meet it with joy. They had a hunger to explore the universe and discover its truth.
```

### Editable actual notes — null MUST be replaced before confirmation

```json
{
  "take_id": "reagan_challenger__user__take01",
  "flaws": null,
  "slips": "For take 05: Pronunciation near Terrible and truths is bad and near that special spirit it was told as the or it was later corrected"
}
```

Confirmation line: leave blank until you have checked everything.

---

## reagan_challenger__user__take02 (global take 06)

Status: NOT CONFIRMED

Raw recording: `data/human/raw/reagan_challenger__user__take02.wav`
ASR source SHA256: `38f04cac198ebc73c513505380dd0ba6897cced6b9b436162eb2bbf17b248deb`

### Recorder-reported notes (not inferred from ASR)

> For take 06: No issues

Reported phrase locations in the reference (NOT confirmed as-spoken spans):

No specific phrase locations supplied.

### PDF plan ONLY — confirm what actually happened

- rushing: canonical unit 10, reference words 122–139. NOT confirmed as performed.
- too_quiet: canonical unit 15, reference words 185–197, last few words only; exact words/times need your confirmation. NOT confirmed as performed.
- awkward_pause: canonical unit 16, reference words 201–202, phrase-internal "were | daring" (exact two-word boundary). NOT confirmed as performed.
Your earlier "No issues" could mean no slips or no delivery flaws. Please clarify that scope. The PDF only describes planned actions; it does not establish that you performed any of them.

### Reference next to ASR suggestions

Automatic word matching assigns the ASR excerpt to a reference unit; row grouping itself may be wrong. Use the complete editable draft below as the transcription source to correct.

| Canonical unit | Canonical reference (bold differences) | Unconfirmed ASR guess (bold differences) |
|---:|---|---|
| 1 | Ladies and gentlemen, **I'd** planned to speak to you tonight to report on the state of the Union, but the events of earlier today have led me to change those plans. | Ladies and gentlemen, **I** **have** planned to speak to you tonight to report on the State of the Union, but the events of **the** earlier today have led me to change those plans. |
| 2 | Today is a day for mourning and remembering. | Today is a day for mourning and remembering. |
| 3 | Nancy and I are pained to the core by the tragedy of **the** **shuttle** **Challenger.** | Nancy and I are pained to the core by the tragedy of **this** **schedule** **challenging.** |
| 4 | We know we share this pain with all **of** the people of our country. | We know we share this pain with all the people of our country. |
| 5 | This is truly a **national** loss. | This is truly a **nation's** loss. |
| 6 | Nineteen years ago, almost to the day, we lost three astronauts in a terrible accident on the ground. | Nineteen years ago, almost to the day, we lost three astronauts in a terrible accident on the ground, |
| 7 | But **we've** never lost an astronaut in flight; | but **we** never lost an astronaut in **a** flight. |
| 8 | **we've** never had a tragedy like this. | **We** never had a tragedy like this. |
| 9 | **And** perhaps **we've** **forgotten** the courage it took for the crew of the shuttle. | Perhaps **we** **are** **forgetting** the courage it took for the crew of the shuttle. |
| 10 | But they, the Challenger Seven, were aware of **the** **dangers,** but overcame them and did their jobs brilliantly. | But they, the Challenger 7, were aware of **this** **danger,** but overcame them and did their jobs brilliantly. |
| 11 | We mourn seven heroes: | We mourn **the** seven heroes. |
| 12 | Michael Smith, Dick **Scobee,** **Judith** **Resnik,** Ronald McNair, **Ellison** Onizuka, Gregory Jarvis, and **Christa** McAuliffe. | Michael Smith, Dick **Scobie,** **Junot** **Riznik,** Ronald McNair, **Alison** Onizuka, Gregory Jarvis, and **Christina** McAuliffe. |
| 13 | We mourn their loss as a nation together. | We mourn their loss as a nation together. |
| 14 | For the families of the seven, we cannot bear, as you do, the full impact of this tragedy. | For the families of the seven, we cannot bear, as you do, the full impact of this tragedy. |
| 15 | But we feel the loss, and **we're** thinking about you so **very** much. | But we feel the loss and **we** **are** thinking about you so much. |
| 16 | Your loved ones were daring and brave, and they had that special grace, that special spirit that says, ``Give me a challenge, and I'll meet it with joy.'' | Your loved ones were daring and brave and they had that special grace, that special spirit that says, give me a challenge and I'll meet it with joy. |
| 17 | They had **a** hunger to explore the universe and discover its truths. | They had **the** hunger to explore the universe and discover its truths. |

### Editable as-spoken transcript — correct this yourself

```text
Ladies and gentlemen, I have planned to speak to you tonight to report on the State of the Union, but the events of the earlier today have led me to change those plans. Today is a day for mourning and remembering. Nancy and I are pained to the core by the tragedy of this schedule challenging. We know we share this pain with all the people of our country. This is truly a nation's loss. Nineteen years ago, almost to the day, we lost three astronauts in a terrible accident on the ground, but we never lost an astronaut in a flight. We never had a tragedy like this. Perhaps we are forgetting the courage it took for the crew of the shuttle. But they, the Challenger 7, were aware of this danger, but overcame them and did their jobs brilliantly. We mourn the seven heroes. Michael Smith, Dick Scobie, Junot Riznik, Ronald McNair, Alison Onizuka, Gregory Jarvis, and Christina McAuliffe. We mourn their loss as a nation together. For the families of the seven, we cannot bear, as you do, the full impact of this tragedy. But we feel the loss and we are thinking about you so much. Your loved ones were daring and brave and they had that special grace, that special spirit that says, give me a challenge and I'll meet it with joy. They had the hunger to explore the universe and discover its truths.
```

### Editable actual notes — null MUST be replaced before confirmation

```json
{
  "take_id": "reagan_challenger__user__take02",
  "flaws": null,
  "slips": "For take 06: No issues"
}
```

Confirmation line: leave blank until you have checked everything.

---

## reagan_challenger__user__take03 (global take 07)

Status: NOT CONFIRMED

Raw recording: `data/human/raw/reagan_challenger__user__take03.wav`
ASR source SHA256: `5aee7b2f96b6244c0bedac06b228609bd9a1d3b7dece2b84b057b5807e6882bb`

### Recorder-reported notes (not inferred from ASR)

> yes, the flaws are random but i felt they were good ot me.

Reported phrase locations in the reference (NOT confirmed as-spoken spans):

No specific phrase locations supplied.

### PDF plan ONLY — confirm what actually happened

- monotone: canonical unit 6, reference words 75–92. NOT confirmed as performed.
- mumbling: canonical unit 9, reference words 108–121. NOT confirmed as performed.
- missing_pause: canonical unit 14, reference words 167–184, join into unit 15. NOT confirmed as performed.

### Reference next to ASR suggestions

Automatic word matching assigns the ASR excerpt to a reference unit; row grouping itself may be wrong. Use the complete editable draft below as the transcription source to correct.

| Canonical unit | Canonical reference (bold differences) | Unconfirmed ASR guess (bold differences) |
|---:|---|---|
| 1 | Ladies and gentlemen, **I'd** planned to speak to you tonight to report on the state of the Union, but the events of earlier today have led me to change those plans. | Ladies and gentlemen, **I** **had** planned to speak to you tonight to report on the State of the Union. But the events of **the** earlier today have led me to change those plans. |
| 2 | Today is a day for mourning and remembering. | Today is a day for mourning and remembering. |
| 3 | Nancy and I are **pained** to the **core** by the tragedy of the shuttle Challenger. | Nancy and I are **pinned** to the **court** by the tragedy of the shuttle Challenger. |
| 4 | We know we **share** this pain with all of the people of our country. | We know we **shared** this pain with all of the people of our country. |
| 5 | This is truly a **national** loss. | This is truly a **nation's** loss. |
| 6 | Nineteen years ago, almost to the day, we lost three astronauts in a terrible accident on the ground. | Nineteen years ago, almost to the day, we lost three astronauts in a terrible accident on the ground. |
| 7 | **But** **we've** never lost an astronaut in flight; | **We** never lost an astronaut in **a** flight. |
| 8 | **we've** never had a tragedy like this. | **We** never had a tragedy like this. |
| 9 | **And** **perhaps** **we've** **forgotten** **the** **courage** **it** **took** **for** **the** **crew** **of** **the** **shuttle.** | (ASR omitted / no match) |
| 10 | But they, the Challenger Seven, were aware of the dangers, but overcame them and did their jobs brilliantly. | But they, the Challenger Seven, were aware of the dangers, but overcame them and did their jobs brilliantly. |
| 11 | We mourn seven heroes: | We mourn **the** seven heroes, |
| 12 | Michael Smith, Dick **Scobee,** **Judith** **Resnik,** Ronald McNair, **Ellison** Onizuka, Gregory Jarvis, and **Christa** McAuliffe. | Michael Smith, Dick **Scobie,** **Junior** **Resnick,** Ronald McNair, **Alison** Onizuka, Gregory Jarvis, and **Christina** McAuliffe. |
| 13 | We mourn their loss as a nation together. | We mourn their loss as a nation together. |
| 14 | For the families of the seven, we cannot bear, as you do, the full impact of this tragedy. | For the families of the seven, we cannot bear, as you do, the full impact of this tragedy, |
| 15 | But we feel the loss, and **we're** thinking about you so **very** much. | but we feel the loss and **we** **are** thinking about you so much. |
| 16 | Your loved ones were daring and brave, and they had that special grace, that special spirit that says, ``Give me a challenge, and I'll meet it with joy.'' | Your loved ones were daring and brave, and they had that special grace, that special spirit that says, give me a challenge and I'll meet it with joy. |
| 17 | They had a hunger to explore the universe and discover its truths. | They had a hunger to explore the universe and discover its truths. |

### Editable as-spoken transcript — correct this yourself

```text
Ladies and gentlemen, I had planned to speak to you tonight to report on the State of the Union. But the events of the earlier today have led me to change those plans. Today is a day for mourning and remembering. Nancy and I are pinned to the court by the tragedy of the shuttle Challenger. We know we shared this pain with all of the people of our country. This is truly a nation's loss. Nineteen years ago, almost to the day, we lost three astronauts in a terrible accident on the ground. We never lost an astronaut in a flight. We never had a tragedy like this. But they, the Challenger Seven, were aware of the dangers, but overcame them and did their jobs brilliantly. We mourn the seven heroes, Michael Smith, Dick Scobie, Junior Resnick, Ronald McNair, Alison Onizuka, Gregory Jarvis, and Christina McAuliffe. We mourn their loss as a nation together. For the families of the seven, we cannot bear, as you do, the full impact of this tragedy, but we feel the loss and we are thinking about you so much. Your loved ones were daring and brave, and they had that special grace, that special spirit that says, give me a challenge and I'll meet it with joy. They had a hunger to explore the universe and discover its truths.
```

### Editable actual notes — null MUST be replaced before confirmation

```json
{
  "take_id": "reagan_challenger__user__take03",
  "flaws": null,
  "slips": "yes, the flaws are random but i felt they were good ot me."
}
```

Confirmation line: leave blank until you have checked everything.

---

## reagan_challenger__user__take04 (global take 08)

Status: NOT CONFIRMED

Raw recording: `data/human/raw/reagan_challenger__user__take04.wav`
ASR source SHA256: `e719709c60e29f6fbac8faa7fec8e0ae8afee5eb7d9e4417ccbe3a02cf66cfd2`

### Recorder-reported notes (not inferred from ASR)

> in take 04 and take 08 it is a mixed one that is the problem like i went with the flow

Spontaneous mixed reading, following the flow. Supported types and locations: UNSPECIFIED. No three-flaw plan or clean label is assigned.

Reported phrase locations in the reference (NOT confirmed as-spoken spans):

No specific phrase locations supplied.

### PDF plan ONLY — confirm what actually happened

No fixed performed types or locations are assigned.

### Reference next to ASR suggestions

Automatic word matching assigns the ASR excerpt to a reference unit; row grouping itself may be wrong. Use the complete editable draft below as the transcription source to correct.

| Canonical unit | Canonical reference (bold differences) | Unconfirmed ASR guess (bold differences) |
|---:|---|---|
| 1 | Ladies and gentlemen, **I'd** planned to speak to you tonight to report on the state of the Union, but the events of earlier today have led me to change those plans. | Ladies and gentlemen, **I** **had** planned to speak to you tonight to report on the State of the Union, but the events of **the** earlier today have led me to change those plans. |
| 2 | Today is a day for mourning and remembering. | Today is a day for mourning and remembering. |
| 3 | Nancy and I are **pained** to the **core** by the tragedy of the **shuttle** Challenger. | Nancy and I are **paying** to the **court** by the tragedy of the **Churchill** Challenger. |
| 4 | We know we share this pain with all of the people of our country. | We know we share this pain with all of the people of our country. |
| 5 | This is truly a **national** loss. | This is truly a **nation's** loss. |
| 6 | Nineteen years ago, almost to the day, we lost three astronauts in a terrible accident on the ground. | 19 years ago, almost to the day, we lost three astronauts in a terrible accident on the ground. |
| 7 | But **we've** never lost an astronaut in flight; | but **we** never lost an astronaut in **a** flight. |
| 8 | **we've** never had a tragedy like this. | **We** never had a tragedy like this, |
| 9 | And perhaps **we've** forgotten the courage it took for the crew of the shuttle. | and perhaps **we** **have** forgotten the courage it took for the crew of the shuttle. |
| 10 | But they, the Challenger Seven, were aware of the dangers, but overcame them and did their jobs brilliantly. | But they, the Challenger 7, were aware of the dangers, but overcame them and did their jobs brilliantly. |
| 11 | We mourn seven heroes: | We mourn **the** seven heroes, |
| 12 | Michael Smith, Dick **Scobee,** **Judith** **Resnik,** Ronald McNair, **Ellison** Onizuka, Gregory Jarvis, and **Christa** McAuliffe. | Michael Smith, Dick **Scobie,** **Junot** **Resnick,** Ronald McNair, **Alison** Onizuka, Gregory Jarvis, and **Christina** McAuliffe. |
| 13 | We mourn their loss as a nation together. | We mourn their loss as a nation together. |
| 14 | For the families of the seven, we cannot bear, as you do, the full impact of this tragedy. | For the families of the seven, We cannot bear, as you do, the full impact of this tragedy, |
| 15 | But we feel the loss, and **we're** thinking about you so **very** much. | but we feel the loss and **we** **are** thinking about you so much. |
| 16 | Your loved ones were daring and brave, and they had that special grace, that special spirit that says, ``Give me a challenge, and I'll meet it with joy.'' | Your loved ones were daring and brave, and they had that special grace, that special spirit that says, give me a challenge and I'll meet it with joy. |
| 17 | They had a hunger to explore the universe and discover its truths. | They had a hunger to explore the universe and discover its truths. |

### Editable as-spoken transcript — correct this yourself

```text
Ladies and gentlemen, I had planned to speak to you tonight to report on the State of the Union, but the events of the earlier today have led me to change those plans. Today is a day for mourning and remembering. Nancy and I are paying to the court by the tragedy of the Churchill Challenger. We know we share this pain with all of the people of our country. This is truly a nation's loss. 19 years ago, almost to the day, we lost three astronauts in a terrible accident on the ground. but we never lost an astronaut in a flight. We never had a tragedy like this, and perhaps we have forgotten the courage it took for the crew of the shuttle. But they, the Challenger 7, were aware of the dangers, but overcame them and did their jobs brilliantly. We mourn the seven heroes, Michael Smith, Dick Scobie, Junot Resnick, Ronald McNair, Alison Onizuka, Gregory Jarvis, and Christina McAuliffe. We mourn their loss as a nation together. For the families of the seven, We cannot bear, as you do, the full impact of this tragedy, but we feel the loss and we are thinking about you so much. Your loved ones were daring and brave, and they had that special grace, that special spirit that says, give me a challenge and I'll meet it with joy. They had a hunger to explore the universe and discover its truths.
```

### Editable actual notes — null MUST be replaced before confirmation

```json
{
  "take_id": "reagan_challenger__user__take04",
  "flaws": null,
  "slips": "in take 04 and take 08 it is a mixed one that is the problem like i went with the flow"
}
```

Confirmation line: leave blank until you have checked everything.

---
