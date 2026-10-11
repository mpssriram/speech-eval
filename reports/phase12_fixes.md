# Phase 12 fixes

## 1. Explanation display

Presentation only: a response-only `display_explanation` fixes old cached jobs as
well as new results. Stored explanation strings and all numeric evidence,
regions, scores, v1/v2 code/configuration and scientific outputs stay unchanged.
The dashboard uses the presentation field, two-decimal seconds, one-decimal
rates and fixed-point chart labels. Pauses below 0.02 seconds display as no
pause; absolute z greater than 10 displays as "more than 10 SD".

There is no final pause-specific sigma floor in v1. The reference builder does
have a generic 0.001 floor on the pooled transformed scale, before shrinkage;
this must not be described as no floor anywhere. Tiny resulting spreads can
still produce extreme z. No sigma/threshold change was made. Any future v2
sigma-floor change would be post-hoc, not part of the frozen published v2.

Two regression tests first failed, then passed: the 6.9e-18 / z=6046 cached API
case, preserving stored JSON bytes and raw evidence; and pause/z boundaries,
fixed-point rates and Mode B wording. The full Python suite passes. Production
dashboard build passes with the existing harmless Plotly size advisory.
All three real Chromium smoke tests pass (40.0 s), covering actual upload,
waveform/region selection, score/evidence cards, participant and same-words
baseline playback, recording controls, A/B/C and mobile overflow. All five
requested screenshots were regenerated. A first browser run caught a defect
in the newly added SD-check regex (it matched the fractional part of 7.12);
that assertion was corrected, not hidden or worked around in production.
Six PDF pages were inspected individually; two renders match SHA256
`8a61d849a8c940263da1ef16259bc607e4fd8d20a29c9099dbdcf0ebfa7f97e1`.
The report example is the exact new display string generated from unchanged
analysis `86964ad39ead`; it is not a new evaluation or a rewritten frozen output.
Docker startup was retried non-destructively; the Linux-engine pipe is still
missing. Live tests used WSL API + Node 22.14.0 dashboard, not Docker.

## 2. Mode B precision diagnosis (DEV only)

The published B cohort contains only JFK/Reagan test speakers; there are no
JFK/Reagan DEV B rows. I did not open those test files. Instead this investigation
used all 152 DEV Gettysburg/O Captain variants (four original readers), each
edited file against its own original, with frozen v1 settings and the existing
same-type IoU >=0.3 / pause-centre <=0.25 s matcher and uncertainty exclusions.
This is a DEV diagnostic cohort, not a replacement for published B precision.
No human input was used and no threshold was selected.

DEV: 624 predictions, 164 eligible truths, 70 hits, 94 misses, 554 false
positives; precision 0.112, recall 0.427, F1 0.178. The four exact self-comparison
controls produce zero flags (0.000 clean alarms/min); edited files still have
many false positives. Per-type counts:

| Type | Predicted | Truth | Hits | FP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| rushing | 12 | 24 | 6 | 6 | 0.500 | 0.250 | 0.333 |
| dragging | 6 | 23 | 5 | 1 | 0.833 | 0.217 | 0.345 |
| monotone | 9 | 23 | 9 | 0 | 1.000 | 0.391 | 0.563 |
| too_quiet | 4 | 24 | 4 | 0 | 1.000 | 0.167 | 0.286 |
| mumbling | 11 | 24 | 11 | 0 | 1.000 | 0.458 | 0.629 |
| awkward_pause | 569 | 23 | 23 | 546 | 0.040 | 1.000 | 0.078 |
| missing_pause | 13 | 23 | 12 | 1 | 0.923 | 0.522 | 0.667 |

Position is relative to the nearest injected interval of any type; an inside
wrong-type flag is still a false positive. Distances are edge-to-edge seconds:

| FP type | Position | Count | Distance median s | p95 s | Maximum s |
|---|---|---:|---:|---:|---:|
| awkward_pause | before | 284 | 30.06 | 69.87 | 98.90 |
| awkward_pause | after | 232 | 22.72 | 71.34 | 87.42 |
| awkward_pause | inside | 19 | 0.00 | 0.00 | 0.00 |
| awkward_pause | overlap | 11 | 0.00 | 0.00 | 0.00 |
| rushing | inside | 5 | 0.00 | 0.00 | 0.00 |
| rushing | overlap | 1 | 0.00 | 0.00 | 0.00 |
| dragging | inside | 1 | 0.00 | 0.00 | 0.00 |
| missing_pause | inside | 1 | 0.00 | 0.00 | 0.00 |

Awkward-pause FP by injected variant: awkward_pause 62, dragging 81,
missing_pause 64, mixed_01 13, mixed_02 16, monotone 78, mumbling 86, rushing 72,
too_quiet 74. There are 374 outside-edit awkward-pause alarms on files with
zero global gain. The median absolute participant/reference pause difference
among pause false positives is only 0.008 s (p95 0.690 s; max 0.930 s).
Awkward-pause FP absolute z median 7.967, p95 2952.000, max 3260.000.

