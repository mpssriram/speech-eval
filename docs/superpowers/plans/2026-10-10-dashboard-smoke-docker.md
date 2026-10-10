# Dashboard, UI Smoke, and Docker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the Phase 9 dashboard, prove Modes A/B/C in Chromium with the required screenshots, and make the complete application reproducible at `http://localhost:8080` with Docker Compose.

**Architecture:** Keep the existing FastAPI analysis service as the sole backend and the React/Vite dashboard as a static client. The development browser run uses Vite's `/api` proxy; production uses an nginx container that serves the Vite build and proxies `/api` to the API container. Playwright exercises the real API and corpus-backed audio, while Docker smoke checks run from a clean temporary clone.

**Tech Stack:** Python 3.11, FastAPI, React 19, TypeScript, Vite, WaveSurfer v7, Plotly, Playwright, Docker Compose, nginx.

**Spec:** `docs/specs/phase09_api_dashboard.md`

## Global Constraints

- Preserve deterministic scoring and never modify `data/raw/`.
- Do not commit audio, secrets, generated application state, or unrelated untracked corpus artifacts.
- Modes A and B use same-text comparisons; Mode C is explicitly labeled as a four-feature guideline prototype.
- Each ordered user item ends with fresh verification, a focused commit, and a push to `origin/main`.
- Genuine blockers are recorded in `docs/BLOCKERS.md`; work then moves to the next item.

## Review Focus

- Browser audio autoplay or unsupported media must surface a useful error and must not silently leave playback at zero.
- A result with no regions must render the empty state without indexing a missing region.
- Mode B must require and use a completed earlier take of the same text.
- Mode C must accept an own-speech transcript, omit baseline playback, and show guideline key moments when present.
- The production proxy must support audio range requests and client-side `/results/<id>` navigation.

---

### Task 1: Browser-verified dashboard

**Files:**
- Modify: `web/src/App.tsx`
- Modify: `web/src/Evidence.tsx`
- Modify: `web/src/types.ts`
- Modify: `web/src/style.css`
- Test: `web/tests/dashboard.spec.ts`

**Interfaces:**
- Consumes: Phase 9 API routes in `src/speecheval/service.py` and `analysis/v1` results.
- Produces: Accessible upload/results controls, synchronized region selection, score/category reasons, two-source phrase playback, and working Mode A/B/C selection.

- [x] **Step 1: Start FastAPI and Vite, open the rendered dashboard in Chromium, and capture console/network failures.**

Run: `uv run uvicorn api.main:app --host 0.0.0.0 --port 8000` and `cd web && npm run dev`, then inspect `http://localhost:5173`.

Expected: the new-analysis page loads, `/api/texts` returns 200, and every visible failure is reproducible.

- [x] **Step 2: Add browser assertions for every broken interaction before changing production code.**

Add Playwright assertions for upload state, Mode A/B/C selectors, score card, region/card synchronization, explanation content, and both playback controls.

Expected: the new assertions fail on the specific broken behavior rather than setup or selector errors.

- [x] **Step 3: Implement the minimum dashboard fixes.**

Keep one selected region index, make empty-region selection safe, expose stable accessible/test identifiers, stop phrase audio at its selected end, disable baseline playback when unavailable or words do not match exactly, and render Mode B progress and Mode C guidelines.

Expected: the focused Playwright assertions pass and the browser console has no page errors.

- [x] **Step 4: Verify build and the real-browser flow.**

Run: `cd web && npm run build` and the focused Playwright dashboard test.

Expected: TypeScript/Vite exit 0 and Chromium completes upload, results, waveform, regions, explanations, playback, scores, and Modes A/B/C.

- [x] **Step 5: Commit and push item 1.**

Commit only the dashboard source/configuration and this plan with message `phase9: finish browser-verified dashboard`, then push `origin main`.

### Task 2: Deterministic Playwright smoke and evidence

