# Phase 3 spec — Flaw injector

Read `AGENTS.md` and `docs/PLAN.md` first. Requires Phases 1–2.

## Goal

A function that takes a clean source recording plus a flaw specification, and returns:

1. flawed audio,
2. an exact label (`labels/v1`),
3. an exact **time map** from source time to flawed time,
4. an **oracle alignment**: the source alignment pushed through the time map.

Everything is deterministic given a seed.

## Flaw types and severity parameters — `configs/flaws.yaml`

```yaml
seed: 20261001
crossfade_ms: 20
region_words: {min: 4, max: 12}        # for region flaws
keep_out_s: 1.0                        # no flaw starts within 1 s of the recording start or end
min_gap_between_flaws_s: 2.0
types:
  rushing:       {kind: region, param: speed_factor,        severity: [1.15, 1.30, 1.50, 1.75, 2.00]}
  dragging:      {kind: region, param: speed_factor,        severity: [0.87, 0.77, 0.67, 0.58, 0.50]}
  monotone:      {kind: region, param: pitch_range_kept,    severity: [0.70, 0.50, 0.35, 0.20, 0.08]}
  too_quiet:     {kind: region, param: gain_db,             severity: [-3, -6, -9, -12, -18],
                  shapes: [flat, trail]}  # trail = linear fade from 0 dB to gain_db over the region
  awkward_pause: {kind: boundary, param: inserted_pause_s,  severity: [0.6, 1.0, 1.5, 2.2, 3.0]}
  missing_pause: {kind: boundary, param: pause_kept_frac,   severity: [0.70, 0.50, 0.30, 0.15, 0.0]}
  mumbling:      {kind: region, param: lowpass_hz,          severity: [3500, 2800, 2200, 1700, 1300],
                  extra_gain_db_per_severity: -1.0}
```

## Where flaws go (`src/speecheval/inject.py`: `choose_sites`)

- RNG: `numpy.random.default_rng(hash64(seed, recording_id, flaw_type, severity, placement_index))`. Use a stable hash (e.g. `xxhash` or `hashlib.sha256`), not Python's `hash()`.
- **Region flaws:** a contiguous run of `min..max` words **inside one sentence**, at least `keep_out_s` from the recording edges.
  - `too_quiet` with shape `trail` always ends at the last word of a sentence.
- **`awkward_pause`:** a word boundary **inside** a phrase. The source pause there must be < 0.15 s, and neither neighbouring word may end with punctuation in the transcript.
- **`missing_pause`:** a word boundary whose source pause is ≥ 0.35 s, normally a sentence or comma boundary.
- If no valid site exists, skip and log it. Never place a flaw in a weird spot to fill a quota.

## How each flaw is made (`apply_*` functions)

All edits work on the 44.1 kHz mono float32 audio. Cut points snap to the nearest zero-crossing within ±5 ms.
Splices use `crossfade_ms` equal-power crossfades.

