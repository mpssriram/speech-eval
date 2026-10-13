---
title: Speech-Eval
sdk: static
license: mit
short_description: "Finds speech delivery flaws: what, where and why"
app_file: index.html
---

# Speech-Eval: precomputed demo

Credit: **Sriram MPS, IIT Mandi**.

Precomputed demo. Live analysis of your own audio runs locally with Docker;
see the [GitHub README](https://github.com/mpssriram/speech-eval#quickstart).
This Space serves a Vite build, stored analysis/v1 JSON, and playback-only MP3s.
There are no analysis API calls and uploading is disabled. The default is the
genuine Gettysburg take02 Mode B comparison with take01, showing larger | sense.
All stored flags and scores are preserved, including false alarms.

[Repository](https://github.com/mpssriram/speech-eval) ·
[Dataset](https://github.com/mpssriram/speech-eval/blob/main/docs/DATASET.md) ·
[Current report PDF](https://github.com/mpssriram/speech-eval/blob/main/docs/report/report.pdf)

## Audio licences

Public-domain readers/source audio have source-specific US public-domain evidence
in [licences.json](licensing/licences.json). Derived synthetic playback clips retain
that source status; labels/annotations are CC BY 4.0. The author's genuine takes
are **CC BY 4.0**, with original consent copied byte-for-byte from
[data/human/CONSENT.md](licensing/CONSENT.md). No loudness normalisation is applied
to playback files. They are MP3 at 128 kbps and never used to recompute results.

Code is [MIT](licensing/LICENSE); documentation, labels and the author's recordings
use [CC BY 4.0](licensing/LICENSE-DATA). Assistance: Claude (Anthropic), Codex (OpenAI).

## Rebuild from the repository

```sh
cd deploy/hf-static
npm ci
npm test
npm run build
python3 scripts/verify_build.py
```

The committed public files suffice for a rebuild. To repack the same stored
results from an installed dataset and completed genuine job cache, use
`python3 scripts/export_examples.py` then `python3 scripts/export_audio.py`.
These scripts copy outputs and encode playback only; they do not run a detector.
`MANIFEST.sha256` pins every JSON in the build to its stored original;
`SOURCE_MAP.js` identifies source paths and `AUDIO_SOURCES.js` identifies playback
source hashes/encoding. Copy `dist/` contents and this README to the exact Space
repository `SriramMPS/Speech-Evalutaion`; no hosted build step is required.
In the Space checkout, run `git lfs install --local` and `git lfs track "*.mp3"`
before staging `.gitattributes` and the build; the Hub requires binary playback
files to use its large-file storage bridge.

The selected synthetic examples illustrate successful matches, not benchmark
precision. Genuine labels are recorder-confirmed; no independent ratings or human
alignment spot-check were performed. Mode C uses norms and has no same-text baseline.
