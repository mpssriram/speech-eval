# Static demo deployment checks

Date: 2026-10-13 (Asia/Calcutta). Frozen v1 results; no detector, score, threshold,
source audio, report source or PDF was modified or recomputed.

- Production Vite build: PASS. Two builds had identical bytes for all 58 shipped
  files (38 stored JSONs, 14 MP3s, HTML/CSS/JS and three licence/consent texts).
- JSON identity: **38/38 PASS**, with the complete inventory checked (extra/missing
  files fail). Every build JSON is byte-identical to its local stored original,
  pinned in `deploy/hf-static/MANIFEST.sha256`; original repo paths are in
  `SOURCE_MAP.js`. Analysis JSONs are copied verbatim, never reserialised.
- Repacking: **59/59** export/provenance files remained byte-identical, including
  all MP3s, catalog, SHA list and copied JSONs. All **23/23** frozen scientific
  code/config and current report files match the pre-task hashes.
- Playback: **14** MP3 files, **23,545,504 bytes**, libmp3lame at **128 kbps**;
  no gain filters or loudness normalisation. `AUDIO_SOURCES.js` records original
  audio hashes, output hashes, sizes and encoding. The analysed HQ timeline is
  retained; these lossy copies are for listening only.
- Node tests: **2 passed** (exact same-word span; unavailable-word refusal).
- Playwright against the production preview: **3 passed in 30.6 s**. All **19**
  views load and play; every A/B view with a selected flag plays the same words
  in its baseline. The clean source has no flag/phrase selection; both complete
  recordings play. C correctly has no same-text baseline. Browser checks include
  default genuine take02 Mode B at **29.90–31.47 s**, switching/selecting regions,
  actual participant/baseline seek and advancing playback, 390px mobile overflow,
  and keyboard selection. Zero page errors, failed HTTP responses or API calls.
- Repository Python suite: **314 passed**, exit 0 (pre-packaging run; static
  assets do not change Python/scientific code). A final packaging run follows
  in reproducibility evidence. Numerical results were not retuned.

Machine browser evidence: `reports/deploy_browser_checks.json`.
Screenshots: `reports/img/static_results.png`, `static_region.png`, `static_mobile.png`.
The default screenshot and mobile layout were inspected for clipping and legibility.

## Reproduce

```sh
cd deploy/hf-static
npm ci
npm test
npm run build
python3 scripts/verify_build.py --require-sources  # installed stored dataset required
npm run test:browser
```

A fresh checkout can run the hash verifier without `--require-sources`: the SHA
pins and committed public data suffice; the strict original-source comparison
above used the installed corpus and the stored genuine job outputs.

## Public Space verification

Published [Speech-Evalutaion](https://huggingface.co/spaces/SriramMPS/Speech-Evalutaion)
as the free static SDK, commit `2403482ae6b0e8fca3c2cdc505948bb0cc428eae`.
`hf auth whoami` confirmed SriramMPS. The existing Space was cloned into a temp
folder, the production build copied, committed and pushed. MP3s use Git LFS / the
Hub storage bridge, as required by the Hub binary-file hook. No credentials were
printed, written into project files, embedded in URLs or saved by this workflow.
Existing login credentials were read in memory for the Git HTTPS request.

Anonymous Hub page: **HTTP 200**. Its public static iframe loads the default
Gettysburg take02 Mode B, selected awkward pause **29.90–31.47 s**. All **38/38**
JSON files fetched anonymously from the public app match MANIFEST.sha256.
Public production browser tests: **3 passed in 58.2 s**, including all 19 examples,
real audio and same-word phrase playback, region selection and mobile layout;
zero page errors, failed app responses or analysis API calls.

Evidence: `reports/hf_public_check.json`, `reports/deploy_browser_checks_public.json`.
Screenshot: `reports/img/hf_space.png` (public Hub chrome and the selected genuine
hit); cropped public hit: `reports/img/hf_space_region.png`. Both were captured
without a browser login. The public page was opened and captured in an anonymous browser session.

A later documentation/provenance-only Space update is commit
`4d7a2f25140e21517ef96875733622b027518d85`: it clarifies that the copied licence
JSON covers the frozen main archive, while the included genuine takes use the
later authorised CC BY 4.0 grant. SOURCE_MAP.js / AUDIO_SOURCES.js are now also
shipped beside the build. App assets, audio, JSON hashes and selected default
are unchanged. Independent read-only review found no Critical or Important
issue; this licence-scope clarification resolved its one Minor finding.