Checks and conclusions:

- After the last edit, actual real-MFA word-start residual versus the mapped
  original has median 0.003 s / p95 0.009 s / max 1.153 s. Against the UNshifted
  original it is 0.287 / 2.204 / 4.153 s. The shift is being handled; independent
  MFA reruns have nonzero jitter and some large local outliers. There is no
  evidence of a systematic forgotten post-edit shift.
- Detection reads independently rerun MFA/features, not oracle time maps.
  Stored oracle edge checks have median zero / p95 0.000301 s, but two insertion
  discontinuities differ by 1 or 3 seconds when replaying rounded map knots:
  Gettysburg lv_pc mixed_01 word212 end and lv_rk mixed_01 word234 start (zero-
  based). Millisecond serialization loses side ownership at a rounded insertion
  knot. This is an oracle/map QA limitation, not an identified cause of live B
  false positives; the detector does not consume those oracle edges. Do not
  claim every oracle edge passed or silently repair the frozen corpus.
- HQ prefix/suffix samples outside edits match the time-shifted source after
  accounting for logged global attenuation: maximum difference 0.596 PCM16 LSB;
  no file exceeds two LSB. HQ sample rate is unchanged at 44.1 kHz. PSOLA/stretch
  operate on local crops; 16 kHz resampling is for separate MFA copies. Common
  anti-clipping gain is applied to 37 edited files and is logged, not hidden.
  Mixed labels repeat the TOTAL recording gain on each of their three flaws;
  summing that repeated value would incorrectly triple attenuation.
- Map/output duration differences are below 0.000499 s. Exact duplicate
  predictions: zero. Overlapping distinct types are not duplicate regions.

The evidence points to independent alignment jitter amplified by a tiny pause
spread, plus the lack of a minimum practical pause excess in v1, rather than a
demonstrated B timing/processing implementation bug. Adding an effect minimum
would be a detector change, not a display or bug fix. Investigation stops here:
no scientific code/configuration changes, no new test evaluation, no claim that
the published test cohort has been diagnosed from its measurements.

Reproduce from the root in WSL:

```sh
env -u PYTHONPATH ~/.local/bin/uv run python scripts/diagnose_mode_b_dev.py
# Add --rows to also print every FP recording/type/interval/position/distance.
```

The sorted per-FP rows SHA256 is
`96eb127dcf0139541ddc7e5c8af87b0d6433e26b1c46f341fd0fe722011f7a27`.
Two further diagnostic runs produced byte-identical JSON stdout, SHA256
`442603fc4c358a952b6e6371768f68cee6cba305280b491505121e0388fec96c`;
two-run computation took 78.630 s. Investigation stayed within the two-hour
timebox (under one hour including verification). Frozen scientific hashes and
the original v2 one-shot marker remain unchanged. Full suite: 277 tests passed.

## 3. Genuine-take review / confirmation gate

Created `data/human/review/TAKES_REVIEW.md`: all eight actual ASR drafts paired
with canonical units, marked suggested word differences, complete editable
transcript blocks, verbatim recorder notes and reference word-span locations.
The PDF plans are separate and unconfirmed, not inferred performed labels.
Gettysburg04 / Reagan04 (global08) are spontaneous mixed readings; types and
locations remain unspecified. "No issues" on global06 is not silently replaced
by the PDF plan. ASR is not ground truth or listening.

An independent document-reader check found no obvious out-of-order ASR row
assignment. Its actionable clarifications were applied: exact splitter rules,
review-form-to-validator notes conversion, validation-only command, and the
scope of "No issues". The duplicate "or" reference match was narrowed to the
recorder's specified unit2. Canonical punctuation is preserved in the reference
column. This is AI document review, NOT independent speech ratings/annotations.

BLOCKED: none of the eight take sections has recorder `CONFIRMED`. Existing
prose notes lack the required explicit complete JSON annotations and confirmed
as-spoken files are still absent. No raw/original audio, consent, source drafts,
user notes or transcripts were changed. Real human A/B evaluation, dashboard
jobs and hits/misses/FP remain unrun/unclaimed. After confirmation: v1 primary;
Mode A all available takes, B02/B03 versus same-text A01, primary all-type
IoU>=0.3; frozen v2 separately labelled post-hoc. Never tune on these takes.

Verification: all eight editable transcript blocks match their actual ASR
draft bodies exactly; all sixteen original/raw hashes still match the import
manifest. The existing validator rejects the missing explicit notes JSON, and
all eight final transcript paths are absent. All frozen v2 code/config hashes
and its one-shot marker pass read-only verification. Review document SHA256:
`ef7289d8f313610ab9ee5b84dff80e485b187515a26876679edd4b06a9ce8de2`.

