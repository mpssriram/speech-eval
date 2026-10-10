# Human-take driver (item B)

User permits a synthetic-file workflow test while genuine WAVs are absent.
No detector/scorer/source alignment code changes, no threshold tuning, no fake
consent, annotations, human audio or ratings. Raw recordings stay immutable.

1. RED tests: consent/input gates, number expansion, format normalisation on a
   tiny generated signal, one-to-one interval matching, pause-policy disclosure.
2. Implement separate human driver: expected eight filenames; require consent,
   notes and per-take as-spoken transcript; format-normalise without gain changes;
   real API MFA jobs, A for all, B02/03 vs01, dashboard links/history.
3. Notes support explicit raw-time intervals or declared sentence intervals.
   Report provenance and uncertainty; never infer intended labels from detections.
   Primary counts use IoU>=0.3 for all types; additionally report the historical
   synthetic pause-event centre rule so the differing policies are visible.
4. No genuine files: exercise driver using two licensed clean/injected crops in
   a separate fixture directory, never data/human/raw. Report fixture results
   separately in phase10_human_takes.md and record genuine-input blockers.
5. GREEN/full suite, verify raw/config hashes unchanged, commit/push item B.

Expected: tested fixture normalises/CPU-MFA-aligns and produces A/B dashboard jobs;
human results remain explicitly pending. Read-only review before completion.
