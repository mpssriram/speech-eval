# Tasks C, D, E — supplied continuation

Source: `C:\Users\msrir\Downloads\speech-eval-drafts\codex_tasks_C_D_E.md`.

C: Build `data/rating_pack/` with 12 clips: 3 clean and 9 injected, mixed
severity, all seven flaw types, randomized names. Blind form: delivery score
1–5, flaw type if any, approximate flaw time. Separate hidden key. Compute
system–human Spearman, mean pairwise human–human Spearman and flaw agreement.
Only use release-archive sources.

D: `docs/DATASET.md`: sources/licences, counts/hours, types/severities,
speaker splits, formats, label generation, limitations. Include human takes
only if `data/human/CONSENT.md` exists.

E: Use the supplied README, report and video drafts. Fill numeric placeholders
only from `reports/*.md`, list unresolved entries in `docs/TODO_PLACEHOLDERS.md`.

Rules: Frozen test evaluation must not be rerun for tuning; label reruns
reproduction. No synthetic substitutes for real takes/ratings. Only authorised
new reports: Phase10 and reproducibility; existing result reports allowed.
Commit and push after each item. End with short `NEXT.md`: done, pending, user.
