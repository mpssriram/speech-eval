# Phase 10 human takes

**Genuine human takes: pending**

No detector thresholds, bins, rubric weights or frozen scientific implementation were tuned.
Format normalisation is mono PCM16/44.1 kHz conversion, not loudness normalisation. Raw audio remains unchanged.
Alignment uses real CPU MFA on supplied as-spoken text with number expansion. Trim offsets come from producer provenance.

Primary interval matching: same type, one-to-one greedy IoU >= 0.3 for every type. Historical synthetic matching uses IoU >= 0.3 for regions but centre distance <= 0.25 s for pause events; its counts are shown separately.
Sentence-only notes are intended intervals, not independent time-labelled perceptual ground truth. Slips must be reflected in the supplied transcript; no automatic listening/review is claimed.

## Pending inputs

- No requested WAVs, notes.md or consent have been supplied in data/human/.

## Synthetic workflow verification — not human results

| Take | Mode | IoU hits / misses / FP | Synthetic-policy hits / misses / FP | Dashboard |
|---|---|---|---|---|
| workflow_fixture_1 | A | 0 / 0 / 0 | 0 / 0 / 0 | [Open](http://localhost:8080/results/86cb86dc2e9402d769f5a14c) |
| workflow_fixture_2 | A | 0 / 1 / 0 | 0 / 1 / 0 | [Open](http://localhost:8080/results/90e5cbba14d9486b41c32754) |
| workflow_fixture_2 | B | 0 / 1 / 0 | 0 / 1 / 0 | [Open](http://localhost:8080/results/2f439711be18c1451466e9e1) |

QA, hashes, exact declared label basis, trim bounds, aligner and score evidence: `data/human/fixture_verification.json` (explicitly synthetic).
Jobs are real completed API jobs, visible via their dashboard links and the existing previous-take history. Fixture jobs must not be presented as the user's recordings.

Actual notes/consent/recordings and independent raters remain user actions. No human accuracy, rehearsal improvement or agreement claim is available until genuine input exists.
