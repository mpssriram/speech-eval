# Speech-eval dataset card

Status: all eligible sources, stage `all`. Human takes, consent and labels are PENDING; Dataset v1 is not fully accepted or tagged.

## Purpose and contrastive design

English speech delivery, not content quality. Same-text clean and synthetically flawed recordings support graded, temporally grounded comparisons.

## Sources and supplied license evidence

| Source | License metadata | Evidence |
|---|---|---|
| lv_gettysburg_150 | Public domain (LibriVox recording; text by Lincoln, d. 1865) | https://librivox.org/pages/public-domain/ |
| lv_o_captain | Public domain (LibriVox recording; text by Whitman, d. 1892) | https://librivox.org/pages/public-domain/ |
| jfk_rice_1962 | Public domain (prepared by US officials as part of official duties) | https://www.jfklibrary.org/asset-viewer/archives/jfkwha-127-002 |
| reagan_challenger_1986 | Public domain (NARA presidential record) — page does not state it explicitly; confirm before publishing | https://www.reaganlibrary.gov/archives/audio/remarks-president-reagan-during-address-nation-space-shuttle-challenger-oval-office |
| jfk_inaugural_1961 | TO CONFIRM on page | https://www.jfklibrary.org/asset-viewer/archives/usg-17 |
| eleanor_roosevelt_1948 | CC0 1.0 (Internet Archive item, FDR Library material) | https://archive.org/details/gov.fdr.309 |
| obama_selma_2015 | Government-produced material, not copyright protected | https://obamawhitehouse.archives.gov/copyright |
| harris_vp_tbd | Government-produced material, not copyright protected | https://bidenwhitehouse.archives.gov/copyright/ |

## Construction

Source audio remains untouched. Prepared mono PCM16 HQ audio is 44.1 kHz, with 16 kHz alignment copies. Source excerpts and transcripts retain Phase 1 provenance. Feature normalisation never changes stored audio.
Injection sites are seeded contiguous 4–12-word within-sentence regions or eligible boundaries, with one-second edge keep-outs. Unknown words are excluded from required evidence. Two mixed files per source contain three distinct effects separated by at least two seconds when eligible sites exist.
Tempo uses Rubber Band fine mode; pitch-range compression uses Praat PSOLA; quietness uses gain envelopes; pauses use looped room tone or central removal with a 30 ms minimum; muffling uses a zero-phase fourth-order Butterworth filter plus gain. Crossfades and common HQ/16 kHz peak attenuation are recorded.
Oracle timestamps use monotone piecewise-linear source-to-flawed maps. The detector MUST use separately computed real MFA alignments and their features. Full-utterance MFA inference uses transcripts, not oracle boundaries. Sentence membership is recovered from text word indices.

| Type | Parameter | Severities 1–5 |
|---|---|---|
| rushing | speed_factor | [1.15, 1.3, 1.5, 1.75, 2.0] |
| dragging | speed_factor | [0.87, 0.77, 0.67, 0.58, 0.5] |
| monotone | pitch_range_kept | [0.7, 0.5, 0.35, 0.2, 0.08] |
| too_quiet | gain_db | [-3, -6, -9, -12, -18] |
| awkward_pause | inserted_pause_s | [0.6, 1.0, 1.5, 2.2, 3.0] |
| missing_pause | pause_kept_frac | [0.7, 0.5, 0.3, 0.15, 0.0] |
| mumbling | lowpass_hz | [3500, 2800, 2200, 1700, 1300] |

## Labels

`labels/v1` stores recording/reference/text IDs, source=synthetic, and flaw type, severity, flawed-timeline start/end, inclusive word bounds and exact parameters. Mixed files contain three flaw entries. Human labels will be explicitly source=human and must not be inferred from intended instructions.

## Splits and evaluation

Sources: 18 train, 4 dev, 7 test. Speaker membership is frozen in configs/splits.yaml. Excluded: {'o_captain__lv_rg__orig': 'clipped source samples'}.
A-LOSO compares Gettysburg/O Captain against other train readers, excluding the source speaker. B-same-speaker uses original JFK/Reagan recordings. C uses good-speaker norms without same-text reference. Test speakers never calibrate thresholds or reference statistics. Human evaluation is pending.

## Observed composition

1103 HQ audio files, 1073 synthetic; 36.263 hours (16 kHz copies are not double-counted).

