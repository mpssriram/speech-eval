# Blind rating pack implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline; checkbox tasks, TDD and one final fresh review.

**Goal:** Twelve reproducible licensed clips and honest real-rater agreement tooling.

**Architecture:** Crop only training members whose bytes match the release inventory.
Project frozen full-context detections into the actual clip and rescore that
duration. Do not treat injection labels as detector output. Keep key/source/system
scores outside the distributed blind folder. Consume only explicitly supplied ratings.

**Tech:** Python 3.11, soundfile, scipy, existing frozen analysis/rubric, Docker.

**Spec:** `docs/TASKS_C_D_E.md`, item C.

## Global constraints

- Exactly 3 clean + 9 injected, all seven types and mixed severities.
- No test-set selection/tuning; training-only, seeded filenames/order.
- No invented real ratings; unit-test ratings are temporary test inputs only.
- Preserve raw audio and frozen code/config; only release-inventory audio.
- No new narrative report; `docs/RATING_PACK.md` and machine-readable evidence.
- Commit/push only after verification; user authorised autonomous execution.

## Review focus

- Blank/partial/duplicate forms: reject malformed scores and retain coverage.
- Constant scores: undefined correlation must be null, not zero or NaN.
- Crop boundary and long injected span: retain full label and transform seconds.
- Corrupt or unlicensed sources: fail closed before blind export.
- Answer leakage: folder given to raters contains no key/system/type/source IDs.

## Task 1: Agreement metrics and clip projection

Files: `src/speecheval/ratings.py`, `scripts/score_ratings.py`, `tests/test_ratings.py`.
Interface: `agreement(key:dict, ratings:list[dict])->dict`; `read_ratings(path:Path,key:dict)->list[dict]`;
`clip_measurement(analysis:dict,alignment:dict,start:float,end:float,rubric:dict)->dict`.

- [ ] Write literal three-clip perfect/inverted rater test: system rho 1, pairwise rho -1;
  constant means -> null; type exact-set agreement disclosed with denominators.
- [ ] Run `uv run pytest tests/test_ratings.py`: expected missing module RED.
- [ ] Implement scipy Spearman with >=3 shared clips, constant -> null; validate
  scores 1–5 integer, known filename/type, approximate time within clip, no duplicates.
- [ ] Tests for blank/partial/error forms and rescore only visible overlapping regions.
- [ ] Run task tests: expected GREEN, then whole suite.

## Task 2: Deterministic blind audio export

Files: `src/speecheval/rating_pack.py`, `scripts/build_rating_pack.py`,
`tests/test_rating_pack.py`, `docs/RATING_PACK.md`, public blind form and private JSON.
Consumes: `clip_measurement`; licensed `data/release/inventory.json`, dataset index.
Produces: public 12 FLACs + blank CSV + instructions; outside-folder key and SHA manifest.

- [ ] Test seeded selection of 3 originals/9 single variants across all seven types,
  training-only; exact crop bounds, transformed label times; corrupted hash rejection.
- [ ] Run task tests: expected missing functions RED.
- [ ] Implement selection across three licensed training readers; crop nominal 20 s,
  expanding for label+context, no gain changes; opaque seeded names; SHA provenance.
- [ ] Run both task tests and whole suite: expected GREEN.
- [ ] Run real licensed builder twice, compare all audio/form/key hashes; inspect key
  and blind folder; no real agreement result without real ratings.
- [ ] One fresh review, grade by user impact, one RED→GREEN important fix pass.
- [ ] Commit and push named files; record actual tests/hashes in ledger.