| Type | Method |
|---|---|
| `rushing` / `dragging` | Cut the region, time-stretch it with the `rubberband` CLI (`--fine`, tempo = `speed_factor`, pitch unchanged), splice it back. Region duration becomes `dur / speed_factor`. |
| `monotone` | Parselmouth Manipulation (time step 0.01, using the recording's pitch floor/ceiling from `speaker_stats`). In the region's PitchTier, replace each point f by `m * (f/m) ** k`, where m = median pitch of the region and k = `pitch_range_kept`. Resynthesise with overlap-add (PSOLA). Splice only the region back, with crossfades. Duration unchanged. |
| `too_quiet` | Multiply the region by a gain envelope: `flat` = constant `gain_db` with 30 ms ramps at both ends; `trail` = linear in dB from 0 to `gain_db` across the region. Duration unchanged. |
| `awkward_pause` | Insert `inserted_pause_s` of **room tone**, not digital silence, at the boundary midpoint. Room tone = the recording's quietest 300 ms between words, looped with crossfades. |
| `missing_pause` | Shorten the existing pause to `max(0.03, pause × pause_kept_frac)` by removing audio from its middle, with a crossfade. |
| `mumbling` | Zero-phase low-pass (4th-order Butterworth, `scipy.signal.sosfiltfilt`) at `lowpass_hz` on the region, plus `extra_gain_db_per_severity × severity` dB, with 30 ms crossfades to the dry signal at both ends. Duration unchanged. |

After editing: if the peak exceeds −1 dBFS, scale the **whole file** down to −1 dBFS peak, and record `"peak_normalised_db"` in the label parameters. Never clip.

## Time map and oracle alignment

- Represent the time map as a monotonic piecewise-linear function from source time to flawed time, stored as breakpoints `[[t_src, t_flawed], ...]`.
- `rushing`/`dragging` scale the region; pauses insert or remove a segment; the other flaws are the identity.
- Push every word's `start`/`end` through the map → `data/alignment/oracle/{flawed_recording_id}.json` (schema `alignment/v1`, aligner name `oracle`).
- Label `start`/`end` (flawed timeline):
  - region flaws: the mapped start of the first region word and mapped end of the last region word;
  - `awkward_pause`: the inserted silence interval;
  - `missing_pause`: the shortened pause interval (it may be 0.03 s long). Also store `"source_pause_s"` and `"result_pause_s"` in `parameters`.
  - `word_start`/`word_end`: for boundary flaws, the two words around the boundary.

## Outputs per flawed file

- Audio, stored as **FLAC** (lossless, half the size of WAV):
  - `data/flawed/hq/{flawed_recording_id}.flac` (44.1 kHz, PCM_16)
  - `data/flawed/align16k/{flawed_recording_id}.flac` (16 kHz)
- `data/labels/{flawed_recording_id}.json` (`labels/v1`, `source: synthetic`, `reference_id` = source `orig` recording).
- `data/alignment/oracle/{flawed_recording_id}.json`.
- `data/flawed/timemaps/{flawed_recording_id}.json`.
- Naming per AGENTS.md §5: `{text_id}__{speaker_slug}__{flaw}_s{severity}_{nn}`. Mixed files use `mixed_{nn}`.

## Step — Listening pack (`speecheval inject preview`)

1. For one clean Gettysburg reader, generate every type × severity (35 files) into `data/flawed/preview/`.
2. Write `reports/phase03_listening.md` with one row per file: type, severity, flaw time range, the words affected, and empty columns `audible (y/n)` and `realistic (1–5)`.
3. Also write `data/flawed/preview/index.html`. It's a plain page with an `<audio>` element per file and the source, and a button that plays the source and flawed versions of the region back to back. (It's only a listening aid, not the product dashboard.)

**USER:** listen to all 35, fill in the two columns, and commit the file. Targets: severity 1 is barely audible, severity 5 is obvious, and nothing sounds broken (clicks, robot voice, glitches). Send the filled sheet to Claude. Severity parameters may be adjusted before Phase 4.

## Tests

- Rushing a 2 s region of a synthetic signal by 1.5× gives region duration 1.333 ± 0.02 s, and the time map's slope in the region is 1/1.5.
- Monotone with k = 0.2 on a synthetic vibrato tone (150 Hz ± 2 st at 5 Hz) reduces the measured F0 std (semitones) to 20% ± 5%.
- `too_quiet` flat −6 dB → RMS ratio in the region 0.501 ± 0.01; outside the region unchanged (bit-identical away from the ramps).
- `awkward_pause` of 1.0 s: total duration grows by 1.000 ± 0.001 s; words after the boundary shift by 1.0 s in the oracle alignment.
- `missing_pause` keeps ≥ 30 ms.
- Labels validate against `labels/v1`.
- Same seed → identical FLAC hash, labels and time map. A different `placement_index` → a different site.
- No sample exceeds full scale.

## Acceptance checklist

- [ ] `speecheval inject preview` produces 35 files, the listening sheet and `index.html`.
- [ ] **USER** has filled and committed `reports/phase03_listening.md`.
- [ ] Any parameter changes agreed with Claude are applied to `configs/flaws.yaml`, and the preview is re-generated.
- [ ] Tests pass; determinism check passes; `PROGRESS.md` is updated.

## Out of scope

Generating the full dataset (Phase 4).