| Text | Split | Kind | Files |
|---|---|---|---:|
| gettysburg | dev | source | 2 |
| gettysburg | dev | synthetic | 74 |
| gettysburg | test | source | 3 |
| gettysburg | test | synthetic | 111 |
| gettysburg | train | source | 10 |
| gettysburg | train | synthetic | 370 |
| jfk_rice | test | source | 1 |
| jfk_rice | test | synthetic | 37 |
| o_captain | dev | source | 2 |
| o_captain | dev | synthetic | 74 |
| o_captain | excluded | source | 1 |
| o_captain | test | source | 2 |
| o_captain | test | synthetic | 74 |
| o_captain | train | source | 8 |
| o_captain | train | synthetic | 296 |
| reagan_challenger | test | source | 1 |
| reagan_challenger | test | synthetic | 37 |

| Text | Split | Type | Severity | Events |
|---|---|---|---:|---:|
| gettysburg | dev | awkward_pause | 1 | 2 |
| gettysburg | dev | awkward_pause | 2 | 3 |
| gettysburg | dev | awkward_pause | 3 | 2 |
| gettysburg | dev | awkward_pause | 4 | 2 |
| gettysburg | dev | awkward_pause | 5 | 3 |
| gettysburg | dev | dragging | 1 | 2 |
| gettysburg | dev | dragging | 2 | 3 |
| gettysburg | dev | dragging | 3 | 2 |
| gettysburg | dev | dragging | 4 | 2 |
| gettysburg | dev | dragging | 5 | 2 |
| gettysburg | dev | missing_pause | 1 | 2 |
| gettysburg | dev | missing_pause | 2 | 2 |
| gettysburg | dev | missing_pause | 3 | 3 |
| gettysburg | dev | missing_pause | 4 | 2 |
| gettysburg | dev | missing_pause | 5 | 2 |
| gettysburg | dev | monotone | 1 | 2 |
| gettysburg | dev | monotone | 2 | 2 |
| gettysburg | dev | monotone | 3 | 2 |
| gettysburg | dev | monotone | 4 | 4 |
| gettysburg | dev | monotone | 5 | 2 |
| gettysburg | dev | mumbling | 1 | 2 |
| gettysburg | dev | mumbling | 2 | 2 |
| gettysburg | dev | mumbling | 3 | 2 |
| gettysburg | dev | mumbling | 4 | 3 |
| gettysburg | dev | mumbling | 5 | 2 |
| gettysburg | dev | rushing | 1 | 2 |
| gettysburg | dev | rushing | 2 | 2 |
| gettysburg | dev | rushing | 3 | 3 |
| gettysburg | dev | rushing | 4 | 2 |
| gettysburg | dev | rushing | 5 | 3 |
| gettysburg | dev | too_quiet | 1 | 2 |
| gettysburg | dev | too_quiet | 2 | 4 |
| gettysburg | dev | too_quiet | 3 | 2 |
| gettysburg | dev | too_quiet | 4 | 2 |
| gettysburg | dev | too_quiet | 5 | 3 |
| gettysburg | test | awkward_pause | 1 | 3 |
| gettysburg | test | awkward_pause | 2 | 3 |
| gettysburg | test | awkward_pause | 3 | 5 |
| gettysburg | test | awkward_pause | 4 | 4 |
| gettysburg | test | awkward_pause | 5 | 5 |
| gettysburg | test | dragging | 1 | 3 |
| gettysburg | test | dragging | 2 | 3 |
| gettysburg | test | dragging | 3 | 3 |
| gettysburg | test | dragging | 4 | 5 |
| gettysburg | test | dragging | 5 | 3 |
| gettysburg | test | missing_pause | 1 | 3 |
| gettysburg | test | missing_pause | 2 | 3 |
| gettysburg | test | missing_pause | 3 | 3 |
| gettysburg | test | missing_pause | 4 | 4 |
| gettysburg | test | missing_pause | 5 | 3 |
| gettysburg | test | monotone | 1 | 3 |
| gettysburg | test | monotone | 2 | 3 |
| gettysburg | test | monotone | 3 | 3 |
| gettysburg | test | monotone | 4 | 4 |
| gettysburg | test | monotone | 5 | 5 |
| gettysburg | test | mumbling | 1 | 3 |
| gettysburg | test | mumbling | 2 | 3 |
| gettysburg | test | mumbling | 3 | 5 |
| gettysburg | test | mumbling | 4 | 3 |
| gettysburg | test | mumbling | 5 | 3 |
| gettysburg | test | rushing | 1 | 3 |
| gettysburg | test | rushing | 2 | 5 |
| gettysburg | test | rushing | 3 | 3 |
| gettysburg | test | rushing | 4 | 4 |
| gettysburg | test | rushing | 5 | 4 |
| gettysburg | test | too_quiet | 1 | 3 |
| gettysburg | test | too_quiet | 2 | 3 |
| gettysburg | test | too_quiet | 3 | 4 |
| gettysburg | test | too_quiet | 4 | 3 |
| gettysburg | test | too_quiet | 5 | 3 |
| gettysburg | train | awkward_pause | 1 | 10 |
| gettysburg | train | awkward_pause | 2 | 12 |
| gettysburg | train | awkward_pause | 3 | 10 |
| gettysburg | train | awkward_pause | 4 | 14 |
| gettysburg | train | awkward_pause | 5 | 10 |
| gettysburg | train | dragging | 1 | 10 |
| gettysburg | train | dragging | 2 | 11 |
| gettysburg | train | dragging | 3 | 13 |
| gettysburg | train | dragging | 4 | 13 |
| gettysburg | train | dragging | 5 | 11 |
| gettysburg | train | missing_pause | 1 | 10 |
| gettysburg | train | missing_pause | 2 | 14 |
| gettysburg | train | missing_pause | 3 | 14 |
| gettysburg | train | missing_pause | 4 | 13 |
| gettysburg | train | missing_pause | 5 | 13 |
| gettysburg | train | monotone | 1 | 10 |
| gettysburg | train | monotone | 2 | 13 |
| gettysburg | train | monotone | 3 | 13 |
| gettysburg | train | monotone | 4 | 10 |
| gettysburg | train | monotone | 5 | 13 |
| gettysburg | train | mumbling | 1 | 10 |
| gettysburg | train | mumbling | 2 | 10 |
| gettysburg | train | mumbling | 3 | 12 |
| gettysburg | train | mumbling | 4 | 11 |
| gettysburg | train | mumbling | 5 | 14 |
| gettysburg | train | rushing | 1 | 10 |
| gettysburg | train | rushing | 2 | 12 |
| gettysburg | train | rushing | 3 | 12 |
| gettysburg | train | rushing | 4 | 12 |
| gettysburg | train | rushing | 5 | 14 |
| gettysburg | train | too_quiet | 1 | 10 |
| gettysburg | train | too_quiet | 2 | 11 |
| gettysburg | train | too_quiet | 3 | 14 |
| gettysburg | train | too_quiet | 4 | 10 |
| gettysburg | train | too_quiet | 5 | 11 |
| jfk_rice | test | awkward_pause | 1 | 1 |
| jfk_rice | test | awkward_pause | 2 | 3 |
| jfk_rice | test | awkward_pause | 3 | 1 |
| jfk_rice | test | awkward_pause | 4 | 1 |
| jfk_rice | test | awkward_pause | 5 | 1 |
| jfk_rice | test | dragging | 1 | 1 |
| jfk_rice | test | dragging | 2 | 1 |
| jfk_rice | test | dragging | 3 | 1 |
| jfk_rice | test | dragging | 4 | 1 |
| jfk_rice | test | dragging | 5 | 1 |
| jfk_rice | test | missing_pause | 1 | 1 |
| jfk_rice | test | missing_pause | 2 | 2 |
| jfk_rice | test | missing_pause | 3 | 1 |
| jfk_rice | test | missing_pause | 4 | 1 |
| jfk_rice | test | missing_pause | 5 | 1 |
| jfk_rice | test | monotone | 1 | 1 |
| jfk_rice | test | monotone | 2 | 1 |
| jfk_rice | test | monotone | 3 | 2 |
| jfk_rice | test | monotone | 4 | 1 |
| jfk_rice | test | monotone | 5 | 2 |
| jfk_rice | test | mumbling | 1 | 1 |
| jfk_rice | test | mumbling | 2 | 1 |
| jfk_rice | test | mumbling | 3 | 2 |
| jfk_rice | test | mumbling | 4 | 1 |
| jfk_rice | test | mumbling | 5 | 1 |
| jfk_rice | test | rushing | 1 | 1 |
| jfk_rice | test | rushing | 2 | 1 |
| jfk_rice | test | rushing | 3 | 1 |
| jfk_rice | test | rushing | 4 | 1 |
| jfk_rice | test | rushing | 5 | 1 |
| jfk_rice | test | too_quiet | 1 | 1 |
| jfk_rice | test | too_quiet | 2 | 1 |
| jfk_rice | test | too_quiet | 3 | 1 |
| jfk_rice | test | too_quiet | 4 | 1 |
| jfk_rice | test | too_quiet | 5 | 1 |
| o_captain | dev | awkward_pause | 1 | 2 |
| o_captain | dev | awkward_pause | 2 | 3 |
| o_captain | dev | awkward_pause | 3 | 2 |
| o_captain | dev | awkward_pause | 4 | 2 |
| o_captain | dev | awkward_pause | 5 | 2 |
| o_captain | dev | dragging | 1 | 2 |
| o_captain | dev | dragging | 2 | 3 |
| o_captain | dev | dragging | 3 | 2 |
| o_captain | dev | dragging | 4 | 2 |
| o_captain | dev | dragging | 5 | 3 |
| o_captain | dev | missing_pause | 1 | 2 |
| o_captain | dev | missing_pause | 2 | 3 |
| o_captain | dev | missing_pause | 3 | 2 |
| o_captain | dev | missing_pause | 4 | 2 |
| o_captain | dev | missing_pause | 5 | 3 |
| o_captain | dev | monotone | 1 | 2 |
| o_captain | dev | monotone | 2 | 2 |
| o_captain | dev | monotone | 3 | 2 |
| o_captain | dev | monotone | 4 | 2 |
| o_captain | dev | monotone | 5 | 3 |
| o_captain | dev | mumbling | 1 | 2 |
| o_captain | dev | mumbling | 2 | 3 |
| o_captain | dev | mumbling | 3 | 3 |
| o_captain | dev | mumbling | 4 | 2 |
| o_captain | dev | mumbling | 5 | 3 |
| o_captain | dev | rushing | 1 | 2 |
| o_captain | dev | rushing | 2 | 4 |
| o_captain | dev | rushing | 3 | 2 |
| o_captain | dev | rushing | 4 | 2 |
| o_captain | dev | rushing | 5 | 2 |
| o_captain | dev | too_quiet | 1 | 2 |
| o_captain | dev | too_quiet | 2 | 2 |
| o_captain | dev | too_quiet | 3 | 3 |
| o_captain | dev | too_quiet | 4 | 2 |
| o_captain | dev | too_quiet | 5 | 2 |
| o_captain | test | awkward_pause | 1 | 2 |
| o_captain | test | awkward_pause | 2 | 3 |
| o_captain | test | awkward_pause | 3 | 2 |
| o_captain | test | awkward_pause | 4 | 2 |
| o_captain | test | awkward_pause | 5 | 2 |
| o_captain | test | dragging | 1 | 2 |
| o_captain | test | dragging | 2 | 2 |
| o_captain | test | dragging | 3 | 2 |
| o_captain | test | dragging | 4 | 2 |
| o_captain | test | dragging | 5 | 2 |
| o_captain | test | missing_pause | 1 | 2 |
| o_captain | test | missing_pause | 2 | 3 |
| o_captain | test | missing_pause | 3 | 3 |
| o_captain | test | missing_pause | 4 | 2 |
| o_captain | test | missing_pause | 5 | 3 |
| o_captain | test | monotone | 1 | 2 |
| o_captain | test | monotone | 2 | 4 |
| o_captain | test | monotone | 3 | 2 |
| o_captain | test | monotone | 4 | 2 |
| o_captain | test | monotone | 5 | 3 |
| o_captain | test | mumbling | 1 | 2 |
| o_captain | test | mumbling | 2 | 2 |
| o_captain | test | mumbling | 3 | 2 |
| o_captain | test | mumbling | 4 | 3 |
| o_captain | test | mumbling | 5 | 3 |
| o_captain | test | rushing | 1 | 2 |
| o_captain | test | rushing | 2 | 2 |
| o_captain | test | rushing | 3 | 3 |
| o_captain | test | rushing | 4 | 2 |
| o_captain | test | rushing | 5 | 2 |
| o_captain | test | too_quiet | 1 | 2 |
| o_captain | test | too_quiet | 2 | 2 |
| o_captain | test | too_quiet | 3 | 3 |
| o_captain | test | too_quiet | 4 | 2 |
| o_captain | test | too_quiet | 5 | 3 |
| o_captain | train | awkward_pause | 1 | 8 |
| o_captain | train | awkward_pause | 2 | 10 |
| o_captain | train | awkward_pause | 3 | 12 |
| o_captain | train | awkward_pause | 4 | 9 |
| o_captain | train | awkward_pause | 5 | 8 |
| o_captain | train | dragging | 1 | 8 |
| o_captain | train | dragging | 2 | 12 |
| o_captain | train | dragging | 3 | 8 |
| o_captain | train | dragging | 4 | 9 |
| o_captain | train | dragging | 5 | 8 |
| o_captain | train | missing_pause | 1 | 8 |
| o_captain | train | missing_pause | 2 | 10 |
| o_captain | train | missing_pause | 3 | 8 |
| o_captain | train | missing_pause | 4 | 10 |
| o_captain | train | missing_pause | 5 | 10 |
| o_captain | train | monotone | 1 | 8 |
| o_captain | train | monotone | 2 | 10 |
| o_captain | train | monotone | 3 | 12 |
| o_captain | train | monotone | 4 | 8 |
| o_captain | train | monotone | 5 | 9 |
| o_captain | train | mumbling | 1 | 8 |
| o_captain | train | mumbling | 2 | 9 |
| o_captain | train | mumbling | 3 | 11 |
| o_captain | train | mumbling | 4 | 10 |
| o_captain | train | mumbling | 5 | 9 |
| o_captain | train | rushing | 1 | 8 |
| o_captain | train | rushing | 2 | 9 |
| o_captain | train | rushing | 3 | 9 |
| o_captain | train | rushing | 4 | 12 |
| o_captain | train | rushing | 5 | 9 |
| o_captain | train | too_quiet | 1 | 8 |
| o_captain | train | too_quiet | 2 | 11 |
| o_captain | train | too_quiet | 3 | 9 |
| o_captain | train | too_quiet | 4 | 11 |
| o_captain | train | too_quiet | 5 | 10 |
| reagan_challenger | test | awkward_pause | 1 | 1 |
| reagan_challenger | test | awkward_pause | 2 | 1 |
| reagan_challenger | test | awkward_pause | 3 | 1 |
| reagan_challenger | test | awkward_pause | 4 | 1 |
| reagan_challenger | test | awkward_pause | 5 | 1 |
| reagan_challenger | test | dragging | 1 | 1 |
| reagan_challenger | test | dragging | 2 | 1 |
| reagan_challenger | test | dragging | 3 | 2 |
| reagan_challenger | test | dragging | 4 | 1 |
| reagan_challenger | test | dragging | 5 | 1 |
| reagan_challenger | test | missing_pause | 1 | 1 |
| reagan_challenger | test | missing_pause | 2 | 2 |
| reagan_challenger | test | missing_pause | 3 | 1 |
| reagan_challenger | test | missing_pause | 4 | 1 |
| reagan_challenger | test | missing_pause | 5 | 2 |
| reagan_challenger | test | monotone | 1 | 1 |
| reagan_challenger | test | monotone | 2 | 1 |
| reagan_challenger | test | monotone | 3 | 2 |
| reagan_challenger | test | monotone | 4 | 1 |
| reagan_challenger | test | monotone | 5 | 2 |
| reagan_challenger | test | mumbling | 1 | 1 |
| reagan_challenger | test | mumbling | 2 | 1 |
| reagan_challenger | test | mumbling | 3 | 1 |
| reagan_challenger | test | mumbling | 4 | 1 |
| reagan_challenger | test | mumbling | 5 | 1 |
| reagan_challenger | test | rushing | 1 | 1 |
| reagan_challenger | test | rushing | 2 | 2 |
| reagan_challenger | test | rushing | 3 | 1 |
| reagan_challenger | test | rushing | 4 | 1 |
| reagan_challenger | test | rushing | 5 | 1 |
| reagan_challenger | test | too_quiet | 1 | 1 |
| reagan_challenger | test | too_quiet | 2 | 1 |
| reagan_challenger | test | too_quiet | 3 | 1 |
| reagan_challenger | test | too_quiet | 4 | 1 |
| reagan_challenger | test | too_quiet | 5 | 1 |

## Known limitations and attributions

Synthetic parameter fidelity does not establish perceptual realism. LibriVox reading differs from oratory. English only. Human takes/ratings are missing. Gold boundaries were marked visually by Claude, without listening; the human spot-check is pending and neither aligner met the Phase 1 gold accuracy target. Uncertain word evidence is excluded. Real-vs-oracle errors and >60 ms risks are saved in data/review/dataset_alignment_qa.json.
Required source attributions: LibriVox, US government works and Internet Archive, with evidence links above. User voice must not be published without explicit consent.
