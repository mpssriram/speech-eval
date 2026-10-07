# Phase 8 Mode C-lite results

Files: 175; norms version `e9686b646c5e9d96af004b7bacdace75aa7886ebdd1c7f6fbaa22dfea313ba28`; built from clean TRAIN sources only.

Mode C is weaker and more general than same-text comparison. Four sentence features are checked: rate, pitch range, sentence-final loudness drop, and non-final sentence-end pause. No mumbling or awkward-pause detector is offered in Mode C. Zero-spread norm features are not scored.

Comparison setting: A-LOSO Gettysburg/O Captain; B-same-speaker JFK/Reagan. Matching uses the same type/sentence granularity for both systems, not Phase 6 word-level boundaries. Too-quiet truth is trail-only; unsupported single-effect files are omitted. In mixed files only supported types are scored.

| Type | C precision | C recall | Reference precision | Reference recall | C clean alarms/min | Reference clean alarms/min |
|---|---:|---:|---:|---:|---:|---:|
| rushing | 0.013 | 0.146 | 0.889 | 0.195 | 1.314 | 0.000 |
| dragging | 0.000 | 0.000 | 0.242 | 0.211 | 0.219 | 0.000 |
| monotone | 0.016 | 0.200 | 0.208 | 0.444 | 1.459 | 0.219 |
| too_quiet | 0.080 | 0.500 | 0.000 | 0.000 | 0.511 | 0.000 |
| missing_pause | 0.026 | 0.244 | 0.054 | 0.537 | 0.657 | 0.365 |
| overall | 0.020 | 0.179 | 0.106 | 0.324 | 4.159 | 0.584 |

Measured aggregate recall: reference 0.324, Mode C 0.179. This comparison describes controlled synthetic changes, not human performance.

## Between-speaker spread

| Train speaker | Median sentence rate (syllables/s) |
|---|---:|
| lv_amb | 4.013 |
| lv_apc | 3.151 |
| lv_chip | 3.135 |
| lv_dj | 5.199 |
| lv_dl | 3.901 |
| lv_eep | 3.822 |
| lv_fb | 4.422 |
| lv_foxits | 3.896 |
| lv_jn | 4.301 |
| lv_jtm | 3.305 |
| lv_law | 4.235 |
| lv_lb | 2.957 |
| lv_mac | 4.147 |
| lv_mas | 2.896 |
| lv_mb | 3.648 |
| lv_md | 3.034 |
| lv_mk | 4.269 |
| lv_mrg | 3.602 |

## Guidelines and limitations

Number checks use a lexical heuristic: digits always count; number words count when multiword or followed by a non-function token (a noun/unit proxy, not a POS model). “one of the” is excluded. Number-rate ≤ own median, preceding pause ≥0.15 s, ending drop ≥−3 dB and ending rate z≤1 are configurable guidelines only and never alter scores. Opening sentences are identified without a separate penalty.
Actual user takes, independent listening labels, and pitch-rehearsal progress are PENDING. ASR-only inputs use configured fixed-beam CUDA ASR where available under the user’s GPU preference, with deterministic CPU MFA and feature extraction. Automatic transcripts are explicitly unreviewed.
