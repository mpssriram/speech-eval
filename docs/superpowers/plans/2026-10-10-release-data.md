# Licensed release and fresh-clone reproduction

Authority: user items A–E and Downloads/speech-eval-drafts/codex_tasks_C_D_E.md.
Execute inline, autonomously; user authorises main-branch commits and pushes.

## Design
Use a deterministic standard-library ZIP, a committed per-file inventory and
separate primary-source licence ledger. Pin the archive SHA in dataset.yaml.
Import inside Docker, never overwrite differing existing files or follow
symlinks, verify the outer hash and every payload hash before installation.
Include only the frozen dataset, its licensed originals and measured provenance;
exclude human recordings, application uploads and inactive sources.

## Task 1: builder/importer
Write tests first for deterministic ZIP generation, licence provenance,
successful/idempotent import, corruption, unsafe members, symlinks, existing
conflicts and missing download URL. Run RED, implement, run GREEN and full suite.
Interfaces: builder produces inventory/archive; importer consumes trusted
inventory/config; Make invokes importer before frozen numeric reproduction.
Expected: all tests pass; unsafe input writes no dataset files.

## Task 2: actual release
Build archive twice and compare SHA; add inventory/config/licence evidence and
Make dependency. Verify unit suite, commit and push implementation checkpoint.
Expected: identical ZIP hashes; frozen detector/scorer bytes unchanged.

## Task 3: GitHub clone
Clone origin into mktemp directory. Import using --from-local in Docker only;
run quick/full twice without changing settings. Save stable output hashes and
timings in reports/reproducibility.md; runtime metadata is not scientific output.
Expected: REPRODUCED OK twice and byte-identical scientific outputs; quick <900s.
Update blockers and Docker instructions, review, commit and push item A.

Review focus: untrusted ZIP path traversal/symlinks/duplicates, interrupted
installation, provenance closure, no unpublished checkout dependency, no
threshold tuning or claims of human listening/ratings.