**Files:**
- Modify: `web/playwright.config.ts`
- Modify: `web/tests/dashboard.spec.ts`
- Create: `web/tests/fixtures.ts`
- Create: `reports/img/ui_upload.png`
- Create: `reports/img/ui_results.png`
- Create: `reports/img/ui_region.png`
- Create: `reports/img/ui_modeB.png`
- Create: `reports/img/ui_modeC.png`
- Create: `reports/phase09_ui.md`

**Interfaces:**
- Consumes: Task 1's accessible controls and real API behavior.
- Produces: A one-command Playwright smoke with five stable evidence screenshots and a provenance report.

- [x] **Step 1: Make fixture preparation deterministic and fail clearly when corpus inputs are absent.**

Use the prepared licensed Gettysburg WAV with its verified SHA-256. It yields two real Mode A regions and exercises both an exact baseline phrase and a phrase whose words differ. Canonical Mode C uses its existing verified corpus transcript.

Expected: fixture setup names every required local input and exits before browser launch if one is missing.

- [x] **Step 2: Run the expanded smoke and observe its first real failure.**

Run: `cd web && npm test` with FastAPI and Vite running.

Expected: RED at the first unimplemented or broken acceptance behavior, not at page bootstrap.

- [x] **Step 3: Complete the A/B/C smoke and exact screenshot names.**

Assert score numbers, Plotly SVG, WaveSurfer regions, region selection, Yours and Baseline playback progress, Mode B progress, and Mode C guideline labeling; save exactly the five requested PNGs.

Expected: all assertions pass with no collected page errors or failed `/api` responses.

- [x] **Step 4: Write the UI verification report.**

Document browser/version, commands, fixture provenance, Mode A/B/C coverage, screenshot paths, and remaining USER-only MediaRecorder/human-listening acceptance.

Expected: `reports/phase09_ui.md` distinguishes automated evidence from unperformed human review.

- [x] **Step 5: Commit and push item 2.**

Commit the smoke test, screenshots, and report with message `phase9: add deterministic UI smoke evidence`, then push `origin main`.

### Task 3: Docker Compose and reproduction targets

**Files:**
- Create: `.dockerignore`
- Create: `Dockerfile`
- Create: `web/Dockerfile`
- Create: `web/nginx.conf`
- Create: `docker-compose.yml`
- Modify: `Makefile`
- Create: `src/speecheval/reproduce.py`
- Create: `scripts/restore_local_data.py`
- Test: `tests/test_release_commands.py`

**Interfaces:**
- Consumes: the Python package, `api.main:app`, Task 1's Vite application, and published/local dataset artifacts.
- Produces: `make up`, `make test`, `make reproduce-quick`, and `make reproduce`; dashboard/API served through port 8080.

- [x] **Step 1: Write executable release-command tests first.**

Create tests that run the Make targets in dry-run or controlled fixture mode and verify that quick reproduction selects one text/three test readers while full reproduction invokes every published report-number check.

Expected: tests fail because the Compose files and targets do not yet exist.

- [x] **Step 2: Add production container definitions.**

Build the API from Python 3.11 with system audio tools, build the web client in Node, serve it from nginx, proxy `/api`, preserve range headers, and mount `./data` for API state and corpus access.

Expected: `docker compose config` exits 0 and exposes only web port 8080 to the host.

- [x] **Step 3: Add Make targets and reproducibility scripts.**

Keep `test` equivalent to the repository contract, make `up` invoke `docker compose up --build`, define a CPU-only quick path for one text/three test readers, and define the full report-number reproduction path.

Expected: command tests pass and target help/output makes scope explicit.

- [x] **Step 4: Verify from a fresh temporary clone.**

Clone the local repository to a new temporary directory, copy or mount only the required ignored `data/` inputs, run `docker compose build`, `docker compose up -d`, query `http://localhost:8080/api/health` and `/`, then tear down the temporary stack.

Expected: health returns 200 JSON, the dashboard HTML returns 200, and no working-tree-only file is required.

- [x] **Step 5: Run the complete test suite, commit, and push item 3.**

Run: `make test`, `docker compose config`, and the fresh-clone smoke; commit with message `phase9: add compose and reproduction entrypoints`, then push `origin main`.

