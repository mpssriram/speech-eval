# Phase 9 spec — API and dashboard

Read `AGENTS.md` and `docs/PLAN.md` first. Requires Phases 5–7 (Phase 8 optional; hide Mode C in the UI if it's not done).

## Goal

A web app where a user uploads or records audio, picks a text and mode, and sees:

- scores,
- flaw regions on the waveform,
- feature curves against the reference band,
- number-backed explanations,
- side-by-side playback of their delivery and the baseline's for the same words.

It runs with one command: `docker compose up`.

## Step 1 — API (`api/`, FastAPI, Python package in the same repo)

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Version, git commit, `reference_version`, detector config hash |
| GET | `/api/texts` | Available texts: `text_id`, title, category, canonical transcript, baseline recording id |
| POST | `/api/analyses` | multipart: `audio` (wav/mp3/m4a/webm/ogg, ≤ 25 MB, ≤ 10 min), `text_id` **or** `transcript`, `mode` (A/B/C), optional `previous_analysis_id` (Mode B). Returns `{analysis_id, status}`. |
| GET | `/api/analyses/{id}` | Status (`queued`, `running`, `done`, `error`), and the `analysis/v1` JSON when done |
| GET | `/api/analyses/{id}/tracks` | For plotting: per-word arrays (index, text, start, end, the 5 comparison features, reference `mu` and `sigma` when available), plus the frame-level F0 (st) and intensity (dB), downsampled to 20 ms |
| GET | `/api/audio/{recording_id}` | Audio with HTTP range support (participant or baseline) |
| GET | `/api/analyses/{id}/baseline-segment?word_start=&word_end=` | Start/end time of the same words in the baseline recording, for A/B playback |
| GET | `/api/history?text_id=` | Previous analyses of this text on this server (for the rehearsal chart) |

Details:

- **Jobs:** one background worker thread processes jobs **sequentially** (determinism, and it fits a single GPU/CPU). The queue and state are stored as JSON files in `data/app/jobs/`. No database.
- **Identical uploads:** if the same audio, mode and text is uploaded again, return the existing analysis, since `analysis_id` is content-addressed.
- **Errors:** validate the format and duration, and convert with ffmpeg. Return clear errors such as "Audio longer than 10 minutes" or "Could not align: transcript does not match the audio". The latter is detected when > 30% of words are unaligned or interpolated.
- **CORS:** only for the dev frontend origin.
- **Tests:** FastAPI `TestClient`, using a 10 s fixture clip and a 2-sentence fixture text, covering upload → done → analysis JSON.

## Step 2 — Frontend (`web/`, React + Vite + TypeScript)

Libraries:

- `wavesurfer.js` v7 with the Regions plugin (waveform + flaw regions);
- `plotly.js-basic-dist` (feature charts);
- one component library for the UI chrome, e.g. shadcn/ui or Mantine — pick one and keep it.

Style:

- Dark navy/black background, cyan/blue accents, clean and professional.
- **Flaw types use 7 distinct colours that also have text labels.** Never colour alone.
- A small legend is always visible.

**Page 1 — New analysis**

- Choose text (dropdown from `/api/texts`) or "My own speech" (paste transcript → Mode C).
- Choose mode: "Compare with expert" (A) or "Compare with my previous take" (B, lists history).
- Input audio by upload, or **record in the browser** with `MediaRecorder` (webm/opus), showing a timer and a level meter.
- "Analyse" shows progress by polling `/api/analyses/{id}` every second.

**Page 2 — Results** (top to bottom)

1. **Score card:** overall score (large) and 5 category scores with a one-line reason each, e.g. "Pace 7.0 — 1 rushed phrase".
2. **Waveform** of the participant with flaw regions coloured by type. Click a region → it's selected everywhere.
3. **Transcript strip:** words in reading order; flawed words underlined in their type colour; hovering a word shows its start time; clicking a word seeks there.
4. **Feature chart:** tabs for Speed / Pitch variation / Loudness / Clarity / Pauses. Per-word participant line over the reference band (`mu ± 2 sigma`, shaded), x-axis = word index with word labels on hover, and the selected region highlighted.
5. **Flaw list:** cards sorted by time. Each card has the type badge, severity (1–5 dots), time range, the quoted words, the explanation text, and buttons **▶ Yours** and **▶ Baseline (same words)**.
6. **Key moments** (Mode C only), shown with a "guideline" label.
7. **Progress** (Mode B / history): a line chart of overall and category scores across takes.

States: loading skeletons, empty state ("No flaws detected — your delivery is within the range of good readers"), and error messages from the API.

## Step 3 — Compose and run

- `docker-compose.yml`:
  - `api`: the Phase 2 image + `uvicorn`, mounting `./data`;
  - `web`: a multi-stage build → nginx serving static files and proxying `/api` to `api`.
- `make up` → `docker compose up --build`. Open http://localhost:8080.
- Dev mode: `make dev` runs uvicorn with reload + `vite dev`.

## Step 4 — End-to-end smoke test (Playwright, already available on the machine)

1. Start the stack.
2. Upload the fixture clip with text = fixture.
3. Wait for done.
4. Assert that the score card shows a number, at least one region is drawn, clicking a flaw card plays audio (the audio element's `currentTime` advances), and the feature chart renders.
5. Save screenshots to `reports/img/ui_*.png`. These are also used in the report and video.

## Acceptance checklist

- [ ] `make up` works from a clean clone with only `data/` present.
- [ ] **USER** runs through: upload a human take (Mode A) → read the explanations → play yours vs baseline → record a new take in the browser → Mode B shows progress.
- [ ] The Playwright smoke test passes; screenshots are saved.
- [ ] Performance: a 2-minute clip analysed in < 60 s on the user's laptop. Alignment and features run on CPU, as Phase 7 requires; the GPU is used only for ASR in Mode C without a transcript.
- [ ] API tests pass; `PROGRESS.md` is updated.

## Out of scope

User accounts, cloud deployment.
