"""Validate real Step 6 artifacts and prove cached reruns preserve frozen files."""
import csv
import hashlib
import json
from pathlib import Path
from collections import Counter
import yaml
from praatio import textgrid
from speecheval.align.base import Alignment, transcript_words
from speecheval.align.pipeline import run_alignment
from speecheval.transcripts import _body_text
from speecheval.verify import _write_json

root=Path.cwd()
rows=list(csv.DictReader((root/'data/manifest/recordings.csv').open()))
assert len(rows)==30
excerpts=yaml.safe_load((root/'data/manifest/excerpts.yaml').read_text())
details=[]
for row in rows:
    rid=row['recording_id']
    transcript=root/'data/transcripts/as_spoken'/f'{rid}.txt'
    body=_body_text(transcript.read_text())
    mask=json.loads((root/'data/transcripts/uncertain'/f'{rid}.json').read_text())
    windows=json.loads((root/'data/alignment/windows'/f'{rid}.json').read_text())
    assert mask['transcript_sha256']==windows['transcript_sha256']==hashlib.sha256(transcript.read_bytes()).hexdigest()
    asr=root/'data/alignment/asr'/f'{rid}.json'
    assert windows['source_asr_sha256']==hashlib.sha256(asr.read_bytes()).hexdigest()
    for key in ('cut_start_s','cut_end_s'):
        assert float(row[key])==windows[key]==excerpts[rid][key]
    for name in ('mfa','whisperx'):
        payload=json.loads((root/'data/alignment'/name/f'{rid}.json').read_text())
        aligned=Alignment.model_validate(payload)
        assert len(aligned.words)==len(transcript_words(body))
        assert [w.text for w in aligned.words]==[w[0] for w in transcript_words(body)]
        assert aligned.uncertain_words==mask['uncertain_words']
        assert aligned.aligner['device']=='cpu'
        tg=textgrid.openTextgrid(str(root/'data/alignment'/name/f'{rid}.TextGrid'),includeEmptyIntervals=False)
        assert set(tg.tierNames)=={'words','sentences'}
        assert len(tg.getTier('words').entries)==sum(w.end>w.start for w in aligned.words)
        counts=Counter(w['type'] for w in aligned.warnings)
        details.append({'recording_id':rid,'aligner':name,'words':len(aligned.words),
                        'uncertain_words':len(mask['uncertain_words']),
                        'interpolated':counts['interpolated'],'oov':counts['oov'],
                        'zero_duration':sum(w.end==w.start for w in aligned.words)})

def snapshot():
    paths=[]
    for directory in ('data/alignment/windows','data/alignment/mfa','data/alignment/whisperx','data/transcripts/as_spoken'):
        paths.extend(p for p in (root/directory).glob('*') if p.is_file())
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

before=snapshot();run_alignment('both');assert snapshot()==before
config=yaml.safe_load((root/'configs/default.yaml').read_text())
assert config['alignment']['primary'] is None
assert not list((root/'data/gold/alignment').rglob('*.TextGrid'))
runs={name:json.loads((root/'data/alignment'/name/'provenance.json').read_text()) for name in ('mfa','whisperx')}
assert all(p['recordings']==30 and p['device']=='cpu' for p in runs.values())
_write_json(root/'data/review/alignment_checks.json',{'recordings':30,'alignments':60,'textgrids':60,
    'all_cuts_and_window_provenance_match':True,'cached_rerun_byte_identical':True,
    'primary_unselected':True,'gold_not_started':True,'runs':runs,'details':details})
lines=['# Day 1 — Step 6 alignment runs','',
       'Completed both CPU forced aligners on the final automatically reviewed transcripts. No human gold or boundary-accuracy claim is made; Step 7a has not started. `alignment.primary` remains null.','',
       '| Aligner | Version | Recordings | Runtime (s) | Jobs/threads |','|---|---|---:|---:|---:|']
for name,version in [('mfa','3.4.2'),('whisperx','3.7.2')]:
    lines.append(f"| {name} | {version} | 30 | {runs[name]['runtime_s']} | 1 |")
lines.extend(['','MFA used english_mfa / english_us_mfa, beam 100, retry beam 400. Corpus validation found 18 OOVs; installed G2P generated all 18 supplementary pronunciations. All state and logs remain inside the project.',
    '', '60 alignment/v1 JSON files and 60 TextGrids passed schema, original-word mapping, monotonic bounds, uncertainty-mask and tier checks. All 30 frozen cuts match excerpts.yaml; transcript and regenerated source-ASR provenance match sentence windows. A normal cached rerun preserves every alignment, TextGrid, frozen window and transcript byte-for-byte.',
    '', '| Recording | Aligner | Words | Interpolated | OOV | Zero-duration | Uncertain |',
    '|---|---|---:|---:|---:|---:|---:|'])
for d in details:
    lines.append(f"| {d['recording_id']} | {d['aligner']} | {d['words']} | {d['interpolated']} | {d['oov']} | {d['zero_duration']} | {d['uncertain_words']} |")
lines.extend(['','## Reproduce','', 'Run from Windows, always entering the WSL checkout:', '', '```powershell',
    'wsl -d Ubuntu -- bash -lc "cd ~/speech-eval && env -u PYTHONPATH ~/.local/bin/uv run speecheval align --aligner both"',
    'wsl -d Ubuntu -- bash -lc "cd ~/speech-eval && env -u PYTHONPATH ~/.local/bin/uv run python scripts/check_alignment.py"',
    'wsl -d Ubuntu -- bash -lc "cd ~/speech-eval && scripts/test.sh -q"','```','',
    'Use `--force` only to explicitly replace frozen sentence windows and rerun both aligners. Ordinary reruns reject changed input provenance. Cached reuse is byte-identical; this does not claim two independent full alignment runs are bit-identical.',
    '', '## Read-only review and limitations','',
    'The review found a frozen-window overwrite bug. Regression tests now protect existing/manual boundaries and reject stale transcript/ASR/cut/padding provenance; only missing windows are created without --force. A stale MFA corpus hardlink is also replaced when the prepared audio inode changes. Both tests were observed failing before the fixes and passing afterward.',
    '', 'Minor deferred robustness issues: per-word interpolation flags are dropped by the shared schema, although warnings remain (none of the 30 original calibration alignments was interpolated); MFA installation lookup is specific to this user. Neither affected these runs. The reviewer declined to judge human transcript truth, boundary accuracy without gold, or generalization of the proxy calibration false-acceptance rate. Final WhisperX artifacts were checked by the execution script after the review finished.',
    '', 'Both aligners map all 7,671 transcript words. MFA has no zero-duration or interpolated entries. WhisperX has 28 zero-duration entries after overlap repair (listed above); they remain in JSON, but cannot be represented as nonzero TextGrid intervals. They require later boundary QA, not invented durations. Neither aligner has interpolated entries in this run.',
    '', 'Three-way ASR agreement remains a proxy, not human ground truth. Uncertain words are propagated for exclusion downstream; alignment completion does not resolve them. Stop before Step 7a.',''])
(root/'reports/day01_alignment_runs.md').write_text('\n'.join(lines))
print('PASS: 30 cuts/windows, 60 JSON + 60 TextGrids, masks/word maps/times, byte-identical cached rerun; no gold/primary')
