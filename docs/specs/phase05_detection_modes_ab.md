# Phase 5 spec — Reference model, flaw detection, explanations (Mode A + Mode B) — MVP

Read `AGENTS.md` (especially §6.4 `analysis/v1`) and `docs/PLAN.md` first. Requires Phase 4 (dataset v1).

## Goal

`speecheval analyze` takes participant audio plus a text, and outputs flaw regions with timestamps, flaw type,
estimated severity, the measured evidence, and a plain-English explanation. All of it is deterministic.

## Step 1 — Participant pipeline (`src/speecheval/pipeline.py`)

For a new audio file (not already in the dataset):

1. Decode to 44.1 kHz and 16 kHz mono.
2. **Trim with energy, not ASR** (deterministic):
   - Find the first and last 10 ms frames where intensity > (median intensity of the loudest 50% of frames − 25 dB), sustained for ≥ 100 ms.
   - Keep 0.25 s of padding.
3. Transcript:
   - Mode A/B: use the canonical text of `text_id`, unless the user supplies `--transcript`.
   - The participant may skip or add words. Align their **as-read** transcript, then map participant words to reference word indices with the token-sequence alignment from Phase 1 (step 5).
   - Words with no match get `ref_i = null` and are not compared.
4. Align (primary aligner), then compute Phase 2 features.

Recordings already in the dataset reuse their stored alignment and features.

## Step 2 — Reference model (`src/speecheval/reference.py`)

Built per `text_id` from **train-split** clean source recordings, optionally excluding one speaker:

```
build_reference(text_id, exclude_speaker=None) -> ReferenceModel
```

For each reference word index `i` and each comparison feature `f` (table below), with readers `r = 1..n`:

- centre: `mu[i,f] = median_r x[r,i,f]`
- spread: `s[i,f] = 1.4826 * median_r |x[r,i,f] - mu[i,f]|` (robust standard deviation)
- **shrunk spread** (stabilises small n):
  `sigma[i,f] = sqrt( (n * s[i,f]^2 + n0 * sigma_pool[f]^2) / (n + n0) )`, with `n0 = 5`
- `sigma_pool[f]` = median over all words of `s[i,f]`, pooled across `gettysburg` and `o_captain` train readers. It is stored in `data/reference/pooled_sigma.json`.

With a **single** reference recording (Mode B, or the JFK/Reagan texts): `n = 1`, `s = 0`, so `sigma ≈ sigma_pool`.
The same formula covers every case.

**Comparison features** (all computed in Phase 2; transforms make distributions closer to normal):

| Feature key | Source column | Transform | Used for |
|---|---|---|---|
| `rate` | windows.`rate_syl_s` | `ln(x)` | rushing (+), dragging (−) |
| `pitchvar` | windows.`f0_st_std` | `ln(x + 0.25)` | monotone (−) |
| `loud` | windows.`int_rel_db_mean` | none (already dB) | too_quiet (−) |
| `clarity` | windows.`hiband_ratio_db_mean` | none (dB) | mumbling (−) |
| `pause` | words.`pause_before_s` | `ln(x + 0.05)` | awkward_pause (+), missing_pause (−) |

Store the reference models as `data/reference/{text_id}__excl-{speaker|none}.json`, with a `reference_version` hash of their inputs.

**Expert baseline for playback** (`configs/baselines.yaml`, generated once):
- multi-reader texts: the train reader with the smallest mean |z| against the other train readers (the "most typical good reader");
- JFK/Reagan: the original recording.

The dashboard plays and plots this baseline next to the participant.

## Step 3 — z-scores

For each participant word `j` mapped to reference index `i`: `z[j,f] = (x[j,f] - mu[i,f]) / sigma[i,f]`. Round to 4 significant digits.

## Step 4 — Detection rules (`src/speecheval/detect.py`), thresholds in `configs/detector.yaml`

```yaml
k: {rushing: 2.0, dragging: 2.0, monotone: 2.0, too_quiet: 2.0, mumbling: 2.0, awkward_pause: 2.0, missing_pause: 2.0}
region_min_words: 3
region_max_gap_words: 1
awkward_pause_min_s: 0.45          # participant pause must also be at least this long
missing_pause_ref_min_s: 0.30      # only boundaries where the reference median pause is at least this
missing_pause_max_frac: 0.40       # and the participant pause is at most this fraction of it
severity_z_bins: [2.0, 2.75, 3.5, 4.5, 6.0]   # mean |z| at or above bin b gives severity b+1; calibrated in Phase 6
```

1. **Region types** (rushing, dragging, monotone, too_quiet, mumbling):
   - Flag word `j` when `z` passes the threshold in the type's direction.
   - Form runs of flagged words, merging gaps of ≤ `region_max_gap_words` within one sentence.
   - Keep runs with ≥ `region_min_words` words.
   - Region `start` = start of the first word, `end` = end of the last word.
