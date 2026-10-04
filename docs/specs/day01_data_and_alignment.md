# Day 1 spec — Source data, audio preparation, and word-level alignment

Read `AGENTS.md` first. This spec follows its rules, layout, and data formats.

## Goal

At the end of Day 1 we have, for every Day 1 source recording:

1. clean, trimmed audio in two formats,
2. a verified as-spoken transcript,
3. word-level timestamps (alignment JSON + Praat TextGrid),

and a measured decision on which aligner (MFA or WhisperX) we use from now on.

Day 1 recordings: the LibriVox Gettysburg collection (15 readers), the LibriVox "O Captain! My Captain!"
collection (12 readers), the JFK Rice excerpt, and the Reagan Challenger address.
All are listed in `data/manifest/sources.yaml`.

## Who does what

| Step | Owner | Est. time |
|---|---|---|
| 0. Machine setup | User | 1–2 h |
| 1–6. Code + pipeline runs | Codex | — |
| 5b. Review transcript differences | User | ~30 min |
| 7a. Mark gold word boundaries in Praat | User | ~45–60 min |
| 7b–8. Aligner bake-off + QA report | Codex | — |

If this spills into Day 2 morning, that is acceptable. Do not skip step 7: the aligner choice affects every later timestamp.

---

## Step 0 — Machine setup (user)

Inside WSL2 Ubuntu:

```bash
# GPU visible inside WSL?
nvidia-smi

# System packages
sudo apt update && sudo apt install -y ffmpeg rubberband-cli sox git

# uv (Python manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Miniforge (conda) for Montreal Forced Aligner
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh -b
~/miniforge3/bin/conda init bash && exec bash

# MFA environment + English models
conda create -n aligner -c conda-forge montreal-forced-aligner -y
conda run -n aligner mfa model download acoustic english_mfa
conda run -n aligner mfa model download dictionary english_us_mfa
conda run -n aligner mfa model download g2p english_us_mfa
conda run -n aligner mfa version
```

Manual downloads (browser) into `data/raw/`:

