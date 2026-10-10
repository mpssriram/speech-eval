# Blind rating pack

Distribute **only `data/rating_pack/`**, including its twelve FLAC clips, blank
`rating_form.csv`, instructions and content checksums. Do not send the repository,
`data/rating_pack_private/answer_key.json`, system outputs or this construction
description to raters. The hidden key is separate, not a security boundary against
raters who independently browse the repository.

The pack contains three uninjected controls and nine single-injection clips,
covering all seven types at mixed severities. Uninjected means no synthetic edit,
not flawless or ideal delivery. Selection is fixed before looking at detections,
from three training speakers only. All source bytes, alignments and labels are
checked against the licensed release inventory. No test-set selection or tuning.
Opaque filenames and form order use a fixed seed. No loudness normalisation.

Rebuild after fetching the release (binary clips are not in Git):

```sh
env -u PYTHONPATH ~/.local/bin/uv run python scripts/build_rating_pack.py
# Docker-only alternative; data/ is already mounted by the tools service:
docker compose run --rm --build --no-deps tools python scripts/build_rating_pack.py
```

Rebuilding refuses to overwrite an edited rating template or accept unexpected
files in the blind folder. Raters should save separate CSVs, with their own
anonymous ID on every filled row. Collect independent ratings; the earlier
validation plan requests at least three raters. No rater responses are supplied
or fabricated here.

```sh
env -u PYTHONPATH ~/.local/bin/uv run python scripts/score_ratings.py \
  --ratings data/ratings/rater_a.csv data/ratings/rater_b.csv data/ratings/rater_c.csv
# Docker: keep the supplied CSVs under data/ and use the same arguments:
docker compose run --rm --build --no-deps tools python scripts/score_ratings.py \
  --ratings data/ratings/rater_a.csv data/ratings/rater_b.csv data/ratings/rater_c.csv
```

Output: `data/rating_pack_private/agreement.json`. Blank templates do not count
as ratings and cannot produce an agreement result. Scores must be integers 1–5;
flaw types are known names or `none`, with approximate in-clip times for flaws.
Duplicate rater/clip rows are rejected; incomplete coverage is explicitly counted.

System–human Spearman uses mean human score per rated clip, with per-rater values
also reported. Human–human uses each pair's shared clips, then the unweighted
mean of defined correlations. Fewer than three shared clips or constant ranks
give `null`, not zero. Exact flaw-type **set** agreement includes `none`, with
explicit pooled denominators for human–human, system–human and human–injection-key.
These are different questions; injection parameters are not perceptual truth.
Approximate times are collected/validated but no precise temporal-accuracy claim
is made from them.

System scores use frozen full-source Mode A detections with the participant
speaker excluded, project only visible overlapping regions into the clip, then
apply the unchanged rubric to the visible aligned speech duration. The detector
had full-source context while raters hear isolated clips; this conditioning is a
limitation, not independent short-clip inference. Tiny convenience sampling,
synthetic edits and correlated excerpts cannot establish population validity.

Actual export repeat/hash evidence is in
`data/rating_pack_private/verification.json`. Real agreement remains pending.