## 4. Independent rating pack

Added one-page plain-English `data/rating_pack/INSTRUCTIONS.md`, allowing about
15 minutes: listen independently to the twelve randomized clips in CSV order,
score overall delivery 1–5, enter only supported flaw names and corresponding
times, save a separately named CSV and return it through the sender's channel.
This matches the actual five-column form. No answer key, system scores or
ratings are supplied. The blank form remains unchanged; zero independent
responses. Report and pending box now say agreement is pending, not unavailable
before the deadline. AI or recorder self-ratings are not rater data.

Document-reader checks clarified skipped rows (preserve clip names; other fields
empty) and uncertainty (replay or skip, never use `none` to mean unsure). Exact
CSV fields and all twelve clip names were checked; all responses remain blank.
Instructions fit one printable A4 page; SHA256
`b17e011ba84aa2438ba561fed7477caaa265ad070b7abc5647139c7d9e9b9f50`.
Updated report rendered twice byte-identically as six A4 pages, every page
visually inspected, PDF SHA256
`221b408343e9094b769a34360660dbfca5f547244772821996e87a4a2d371f8c`.
The real browser suite also passed all three tests at `http://localhost:8080`
(34.9 s), including A/B/C, phrase playback and mobile layout with zero page
errors. Its screenshots and machine verification were refreshed; this is
functional evidence, not new detector-performance or human-rating evidence.

## 5. Report wording / footer

Replaced the bold Claude shorthand with the requested unbolded disclosure:
"Boundaries were placed visually from waveform and spectrogram by an AI
assistant (Claude), without listening; a human spot-check is pending."
Retained the independence limitation. Section 6.1 now plainly states that v2
halves A clean alarms (1.341 to 0.671/min) but lowers recall (0.400 to 0.288);
F1 is effectively unchanged (0.190 to 0.193), not literally identical. V1 stays
primary. All values were already published; no new scientific numbers or test
evaluation. Removed "human evidence pending" only from the page footer;
the honest limitations and final pending box remain.

Two presentation regression tests first failed on the old wording/footer,
then passed after these edits. No detector/configuration/threshold changes.

Full suite: 279 passed in 26.84 s. Updated PDF rendered twice byte-identically,
six A4 pages; every final page visually inspected. SHA256:
`4e6d7fd4f6018e57baeb718bb61b2f3c798a882c5c6b28633926636d1fd6909a`.

## Application readiness for local testing

Live dashboard/API: `http://localhost:8080` (WSL API plus clean Linux Node
22.14.0/Vite frontend, NOT Docker). All three real-browser tests pass, with no
page errors, on desktop and mobile viewports. Production bundle builds; the
known large Plotly bundle warning remains. Live health returns nonnull git
metadata and the unchanged frozen v1 detector config hash.

The existing fixture helpers were exercised directly, without the report-writing
driver: real CPU MFA 3.4.2, licensed clean/injected crops only, A for both crops
and B for the injected crop against the clean one. The genuine human folder,
consent, notes and Phase10 report hashes were checked unchanged. No human take
was processed. The injected rushing region was missed in A and B (each: zero
hits, one miss, zero FP); clean A has no flags. This proves functional completion,
not useful sensitivity. No tuning followed. Synthetic-only completed jobs:

- [Clean fixture A](http://localhost:8080/results/c8094811702e1bb057799eb2)
- [Injected fixture A](http://localhost:8080/results/62ed557c7f38790be77c43e2)
- [Injected fixture B](http://localhost:8080/results/7b661cf50588fec352dba93a)

Browser recording used its synthetic test device; the user's real microphone
permissions and recording experience are not claimed verified. Genuine A/B
counts remain gated on the eight recorder confirmations and complete inputs.
Docker-dependent fresh-clone v2 reproduction/total-disk measurement remain
blocked; host tests do not substitute for those. Restart/test steps are in NEXT.

## Docker recovery / documentation packaging regression

Docker Desktop's Linux engine and WSL integration became available during the
final read-only retry. This supersedes the earlier startup blocker; no reset,
data deletion, pruning or settings rewrite was performed.

A new GitHub clone at `/tmp/speech-eval-phase12-AiGgHp/clone` exposed a real
packaging problem: the image omitted README/docs required by documentation
regression tests. Three tests failed with missing `/app/README.md`, report
source and PDF renderer. Fixed only Dockerfile COPY instructions to include
README/docs, rather than skipping those tests. The complete rebuilt CPU image
suite passes: 279 tests in 41.71 s. No scientific code/configuration change.
The first frozen v2 reproduction also matched the published JSON hash; repeated
post-commit verification and container browser/disk checks follow below.
