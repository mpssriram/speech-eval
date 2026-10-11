# Recorder-supplied notes

Recorder confirmation, 2026-10-12. This first JSON block supersedes the old
incomplete prose and the manual TAKES_REVIEW confirmation requirement.
Canonical unit numbering and localized spans are fixed before results in
`data/human/review/CONFIRMED_PROTOCOL.md`. Labels are recorder-confirmed intended
flaws, not independently listened-to annotations. No severity is invented.

```json
{"takes": {
"gettysburg__user__take01": {"flaws": [], "slips": "Natural reading. Repeated some words near 'government' (unit 10)."},
"gettysburg__user__take02": {"flaws": [{"type":"rushing","sentence":4},{"type":"awkward_pause","sentence":6},{"type":"too_quiet","sentence":8}], "slips": "Slip on 'or' in unit 2 (said 'that nation, any nation'). Unit 9: said 'they have who have fought' instead of 'they who fought'."},
"gettysburg__user__take03": {"flaws": [{"type":"monotone","sentence":2},{"type":"mumbling","sentence":7},{"type":"missing_pause","sentence":8},{"type":"dragging","sentence":9}], "slips": "Unintended slowing at 'have thus far' (unit 9), labelled dragging because it happened. 'died' (unit 10) mispronounced."},
"reagan_challenger__user__take01": {"flaws": [], "slips": "Natural reading. Mispronounced 'terrible' (unit 6) and 'truths' (unit 17). Unit 16: said 'the' for 'that' before 'special spirit', then corrected."},
"reagan_challenger__user__take02": {"flaws": [{"type":"rushing","sentence":10},{"type":"too_quiet","sentence":15},{"type":"awkward_pause","sentence":16}], "slips": "No slips."},
"reagan_challenger__user__take03": {"flaws": [{"type":"monotone","sentence":6},{"type":"mumbling","sentence":9},{"type":"missing_pause","sentence":14}], "slips": "No slips."},
"gettysburg__user__take04": {"flaws": null, "slips": "NOT SPECIFIED", "excluded_from_scoring": true, "exclusion_reason": "Spontaneous mixed reading; delivery flaws unknown."},
"reagan_challenger__user__take04": {"flaws": null, "slips": "No slips.", "excluded_from_scoring": true, "exclusion_reason": "Spontaneous mixed reading; delivery flaws unknown."}
}}
```

## Historical prose (superseded by confirmation above)

The following wording was supplied by the recorder in chat, not inferred from
ASR, listening or detector output. The recorder confirmed global takes 01–04
are Gettysburg 01–04, and 05–08 are Reagan Challenger 01–04. Machine-readable
delivery-flaw labels remain incomplete; this is not yet validator-ready JSON.

> For take 01: slips are repeating near the government. There are some repetiton of words in it.
> For take 02 :  slip in (or) in line 2. Slip in line 9 they who have fought was told but that was no correct.
> For take 03: Slowed near have thus far in the voice. Died was not prounced properly
> For take 05: Pronunciation near Terrible and truths is bad and near that special spirit it was told as the or it was later corrected
> For take 06: No issues

Additional recorder wording, in response to a question about takes 04, 07 and 08:

> yes, the flaws are random but i felt they were good ot me.

No flaw type, timing, severity or clean-take declaration is inferred from that
statement. Repetitions and pronunciation slips are not automatically relabelled
as the detector's delivery-flaw types. Global take06's "No issues" is the
recorder's statement about Reagan take02, not an independent rater response.
