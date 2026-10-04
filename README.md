# speech-eval

Deterministic speech-delivery evaluation for the Multimodal AI Hackathon 2026.

The project runs in WSL Ubuntu at `/home/sriram/speech-eval`.

```bash
cd /home/sriram/speech-eval
env -u PYTHONPATH ~/.local/bin/uv run speecheval transcripts triage
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

Open `\\wsl$\Ubuntu\home\sriram\speech-eval\data\review\index.html` in a browser.
Its players reference `../audio/hq/*.wav` and play the four-second review
window around each timestamp. Decisions typed into the HTML are temporary;
save decisions in `reports/day01_listen_list.md`, update the corresponding
as-spoken transcript for actual speech changes, then add `# reviewed: yes`.
Already reviewed recordings stay in the audit but are excluded from the
active listen list. Triage does not mark recordings reviewed automatically.
