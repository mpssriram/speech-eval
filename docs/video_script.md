# Demo video script — target 6:30, maximum 10:00

Based on the supplied draft. Record real screen actions; never narrate pending
human/rater/pitch results as completed. Numbers come from linked result reports.

| Time | Segment | On screen |
|---|---|---|
| 0:00–0:30 | Problem | Title and dashboard |
| 0:30–2:00 | Dataset | Card and licensed synthetic preview |
| 2:00–4:00 | Live demo | Upload, region, explanation, phrase playback |
| 4:00–5:00 | Results | Frozen results and separate C comparison |
| 5:00–6:00 | Rehearsal workflow | Own takes only if available; otherwise labelled synthetic workflow |
| 6:00–6:30 | Limits/reproduction | README, hashes, pending actions |

## 0:00–0:30 — problem

“One score is not enough. Our system shows what delivery pattern differs, where
and why, with measured evidence. It compares deliveries, not content or an ideal
speaking-quality standard.”

## 0:30–2:00 — dataset

“Licensed public-domain speech in the USA: 15 Gettysburg readers, 13 O Captain,
plus Kennedy and Reagan. Eligible sources get seven controlled flaw types at
five edit strengths. The release has 1,103 indexed variants and
36.26268833333334 hours; duplicate rates are not counted again.”
[Counts](../reports/reproducibility.md).

Play weak/strong edits from the synthetic preview: “These are controlled edits,
not proof that people hear every severity as intended.” Do not claim barely
audible/obvious effects without listening evidence. Show splits and real/oracle separation.

## 2:00–4:00 — live demo

If consented own takes exist, show an actual Phase10 job/notes. Otherwise say:
“This is a licensed source or synthetic example, **not my recording**.” Browser-
verified `gettysburg__lv_mk__orig` has Mode A overall 9.4 and two regions.
[Browser evidence](../reports/phase09_ui.md).

Select a **detected** region, read the actual on-screen explanation, play Yours /
Baseline (same words). Do not promise detection of intended rushing: the workflow
fixture missed it. “dedicated to” plays in both; unavailable words disable baseline
playback. Report-only explanation fields remain pending: `{{p_rate}}`,
`{{r_rate}}`, `{{z}}`. Never invent them. “Measured rule explanation, not causal proof.”

## 4:00–5:00 — results

“Controlled same-text test recall is 0.400 and precision 0.125. The dev clean-alarm
guard failed: 1.777 per minute against maximum 0.5. Scores are not validated by
real raters yet.” [Phase6](../reports/phase06_results.md).

Show severity chart without unsupported pooled severity-4/5 rate (`{{r_sev45}}`
pending). No fabricated human scatter: “The pack is ready; independent ratings
are pending.” Show **paired sentence-level** C comparison: “Reference recall
0.324 versus no-reference 0.179, with more clean alarms. Controlled edits, not
human performance.” [Mode C](../reports/phase08_mode_c.md).

## 5:00–6:00 — rehearsal workflow

Show genuine Gettysburg take02 Mode B versus take01, job
`6d8cbd6dec22ffc8f7827ebc`. Select the larger|sense awkward pause at
29.90-31.47 s and show Yours / Baseline (same words) playback.
“This matches the pause I confirmed performing. It is not independent annotation
or proof of overall improvement. Across six scored takes, frozen v1 Mode A hit
4 of 13 labels with 77 unmatched flags; Mode B hit 3 of 13 with 60 unmatched flags.”
Both mixed take04s are unknown and excluded from scoring, not clean negatives.
[Phase10](../reports/phase10_human_takes.md).

## 6:00–6:30 — limits and reproduction

“Edits approximate real flaws. Our visual alignment reference was placed without
listening; no human spot-check was done. Human agreement was not measured: no
independent raters were available; no AI or self-ratings were used. C is heuristic. Fresh GitHub-clone
Docker reproduction matched 563 scientific outputs byte-for-byte twice. The
archive is built but public upload is pending; local import and hashes are documented.”
[Scope](../reports/reproducibility.md).

Before recording: author/name, archive `{{dataset_url}}` and video `{{video_url}}`;
genuine takes/ratings for any human-result segments. This is an evidence-labelled
engineering demo script, not a completed video or human-validation claim.
