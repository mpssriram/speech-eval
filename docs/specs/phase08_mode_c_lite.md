# Phase 8 spec — Mode C-lite: good-speaker norms and key-moment checks (no reference needed)

Read `AGENTS.md` and `docs/PLAN.md` first. Requires Phases 5–7. If time is short, apply cut line 1 in PLAN.md
(rate and sentence-end pause only).

## Goal

Evaluate **any** speech, such as an original investor pitch, without a recording of someone else saying the same words.
Instead of comparing word by word, compare each **sentence** against the distribution of how good speakers
deliver sentences in general, learned from our clean recordings.

Mode C is deliberately limited to 4 features. The report must state clearly that it is a weaker, more general mode than A.

## Step 1 — Build the norms (`speecheval norms build`) → `data/reference/norms_v1.json`

- Source: all **train-split** clean source recordings (sentence table from Phase 2).
- One row per sentence with ≥ 4 words. Features, with the same transforms as Phase 5:

| Norm key | Sentence column | Transform | Flags |
|---|---|---|---|
| `rate` | `articulation_rate_syl_s` | ln | rushing (+), dragging (−) |
| `pitchrange` | `f0_st_range` | ln(x + 0.5) | monotone (−) |
| `final_drop` | `final_int_drop_db` | none | trailing off → `too_quiet` (−) |
| `end_pause` | `pause_after_s` (non-final sentences only) | ln(x + 0.05) | missing_pause (−) |

- Store per feature: median, robust SD (1.4826 × MAD), the 5/25/50/75/95 percentiles, and n.
- Also store `rate` norms **per speaker** (median across that speaker's sentences), so the report can show the between-speaker spread.

## Step 2 — Mode C analysis (`speecheval analyze AUDIO --mode C --transcript FILE`)

A transcript is required. If none is given, run WhisperX ASR (CPU, fixed settings), save the transcript next to the analysis, and set `"transcript_source": "asr"` in the output.

For each sentence s with ≥ 4 words:

1. Compute the 4 features (Phase 2 code).
2. Compute z against the norms.
3. Flag using `configs/detector.yaml` → `mode_c.k` (default 2.0 for all four):
   - `rate` z ≥ k → `rushing` region = the sentence; z ≤ −k → `dragging`.
   - `pitchrange` z ≤ −k → `monotone` region = the sentence.
   - `final_drop` z ≤ −k → `too_quiet` region = the **last 2 words** of the sentence (trailing off).
   - `end_pause` z ≤ −k → `missing_pause` event at the sentence end.
4. Severity uses the Phase 6 calibrated bins. Explanations use the Phase 5 templates, with "good readers" replaced by "good speakers in our dataset (typical range {p25}–{p75})".

## Step 3 — Key-moment checks (heuristic, labelled as such)

Find key moments in the transcript:

- every sentence containing a number (digits, number words, %, ₹, $);
- the final sentence;
- the first sentence.

At each key moment, check:

| Check | Rule | Message |
|---|---|---|
| Slow down for numbers | local `rate` over the number word ±1 word ≤ the speaker's own median articulation rate × 1.0 | "You rushed your key figure '{words}' ({rate} vs your average {avg} syllables/s)." |
| Pause before the number | `pause_before` of the number's first word ≥ 0.15 s | "No pause before '{words}'. A short pause makes the number land." |
| Strong ending | final sentence `final_drop` ≥ −3 dB **and** `rate` z ≤ +1 | "Your final sentence trails off / is rushed." |

Output these as `key_moments` in the analysis (AGENTS.md §6.4), **not** as flaw regions, because they are heuristics, not statistically derived. Their thresholds live in `configs/detector.yaml → key_moments` and are documented as heuristics in the report.

Scores in Mode C use the same rubric; key moments do not change scores.

## Step 4 — Cost of no reference (`speecheval evaluate mode-c`)

1. Run Mode C on the **test** synthetic files of `gettysburg`, `o_captain`, `jfk_rice` and `reagan_challenger`, using their as-spoken transcripts, and on the human takes.
2. Evaluate only the types Mode C can produce (rushing, dragging, monotone, too_quiet [trail only], missing_pause). Matching is at **sentence** granularity: a true flaw counts as found if Mode C flags its sentence with the same type.
3. Report `reports/phase08_mode_c.md` with:
   - a table of Mode C recall/precision vs Mode A on the same files and types;
   - a plain statement such as: "Without a reference, recall drops from X to Y. Mode C catches strong flaws (severity ≥ 4) but misses subtle ones."
   - false alarms on clean test sources.

## Step 5 — USER: pitch rehearsals (feeds the demo video)

1. Write the hackathon pitch script into `data/human/pitch/script.txt`.
2. Record `pitch__user__take01` … `take04` on different days, after reading each previous take's Mode C analysis and fixing what it flagged.
3. Codex runs Mode C on each take, and Mode B on each take vs the previous one, and writes `reports/phase08_pitch_progress.md`:
   - a scores-per-take table;
   - flagged items per take;
   - a chart `reports/img/pitch_progress.png`.

## Tests

- Norms from a synthetic sentence table give the hand-computed medians and SDs.
- The key-moment finder detects "10,000", "ten thousand", "45%" and "₹2 crore", and ignores "one of the" (not a figure).
  Rule: number words count only when followed by a noun or unit, **or** when part of a multi-word number. Document the rule.
- Mode C on a sentence table with one sentence at z = +3 for rate gives exactly one rushing region covering that sentence.
- Determinism, as in other phases.

## Acceptance checklist

- [ ] `norms_v1.json` is built, with between-speaker spread reported.
- [ ] Mode C runs on any transcript + audio, including an ASR-only case.
- [ ] `reports/phase08_mode_c.md` contains the cost-of-no-reference table and honest statement.
- [ ] **USER**: at least 2 pitch takes recorded and analysed; the progress report exists.
- [ ] Tests pass; `PROGRESS.md` is updated.

## Out of scope

UI (Phase 9).
