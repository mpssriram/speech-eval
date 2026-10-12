# Genuine take analysis

Current recorder authority (2026-10-12): the explicit chat confirmation replaces
manual TAKES_REVIEW editing. Fixed inputs/provenance are in
`data/human/review/CONFIRMED_PROTOCOL.md` and `confirmation.json`. Transcripts
are built by the recorder's canonical/ASR structural-edit rule, not independently
verified verbatim; use canonical splitter units Gettysburg 1–10/Reagan 1–17.
Unknown spontaneous take04s have `flaws: null`, `excluded_from_scoring: true`
and `exclusion_reason`; they are not clean negatives. They receive A/C analyses,
while B is take02/03 versus own01. No severity labels were supplied or invented.

With the Docker API already healthy, run in WSL from `~/speech-eval`:

```sh
env -u PYTHONPATH ~/.local/bin/uv run python scripts/prepare_human_confirmation.py
env -u PYTHONPATH ~/.local/bin/uv run python scripts/analyze_human.py --detector both --v2-runtime docker
```

V2 must run in the environment that produced the measurements; absolute model
paths are provenance inputs. The Docker option calls the unchanged frozen v2
inside the existing API container, retaining every provenance check. V1 remains
primary; v2 is labelled post-hoc. The older generic notes instructions follow.

Expected inputs: Gettysburg and Reagan Challenger `take01`–`take04` WAVs in
`data/human/raw/`, plus your `notes.md` there and `data/human/CONSENT.md`.
Never put a synthetic fixture in this folder. Latest recording instructions are
the supplied `speech-eval-drafts/recording_script.md`; the old phase-4 twelve-take
generator is not the current eight-take request.

Save the **actual words spoken**, including slips and only the Reagan excerpt
you read, in `data/human/transcripts/{text_id}__user__takeNN.txt`. Do not align a
partial recording to the full canonical text or silently pretend slips were
spoken correctly. Written numbers are expanded while punctuation is retained.
These supplied transcripts are not claimed to have been independently reviewed.

Keep your natural notes, and add one explicit JSON block for reliable evaluation:

```json
{"takes": {
  "gettysburg__user__take01": {"flaws": [], "slips": "none"},
  "gettysburg__user__take02": {"flaws": [
    {"type": "rushing", "sentence": 4},
    {"type": "awkward_pause", "start": 45.0, "end": 47.0}
  ], "slips": "describe actual slips here"}
}}
```

The times above illustrate the format; they are **not** labels for your recordings.
Use your actual raw-recording times. Types use underscores (`too_quiet`,
`awkward_pause`, `missing_pause`). Sentence numbers are one-based and refer to
your as-spoken transcript. Sentence intervals are approximate intended locations,
not independently measured flaw boundaries. Empty flaws must be explicitly
declared, never inferred from absence of detections. Add every available take.

Start the dashboard/API, then run:

```sh
env -u PYTHONPATH ~/.local/bin/uv run python scripts/analyze_human.py
# Docker alternative; dashboard services must already be healthy:
docker compose run --rm --build --no-deps \
  -v "$PWD/docs:/app/docs" -v "$PWD/reports:/app/reports" tools \
  python scripts/analyze_human.py --base-url http://web \
  --dashboard-url http://localhost:8080
```

The driver records original sample rate/channels, converts format without gain
normalisation, preserves raw bytes, uploads supplied text for real CPU MFA, and
uses the producer's trim offsets when comparing raw-time notes. Mode A processes
each available take; Mode B02/B03 use A01 of the same text. If A01 is unavailable,
rehearsal comparisons cannot be made. Reagan's expert reference has one speaker,
so it is not a many-reader empirical distribution.

The Phase10 report links every completed job directly into the existing dashboard;
completed takes also populate its previous-take selector. Named immutable take
IDs map to API job/recording IDs in `data/human/evaluation.json`. Processed human
audio is lossless FLAC under `data/human/prepared/`. Public release inclusion is
not automatic: the frozen release archive excludes all human inputs.

When no genuine audio exists, explicitly run `--fixture` to exercise the same
driver on licensed clean/injected crops in `data/.cache/human-fixture/`. Its
numbers are workflow evidence only, never human-performance or human-agreement
results. No threshold is tuned on either fixture or user recordings.

The Docker bind mounts preserve the authorised Phase10 report and blocker log
on the host; otherwise a one-off container would discard them. Use this command
from the repository root in a POSIX shell (including WSL).