- JFK Rice MP3 from https://www.jfklibrary.org/asset-viewer/archives/jfkwha-127-002 → `data/raw/jfk_rice_1962.mp3`
- Reagan Challenger MP3 (NARA catalog 7087577, linked from
  https://www.reaganlibrary.gov/archives/audio/remarks-president-reagan-during-address-nation-space-shuttle-challenger-oval-office)
  → `data/raw/reagan_challenger_1986.mp3`

Create an empty GitHub repo `speech-eval`, clone it, and put `AGENTS.md`, this spec, and
`data/manifest/sources.yaml` in it before starting Codex.

---

## Step 1 — Repository scaffold (Codex)

1. Create the layout from `AGENTS.md` §4 (empty modules may contain only a docstring).
2. `.gitignore`: audio extensions, `.venv/`, `__pycache__/`, `data/raw/**` except `.gitkeep`, MFA temp dirs.
3. `pyproject.toml`, package `speecheval` under `src/`, console script `speecheval = speecheval.cli:app`.
4. `configs/default.yaml`:

```yaml
paths:
  raw: data/raw
  hq: data/audio/hq
  align16k: data/audio/align16k
  transcripts_canonical: data/transcripts/canonical
  transcripts_as_spoken: data/transcripts/as_spoken
  alignment: data/alignment
  gold: data/gold/alignment
  reports: reports
audio:
  hq_sample_rate: 44100
  align_sample_rate: 16000
  trim_padding_s: 0.25        # silence kept before first word / after last word
  edge_fade_ms: 10            # fade only at the cut edges, to avoid clicks
asr:                          # used ONLY to propose trims, excerpts and sentence windows (frozen to files)
  model: large-v3
  language: en
  beam_size: 5
  temperature: 0.0
  compute_type: float16       # float32 on CPU
alignment:
  primary: null               # set to "mfa" or "whisperx" after the Step 7 bake-off
  sentence_window_padding_s: 0.30
  mfa:
    acoustic_model: english_mfa
    dictionary: english_us_mfa
    g2p_model: english_us_mfa
    beam: 100
    retry_beam: 400
rounding:
  time_decimals: 3
  feature_sig_digits: 4
```

5. Dependencies (pin exact versions once installed):
   `torch`/`torchaudio` (CUDA 12.8+ wheels, e.g. `--index-url https://download.pytorch.org/whl/cu128`),
   `whisperx`, `praat-parselmouth`, `librosa`, `soundfile`, `pyloudnorm`, `numpy`, `scipy`,
   `internetarchive`, `typer`, `pyyaml`, `pydantic`, `praatio`, `num2words`, `rapidfuzz`, `pytest`.
6. `speecheval --help` lists the commands added below.

## Step 2 — Fetch sources (Codex) — `speecheval fetch`

1. Load and validate `data/manifest/sources.yaml` with a pydantic model. Skip entries with `status: later`.
2. `ia_item` sources: download the audio files of the item with the `internetarchive` package
   into `data/raw/{source_id}/`. Prefer the highest-quality MP3 or Ogg available; download one format per reading, not all.
3. `manual` sources: check the file exists at `expected_file`. If missing, log a clear message and continue.
4. For collections, determine the reader of each file from the item's file-level metadata (`creator`/`artist`/`title`).
   If unavailable, use the reader table on the LibriVox `page`. Last resort: `lv_reader01`, `lv_reader02`…
   in file-name order, and log a warning.
5. Write `data/manifest/raw_files.csv`:
   `source_id, recording_id, speaker_slug, raw_path, sha256, bytes, original_sample_rate, channels, duration_s`.
   `recording_id` follows `AGENTS.md` §5 with `variant = orig`.

## Step 3 — Canonical transcripts (Codex, user checks)

Create `data/transcripts/canonical/{text_id}.txt` for the 4 Day 1 texts.

- **Copy the text from an authoritative source page. Never type it from memory.**
  Put the source URL in the first line as `# source: <url>`; loaders ignore lines starting with `#`.
- `reagan_challenger`: https://www.reaganlibrary.gov/archives/speech/address-nation-explosion-space-shuttle-challenger
- `jfk_rice`: the "View transcript" / "Download Transcript" on
  https://www.jfklibrary.org/learn/about-jfk/historic-speeches/address-at-rice-university-on-the-nations-space-effort
  (full text; the excerpt is cut in step 4).
- `gettysburg`: the Bliss copy from a Library of Congress or Abraham Lincoln Online page.
- `o_captain`: poets.org or another authoritative copy. Keep line breaks: each poem line ends with a newline.
- If a page cannot be fetched by script, add it to `docs/BLOCKERS.md` for the user to paste in.

## Step 4 — Prepare audio (Codex) — `speecheval prepare`

For each recording in `raw_files.csv`:

1. **Decode** with ffmpeg to mono. Write a temporary 16 kHz WAV.
2. **Rough ASR** on the 16 kHz audio using WhisperX with the `asr` settings in config, plus WhisperX's
   own word alignment. Store the raw ASR words in `data/alignment/asr/{recording_id}.json`.
   This ASR output is used **only** for decisions 3–4 below and for step 5. Nothing downstream depends on re-running ASR.
3. **Trim** (LibriVox intros/outros, and leading/trailing noise everywhere):
   - Fuzzy-match (rapidfuzz on normalised tokens) the first 6 and last 6 canonical words against the ASR words.
   - Cut at `first_word.start - trim_padding_s` and `last_word.end + trim_padding_s`.
     Never cut inside a word. Apply `edge_fade_ms` fades only at the two cut points.
4. **Excerpt** (only for sources with an `excerpt` block, i.e. JFK Rice):
   - Find `start_anchor` in the ASR words.
   - Excerpt start = start of the sentence two sentences before the anchor's sentence.
   - Excerpt end = end of the first sentence that ends at or after `start + 150 s`.
     Result must fall inside `target_length_s`. Otherwise extend or shrink by whole sentences.
5. **Freeze decisions** in `data/manifest/excerpts.yaml` (committed):
   `recording_id: {cut_start_s, cut_end_s, method: "asr_anchor", asr_model, notes}`.
   On re-runs, if an entry exists, use the frozen times and skip ASR.
6. **Write audio:**
   - `data/audio/hq/{recording_id}.wav`: 44.1 kHz, mono, PCM16, no loudness change.
   - `data/audio/align16k/{recording_id}.wav`: 16 kHz, mono, PCM16, same cut.
7. **Measure and write** `data/manifest/recordings.csv`:
   `recording_id, text_id, speaker_slug, duration_s, integrated_lufs, peak_dbfs, clipped_fraction, original_sample_rate, cut_start_s, cut_end_s`.
   Flag in a `qa_flags` column: `clipped` if more than 0.1% of samples are at ±full scale,
   `very_quiet` if LUFS < −40, `low_sr` if the original sample rate is < 16 kHz.

## Step 5 — As-spoken transcripts (Codex + user)

Readers and speakers do not always say exactly the canonical text. For example, Gettysburg readers may use
a different manuscript version, and JFK departed from his prepared text.

**5a. Codex — `speecheval transcripts diff`**

1. For each recording, create `data/transcripts/as_spoken/{recording_id}.txt` as a copy of the canonical
   text (or the excerpt's portion of it). Skip any file that already exists: the user may have edited it.
2. Normalise both the as-spoken text and the ASR words: lowercase, strip punctuation, numbers to words
   (num2words), "&" → "and". Align the two token sequences, e.g. difflib `SequenceMatcher` on token lists.
3. Write `reports/day01_transcript_diffs.md`. Per recording, list every insert/delete/replace with
   the transcript words, the ASR words, and ASR start time. Sort recordings by number of differences, worst first.

**5b. User**

**2026-10-04 user-authorized replacement:** the user cannot reliably perform
listening review. Use `speecheval transcripts verify` instead: frozen listen-list
items, CPU wav2vec2 TOTAL CTC log-likelihood summed across alignment paths in local
windows (disputed words plus one neighbouring word each side, 0.2 s padding).
Candidate A is ORIGINAL pre-verification text, including the six previously applied
edits. Calibrate a total-nats margin on 300 seeded controls proportionally across
all 30 recordings using three-way agreeing, non-uncertain proxy-labelled sentences;
choose the smallest positive margin with empirical fake acceptance <=2%.
Apply B above the margin, keep A below the negative margin,
and retain UNSURE otherwise. Record ASR agreement and the score-difference
distribution. Never add `# reviewed: yes` to automatic results; these are model
preferences rather than human-verified ground truth. Use `# reviewed: auto-acoustic-calibrated`
and preserve unresolved final word indices in `data/transcripts/uncertain/*.json`;
both aligners propagate `uncertain_words`, excluded from later statistics/evaluation.
The original manual procedure
below remains available only for optional later human review. The updated
acceptance condition is documented automatic decisions with all remaining
uncertainty and newly exposed differences reported, rather than false human-review markers.

For each listed difference, listen at the given time and decide:

- the speaker really said something different → edit `as_spoken/{recording_id}.txt`;
- ASR error → do nothing.

Mark the recording as reviewed by adding `# reviewed: yes` at the top of its as-spoken file.

**5c. Codex**

Re-run the diff. Recordings with `# reviewed: yes` are listed as reviewed with their remaining differences
(these should all be ASR errors).

## Step 6 — Forced alignment (Codex) — `speecheval align --aligner {mfa|whisperx|both}`

Forced alignment uses the **as-spoken transcript**, not the ASR text.

**6a. Sentence windows (shared by both aligners)**

1. Split the as-spoken transcript into sentences on `. ! ? ;` (also `:` when followed by a capital).
   For `o_captain`, each poem line is a unit.
2. Map each sentence's first and last token to ASR word times using the same token alignment as in step 5.
   If a boundary token has no match, use the nearest matched neighbour.
3. Window = `[first.start - pad, last.end + pad]` with `pad = sentence_window_padding_s`,
   clipped so windows of neighbouring sentences do not overlap by more than `pad`.
4. Freeze to `data/alignment/windows/{recording_id}.json` (committed). Reuse if it exists.

**6b. MFA** (`src/speecheval/align/mfa.py`)

1. Build an MFA corpus in a temp dir: one `{recording_id}.wav` (16 kHz) plus one `{recording_id}.TextGrid`
   with a single tier whose intervals are the sentence windows labelled with sentence text.
   MFA reads the tier name as the speaker, so name the tier after the `recording_id`. This gives one speaker per recording.
2. Find out-of-vocabulary words with `mfa validate`. Generate pronunciations for them with `mfa g2p`
   using the `english_us_mfa` g2p model into a supplementary dictionary, and align with both dictionaries.
   Record OOV words in `warnings`.
3. Run `mfa align` with the configured acoustic model, dictionary, `--beam` and `--retry_beam`, `--clean`,
   and a fixed number of jobs. Parse the output TextGrid's `words` tier.

**6c. WhisperX** (`src/speecheval/align/whisperx_align.py`)

1. Build `segments = [{"text": sentence_text, "start": w.start, "end": w.end} ...]` from the sentence windows.
2. Run `whisperx.load_align_model(language_code="en", device=...)` and
   `whisperx.align(segments, model, metadata, audio, device)`. Collect word timings.

**6d. Shared post-processing** (`align/base.py`)

1. Map aligner output words back to transcript word indices. Aligners may split or merge tokens (hyphens,
   apostrophes, numbers). Use token-sequence alignment on `norm` forms. Every transcript word must get
   exactly one entry.
2. Unplaced words: interpolate between neighbours and add an `interpolated` warning.
3. Enforce monotonic, non-overlapping word times: `end[i] <= start[i+1]`. Fix overlaps by splitting at the midpoint.
4. Validate against a pydantic model of `alignment/v1` (`AGENTS.md` §6.1). Round times to 3 decimals.
5. Write `data/alignment/{aligner}/{recording_id}.json` and a Praat TextGrid
   `data/alignment/{aligner}/{recording_id}.TextGrid` with `sentences` and `words` tiers.
6. Once `alignment.primary` is set in config, `speecheval align --promote` copies the primary aligner's
   files to `data/alignment/{recording_id}.json` / `.TextGrid`.

## Step 7 — Aligner bake-off

**7a. Codex prepares and the user marks gold boundaries**

1. `speecheval gold prepare` selects 3 recordings: one Gettysburg reader with `qa_flags` empty and
   the highest LUFS, `jfk_rice__jfk__orig`, and `reagan_challenger__reagan__orig`.
2. From each, it picks 20 words deterministically: every k-th word with duration ≥ 0.15 s in both
   aligners, k chosen to spread the 20 words across the recording.
3. It writes `data/gold/alignment/todo/{recording_id}.TextGrid` with a tier `gold`. Each interval is
   labelled with the word, and its boundaries are the **average of both aligners' times widened by 0.15 s
   on each side**, so the user must tighten every boundary. This avoids biasing the gold set toward either aligner.
4. **User:** open the WAV and TextGrid together in Praat. Drag each boundary to the true start and end
   of the word (zoom in, use the waveform and spectrogram). Save to `data/gold/alignment/{recording_id}.TextGrid`.

**7b. Codex — `speecheval evaluate alignment`**

For each aligner, compute against the gold boundaries:

- median and mean absolute error of word starts and of word ends (ms),
- % of boundaries within 20 ms and within 50 ms,
- count of interpolated words and OOV words over all Day 1 recordings,
- total runtime, and whether the hardware was GPU or CPU,
- **determinism:** run the aligner twice on the 3 gold recordings and compare sha256 of the JSON outputs.

Write `reports/day01_aligner_bakeoff.md` with a results table and a recommendation, using this rule:

- Choose the aligner with the lower median absolute error over all boundaries.
- If the two medians differ by less than 10 ms, choose the one that is deterministic (identical hashes)
  and runs on CPU. MFA is expected to win this tie-break.
- Report anything that fails ≥ 90% within 50 ms as a risk.

The **user** sets `alignment.primary` in `configs/default.yaml` after reading the report. Codex then runs `speecheval align --promote`.

## Step 8 — Alignment QA report (Codex) — `speecheval report alignment`

`reports/day01_alignment_qa.md`, one row per recording, using the primary aligner:

`recording_id | duration_s | words | speech_rate_wps | interpolated | oov | short_words(<40ms) | long_words(>1.5s, excl. sentence-final) | qa_flags`

Below the table, list every recording with any interpolated word, short word, or long word.
These are the ones the user spot-checks in Praat.

## Step 9 — Tests (Codex)

Fast tests only. No real audio, no model downloads.

- Text normalisation: `"Four score"`, `"1962"`, `"don't"`, `"well-being"`, `"&"`.
- Sentence splitting, including the poem-lines mode.
- Token mapping when an aligner splits `"well-being"` into two tokens, and when one word is missing → interpolated.
- Monotonic-time fixer with an overlapping pair.
- Trim logic on a synthetic signal (0.5 s silence + 1 s tone + 0.5 s silence) with fake word times.
- Alignment JSON: schema validation passes for a valid example and fails for a missing field; rounding to 3 decimals.

## Acceptance checklist (Day 1 is done when all are true)

- [ ] `speecheval fetch` → `raw_files.csv` lists ~29 recordings (15 + 12 + 2), each with a sha256.
- [ ] Every recording has `hq` and `align16k` WAVs. Spot-check 3 LibriVox files: no intro or outro text remains.
- [ ] JFK excerpt is 120–240 s, starts and ends at sentence boundaries, and contains "We choose to go to the moon".
- [ ] Every original Step 5b listen-list item has an automatic acoustic audit and a decision; UNSURE cases and additional unverified differences are explicitly documented. Automatic results are not marked `# reviewed: yes` (user-authorized replacement on 2026-10-04).
- [ ] Both aligners produced valid `alignment/v1` JSON for every recording.
- [ ] `reports/day01_aligner_bakeoff.md` exists. `alignment.primary` is set and files are promoted.
- [ ] `reports/day01_alignment_qa.md` exists, and the user has spot-checked the flagged recordings in Praat.
- [ ] Re-running `prepare` and `align --aligner <primary>` gives identical sha256 for all outputs.
- [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 env -u PYTHONPATH uv run pytest` passes.
- [ ] `docs/specs/PROGRESS.md` has the Day 1 summary.

## Out of scope for Day 1

Feature extraction, normalisation, flaw injection, the dashboard, and the `status: later` sources.
