# speech-eval

Deterministic speech-delivery evaluation for the Multimodal AI Hackathon 2026.

The project runs in WSL Ubuntu at `/home/sriram/speech-eval`.

```bash
cd /home/sriram/speech-eval
env -u PYTHONPATH ~/.local/bin/uv run speecheval transcripts triage
env -u PYTHONPATH ~/.local/bin/uv run speecheval transcripts verify
make test
# Equivalent direct test command:
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 env -u PYTHONPATH ~/.local/bin/uv run pytest
# Wrapper also accepts pytest arguments:
scripts/test.sh tests/test_triage.py
```

The Makefile and test wrapper remove inherited `PYTHONPATH` (including ROS 2
paths) and disable external pytest plugin autoloading. The CLI warns when a
non-empty `PYTHONPATH` is present.

Triage freezes all five Gettysburg manuscript versions with source URLs,
selects an alternative only when it saves at least three token edits over
Bliss, and preserves files marked `# reviewed: yes`. Spelling equivalences
live in `configs/text_equiv.yaml`. `data/review/triage.json` records every edit
and classification, including items excluded from the listen list.

For LISTEN edits, independent WhisperX `medium.en` runs on CPU with beam 5
on the full edit span plus one second on either side. It uses int8 computation
and caches the result by audio SHA-256, clip bounds and model settings in
`data/review/secondary_asr.json`. LIKELY_REAL requires both ASRs to agree on
the entire normalized clip context; it remains a human-review suggestion.

Step 5b human listening review has been replaced, at the user's request, by
`speecheval transcripts verify`. It freezes the original listen-list items and
transcripts, repairs repeated-ending poem cuts if needed, builds sentence/poem-line
windows, and compares candidate A (ORIGINAL pre-verification transcript) with B (ASR substitution), including reassessment of all six earlier applied edits.
The cached WhisperX wav2vec2 model runs on CPU with seed 0, evaluation mode, one
thread and deterministic algorithms. Each score is the total CTC log-likelihood
summed over all valid alignment paths. Identical LOCAL audio covers disputed words plus one neighbour on each side, with 0.2 s padding; total likelihoods are compared without per-frame averaging.
The model checkpoint, audio, inference settings and candidate texts identify caches.

The total-nats margin is calibrated using 300 fixed-seed substitution/deletion/insertion controls, proportionally allocated to eligible words across all 30 recordings. Eligible sentences require exact normalized transcript/large-v3/medium.en agreement and exclude previously uncertain words. Independent full-recording medium.en context is used when sentence-clipped ASR provides no eligible pool. This is unprompted decoding, not transcript-conditioned ASR. The smallest positive margin giving inclusive empirical fake acceptance <=2% is saved in config. A finite B advantage above that margin applies B, a finite A advantage
keeps A, and other cases stay UNSURE. ASR agreement is recorded as supporting
evidence. The score distribution and every decision appear in
`reports/day01_acoustic_verification.md`; full candidate texts, window times, frame
counts and evidence hashes appear in `data/review/acoustic_verification_calibrated.json`. The original audit remains in `data/review/acoustic_verification_legacy.json`.
This is automatic model evidence, not human-verified ground truth. No
`# reviewed: yes` marker is added; files use `# reviewed: auto-acoustic-calibrated`. Three-way agreement is a proxy label, not human ground truth, and the in-sample calibration rate is not guaranteed accuracy on real disagreements. New differences exposed by repaired audio and
UNSURE items remain explicitly unresolved. An unchanged rerun validates provenance,
reuses its audit and preserves applied edits; if transcripts/audio/model/settings
have changed, it stops rather than overwriting that audit. Final zero-based unresolved word indices are saved in `data/transcripts/uncertain/*.json` and propagated as `uncertain_words` in alignments. Later reference statistics and evaluation must exclude them.

For optional inspection, open `\\wsl$\Ubuntu\home\sriram\speech-eval\data\review\index.html` in a browser.
Its players reference `../audio/hq/*.wav` and play the four-second review
window around each timestamp. Decisions typed into the HTML are temporary;
save any later human decisions separately, update the corresponding
as-spoken transcript for actual speech changes, and add `# reviewed: yes` only
if a human actually performed that review.
Already reviewed recordings stay in the audit but are excluded from the
active listen list. Triage does not mark recordings reviewed automatically.
