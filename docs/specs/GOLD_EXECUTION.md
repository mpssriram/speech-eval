# Step 7a execution ledger

Base: 87a715b. User said continue after Step 6. Execute the existing day01 Step 7a preparation only, then STOP at human annotation. Work remains in the authorized WSL checkout/main; commit and push the completed preparation.

Pre-flight: both aligners use the same original transcript indices and final uncertainty masks. Their schema includes all words, including zero-duration ones. Templates require duration >=0.15 s in both aligners; never use unreviewed averages as human gold.

Ruling: interpret the spec's every-kth sampling as a rounded fractional stride over eligible words so exactly 20 unique samples span the full recording, including both ends. An integer floor stride can sample only half of a small eligible list. Cost if wrong: sample indices differ from a particular unstated integer-k convention; selection is frozen and disclosed.

Ruling: exclude uncertain and interpolated words from sampling under AGENTS section 6.1; do not let unreliable reference evidence enter the gold comparison. Cost if wrong: fewer eligible words, in which case preparation fails rather than weakening the threshold.

Ruling: preserve existing/manual todo templates and reject changed input provenance or modified templates. No automatic force overwrite is added. Cost if wrong: regeneration after input changes needs an explicit preservation/resolution step, protecting human work.

Tests first: initial collection failed because the gold implementation did not exist. Implemented selection, averaged padded boundaries, eligibility exclusions, insufficient-candidate rejection, frozen provenance and safe reruns. One fixture assumed praatio tierNames was a list rather than its actual tuple; corrected only that framework-type expectation. Full suite then passed 67/67. Actual CLI generated three unreviewed templates and reused them on rerun.

Final review: independent read-only reviewer confirmed the real highest clean LUFS selection (lv_fb, -22.405), all 60 candidate intervals, hashes and safe reruns. Missing loaded alignment schema/identity validation was regraded Important: valid but misfiled JSON, or MFA copied into the WhisperX location, would silently bias the independent average. Fixed in the single root fix pass: two identity regressions RED -> GREEN, shared Alignment schema validated before any writes. No deferred minors.

Final: Ruling: reviewer set aside acoustic boundary correctness and human annotation quality; templates explicitly remain unreviewed, and execution stops for human annotation. Cost if wrong: model averages mistaken for truth would invalidate the bake-off, so no such claim is allowed.

Final: Ruling: reviewer set aside downstream bake-off/evaluation and model pipeline behavior; no such stages or models were run or modified in this task. Cost if wrong: later stages remain unverified; Step 7b must verify them rather than extrapolate from these template checks.

Task complete: full suite 69/69 passed; `scripts/check_gold.py` passed all 3 templates / 60 intervals, independent average/padding and exclusions, all hashes and byte-identical cached preparation. No final human gold files exist. Handoff stops at USER Step 7a annotation, with instructions in reports/day01_gold_annotation.md.
