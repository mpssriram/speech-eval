# Execution decisions and deferred review items

Items A-E were implemented in the authorised main checkout, with scoped commits
and pushes. No frozen detector/scoring thresholds changed. This preserves the
decisions from the temporary execution ledgers before their recoverable cleanup.
Order below follows each ledger; repeated decisions are retained deliberately.

## Rulings I made

1. Exclude the unlicensed legacy participant fixture despite the historical
   freeze listing it: no indexed scientific consumer needs it. Cost if wrong:
   reproduction must fail rather than substitute private audio.
2. Accept hash-verified global provenance for the audit-only clipped LibriVox
   source, matching the unchanged reference fallback. Cost if wrong: frozen
   Docker reproduction rejects it.
3. Use a release-only historical Phase7 validation adapter exempting precisely
   that unused unlicensed fixture, verifying other historical inputs and restoring
   the hook after Mode C. Cost if wrong: scientific hash/number comparisons fail.
4. Retain primary institutional licensing evidence with a US caveat despite the
   reviewer declining independent legal validation. Cost: other jurisdictions
   still require user rights review.
5. Preserve frozen scientific code/configuration and call reruns reproduction;
   scientific validity was not independently re-reviewed. Cost: existing
   methodological limitations remain.
6. Use executor-run integration, tests and GitHub-clone verification where the
   reviewer did not rerun them; no second review. Cost: no independent post-fix
   execution review.
7. Choose deterministic ZIP instead of tar.zst for standard-library import.
   Cost if wrong: compression ratio, not scientific results.
8. Push a checkpoint before fresh GitHub-clone verification so the remote has
   the importer. Cost: extra focused commits within A.
9. Use native ledgers because the installed helper scripts have unusable CRLF
   shebang paths. Cost: manual bookkeeping.
10. Require explicit as-spoken transcripts and structured intended-region notes,
    rather than infer unheard words. Cost: extra user annotation.
11. Report primary strict IoU >=0.3 for every human flaw type and separately the
    historical synthetic pause-centre rule. Cost: two labelled matching columns.
12. Show completed takes using existing dashboard links/history, not a gallery
    without genuine inputs. Cost: hashed job IDs need a take-name lookup.
13. Regrade malformed notes from minor to important: otherwise a crash hides an
    actionable blocker. Cost if wrong: stricter notes schema.
14. Treat consent/annotation authenticity as pending and use executor workflow
    tests rather than imply genuine validation. Cost: human review still needed.
15. Keep existing dashboard links/history instead of adding a gallery (final
    review reaffirmation). Cost: hashed IDs require report aliases.
16. Bind host report/docs paths and separate public dashboard URL from internal
    Docker DNS. Cost: documented driver commands use a POSIX repository shell.
17. Follow the supplied autonomous spec without design approval pauses. Cost
    if wrong: later correction of design choices.
18. Build training-only rating clips using frozen full-context detection projected
    into visible spans and rescored for clip duration. Cost: human listeners see
    isolated clips while the detector used surrounding context.
19. Distribute only the blind folder; keep the answer key outside it but in the
    repository. Cost: a rater given repository access can unblind themselves.
20. Use a native rating-pack ledger for the same CRLF helper issue. Cost: manual
    bookkeeping may omit checkpoints.
21. Regrade type/time pairing from minor to important because sorting types
    corrupted timestamp meaning. Cost if wrong: retain declared unsorted order.
22. Keep rating-pack perceptual/population/short-clip and external-rights caveats;
    rely on executor repeated builds and primary evidence, not independent
    validity claims. Cost: no independent human or legal validity established.
23. Keep unsupported draft numbers and proposed formal licensing grants pending,
    instead of estimating them. Cost: submission still needs owner input/evidence.
24. Retain the separately supplied archive prerequisite until its actual URL is
    uploaded. Cost: a public clone alone cannot download the dataset yet.
25. Submission reader declined PDF layout, perceptual realism, legal validity,
    human accuracy, worldwide licensing, repeat execution and future video
    fidelity. Use executor PDF inspection/repeat proof and disclose all remaining
    evidence gaps. Cost: no independent validation of those gaps.
26. Correct PDF determinism at the document template rather than only a partial
    canvas constructor; the template overrode that setting. Cost if wrong:
    repeat-byte verification fails. Authoring check observed RED, then GREEN.

## Deferred minors

- ZIP metadata/compression defaults across platforms: byte identity is proved
  only for the tested Linux Python 3.11 builder.
- Unsafe-member tests currently reject membership first; there is not a dedicated
  direct test of the path-validation helper itself.

No remaining B/C important finding is deferred. Genuine recordings, ratings,
archive hosting, author/licence confirmation and the recorded video are user-input
blockers, not minor review findings. See `BLOCKERS.md` and `../NEXT.md`.