2. **Boundary types:**
   - `awkward_pause`: `z_pause ≥ k` **and** participant pause ≥ `awkward_pause_min_s`.
   - `missing_pause`: reference median pause ≥ `missing_pause_ref_min_s`, **and** participant pause ≤ `missing_pause_max_frac` × reference median pause, **and** `z_pause ≤ −k`.
   - Event `start`/`end` = the pause interval in the participant audio. If the pause is shorter than 30 ms, use ±15 ms around the boundary.
3. **Conflict rules**, applied in this order:
   1. Drop `missing_pause` events strictly inside a `rushing` region.
   2. Drop `awkward_pause` events strictly inside a `dragging` region.
   3. Where a `too_quiet` region lies entirely inside a `mumbling` region and has smaller mean |z|, drop the `too_quiet` region.
4. **Severity** = bin of the region's mean |z| (key feature only) using `severity_z_bins`.

## Step 5 — Explanations (`src/speecheval/explain.py`)

Fill a deterministic template per type. Numbers use 2 significant figures, times 1 decimal place.
Every explanation has three parts:

1. **WHAT** was measured.
2. **HOW MUCH** it differs, as a ratio or difference **and** as z (in standard deviations).
3. **WHERE** in the text, quoting the words.

Templates (exact wording can be polished, but the three parts must stay):

- **rushing:** "{start}–{end} s, "{words}": you spoke at {p_rate} syllables/s; good readers average {r_rate} ({ratio}× faster, {z} SD above). Rushing this phrase reduces its weight."
- **dragging:** "... {p_rate} vs {r_rate} syllables/s ({ratio}× slower, {z} SD below) ..."
- **monotone:** "... your pitch varied by {p_st} semitones; good readers vary by {r_st} ({pct}% less variation, {z} SD below). The phrase sounds flat."
- **too_quiet:** "... {diff} dB quieter than good readers relative to your own average level ({z} SD below)." If the region ends a sentence: "... your voice trails off at the end of the sentence."
- **mumbling:** "... high-frequency energy (consonant clarity) is {diff} dB lower than good readers ({z} SD below). Words may sound muffled."
- **awkward_pause:** "{start} s, between "{w1}" and "{w2}": a {p} s pause where good readers pause {r} s, inside a phrase. It breaks the sentence."
- **missing_pause:** "{start} s, after "{w1}": you paused {p} s where good readers pause {r} s. The listener gets no breathing space."

Add context tags when true: `sentence_final`, `final_sentence`, `contains_number`, `first_sentence`. Append one short clause per tag, e.g. "This is the speech's final sentence."

## Step 6 — Mode B (rehearsal comparison)

`speecheval analyze NEW.wav --text T --mode B --previous OLD.wav`:

- Reference = features of `OLD` (n = 1, so `sigma ≈ sigma_pool`). Same detection and templates, with the wording "your previous take" instead of "good readers".
- Also output a `progress` block (schema in AGENTS.md §6.4): for each flaw type, count and total duration in the previous take's own Mode A analysis vs the new take's Mode A analysis. Mode A analyses are run automatically if missing.

## Step 7 — CLI and outputs

```
speecheval analyze AUDIO --text TEXT_ID [--mode A|B] [--transcript FILE]
                   [--exclude-speaker SLUG] [--previous AUDIO] [--plot]
speecheval analyze-batch --split dev --setting A-LOSO|B-same-speaker   # used in Phase 6
```

- Writes `data/analyses/{analysis_id}.json` (`analysis/v1`).
  `analysis_id = sha256(audio_bytes + mode + reference_version + detector_config_hash)[:12]`.
- Batch mode applies the evaluation settings from PLAN.md §4: A-LOSO uses `exclude_speaker = source speaker`, and B uses the original recording as `--previous`.
- `--plot` writes a PNG with:
  - the waveform with coloured flaw regions;
  - the participant's rate, pitch-variation and loudness tracks against word index, over the reference band `mu ± 2 sigma` (shaded);
  - the region list.

## Tests

- Reference model: 5 synthetic readers with known values give the hand-computed `mu`, `s` and `sigma`; n = 1 gives `sigma` within 1% of `sigma_pool`.
- Detection: a z-table with words 10–15 above threshold for `rate` gives exactly one rushing region covering words 10–15. A one-word gap merges; a two-word gap splits.
- Boundary rules: the awkward/missing pause cases including the absolute-duration guards.
- Conflict rules: each of the three.
- Templates: fixed input → exact expected string.
- Determinism: the same audio analysed twice gives a byte-identical analysis JSON.
- Word mapping: a participant transcript with one skipped and one inserted word maps correctly, and unmatched words are not compared.

## Acceptance checklist

- [ ] `speecheval analyze` works on: one dev synthetic file (A-LOSO), one JFK flawed file (Mode B), and one human take.
- [ ] On 20 dev files (fixed sample), the report `reports/phase05_smoke.md` lists true labels next to detected regions and explanations, for eyeballing. No metrics yet; those are Phase 6.
- [ ] `--plot` PNGs look sensible: **USER** checks 3 of them.
- [ ] Tests pass; determinism passes; `PROGRESS.md` is updated.
- [ ] Commit tagged `mvp`.

## Out of scope

Metrics and threshold tuning (Phase 6), rubric scores (Phase 7), Mode C (Phase 8).
