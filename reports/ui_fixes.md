# UI fixes and landing page — 2026-10-13

Parts A, B and C are complete. Both builds use the same result components and presentation formatter: two-decimal times, no scientific notation, pauses below 0.02 seconds described as absent, and deviations above 10 SD capped in display. Pause grammar, wrapping chips, minimum 4 px waveform markers and subdued identifiers are fixed. Raw evidence, detection, thresholds and scores are unchanged.

The shared navy/cyan landing page has hash navigation, browser back, three comparison modes, 11 gallery cards and project/licence links. The first example is Gettysburg take02 Mode B, showing the “larger | sense” hit. Static upload opens the accessible local-analysis modal and sends no request. Docker retains the existing recording/upload flow.

Verification: **337 Python**, **28 unit**, **25 live browser** and **27 static browser** tests pass. A further real upload/playback/Modes A–C test passes on the production Docker frontend at localhost:8080. Layouts fit 375, 768, 1280, 1440 and 1920 px; the landing fits a 1000 px desktop viewport. A clean static rebuild works without web/node_modules.

All **48 JSON files** match the manifest and stored sources locally and publicly. The original 38 entries and all 830 preexisting protected files are unchanged. GitHub and the Space have rollback tag `ui-v2`. The frontend was rebuilt; the Docker API uses its existing pinned runtime with updated presentation source.

The [public Space](https://huggingface.co/spaces/SriramMPS/Speech-Evalutaion) at `f1c46a605cbb4e3a6be9d5355d41df6ec31246fa` was opened and checked inside its actual Hugging Face iframe: landing, examples, modal, all hosted hashes and no API calls.

The five requested screenshots (`ui_landing`, `ui_upload_modal`, `ui_results`, `ui_region`, `ui_modeC`) and refreshed supplementary views are copied and byte-verified in `Downloads/speech-eval-report-inputs/`. The region capture shows the genuine 29.90–31.47 s hit. Evidence: `ui_fixes_verification.json` and `ui_fixes_public_verification.json`. `NEXT.md` retains the owner’s video, final PDF, repository-access review and submission actions.
