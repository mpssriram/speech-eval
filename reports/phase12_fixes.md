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
