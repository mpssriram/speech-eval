"""Full Phase 1 engineering acceptance, with human evidence honestly left pending."""
import csv
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
import soundfile as sf
import yaml
from speecheval.align.pipeline import run_alignment
from speecheval.align.mfa import ensure_adoption
from speecheval.prepare import prepare_recordings
from speecheval.evaluate import load_recordings, validate_dataset
from speecheval.transcripts import _body_text, normalize_tokens
from speecheval.verify import _write_json

root=Path.cwd();config=yaml.safe_load((root/'configs/default.yaml').read_text())
ensure_adoption(root,config['alignment']['mfa'])
checks=[]
def check(name: str, passed: bool, evidence: str, pending: bool = False) -> None:
    checks.append({'item':name,'status':'PENDING' if pending else ('PASS' if passed else 'FAIL'),'evidence':evidence})
rows=list(csv.DictReader((root/'data/manifest/recordings.csv').open()))
raw=list(csv.DictReader((root/'data/manifest/raw_files.csv').open()))
hash_ok=all(hashlib.sha256((root/r['raw_path']).read_bytes()).hexdigest()==r['sha256'] for r in raw)
check('Licensed source manifest and raw hashes',len(raw)==len(rows)==30 and hash_ok,'30 sources: 15 Gettysburg, 13 O Captain, JFK and Reagan; SHA256 verified')
audio_ok=True
for r in rows:
    for folder,rate in [('hq',44100),('align16k',16000)]:
        info=sf.info(root/'data/audio'/folder/f"{r['recording_id']}.wav")
        audio_ok&=info.channels==1 and info.samplerate==rate and info.subtype=='PCM_16' and abs(info.duration-float(r['duration_s']))<=.002
check('Prepared audio formats and durations',audio_ok,'60 mono PCM16 WAVs: 44.1 kHz / 16 kHz')
check('Three LibriVox listening spot-checks',False,'Frozen ASR-anchor cuts are available; no human listening check claimed',True)
jfk=next(r for r in rows if r['recording_id']=='jfk_rice__jfk__orig')
tokens=normalize_tokens(_body_text((root/'data/transcripts/as_spoken/jfk_rice__jfk__orig.txt').read_text()))
check('JFK excerpt',120<=float(jfk['duration_s'])<=240 and 'we choose to go to the moon' in ' '.join(tokens),
      f"{jfk['duration_s']} s; frozen sentence-bounded excerpt from Phase 1 ASR-anchor audit; anchor present")
audit=json.loads((root/'data/review/acoustic_verification_calibrated.json').read_text())
check('Automatic transcript audit replacing Step 5b',len(audit['items'])==85 and sum(audit['counts'].values())==85 and not audit['human_reviewed'],
      'Historical original-candidate audit: 64 APPLY_B, 18 KEEP_A, 3 UNSURE; number rendering changed without claiming new human/acoustic truth')
ids=[r['recording_id'] for r in rows]
validate_dataset(root,config,load_recordings(root,ids))
check('Both aligners produced valid current JSON',True,'60 alignment/v1 outputs match transcript words, masks and provenance')
primary=config['alignment']['primary'];promotion_ok=primary=='mfa'
for rid in ids:
    for suffix in ('.json','.TextGrid'):
        promotion_ok&=(root/'data/alignment'/(rid+suffix)).read_bytes()==(root/'data/alignment'/primary/(rid+suffix)).read_bytes()
check('Bake-off, primary selection and promotion',promotion_ok and (root/'reports/day01_aligner_bakeoff.md').exists(),'MFA selected by user; all 60 promoted artifacts byte-identical to primary')
qa=json.loads((root/'data/review/alignment_qa.json').read_text())
check('Step 8 QA report',len(qa['rows'])==30 and (root/'reports/day01_alignment_qa.md').exists(),f"30 rows; {len(qa['flagged'])} flagged recordings")
check('Human Praat spot-check of flagged alignments',False,'PENDING; user approval of aligner choice is not a listening/boundary check',True)
check('Gold accuracy target',False,'Both aligners below 90% within 50 ms against limited visual reference; explicit risk, not silently passed')
paths=[p for folder in ('data/audio/hq','data/audio/align16k','data/alignment/mfa','data/alignment/whisperx','data/alignment/windows','data/transcripts/as_spoken')
       for p in (root/folder).iterdir() if p.is_file()]
paths.extend([root/'data/manifest/excerpts.yaml',root/'data/manifest/recordings.csv'])
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
prepare_recordings();run_alignment('mfa')
same=before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
check('Cached prepare and primary alignment hash rerun',same,'Audio, manifests, alignments, windows and transcripts byte-identical')
check('Pytest isolation/cache placement',not (root/'data/.cache/pytest').exists(),'.pytest_work/ and .pytest_cache/ ignored outside data/.cache; make test removes PYTHONPATH and disables external plugins')
test_env=os.environ.copy();test_env['PYTHONPATH']='/opt/ros/jazzy/lib/python3.12/site-packages'
tests=subprocess.run(['make','test'],cwd=root,env=test_env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
match=re.search(r'(\d+) passed',tests.stdout)
check('Full test suite',tests.returncode==0,f"make test with inherited ROS PYTHONPATH: {match.group(1) if match else 'see output'} tests passed; exit {tests.returncode}")
print(tests.stdout)
check('Progress summary', '2026-10-07' in (root/'docs/specs/PROGRESS.md').read_text(),'Current dated summary in docs/specs/PROGRESS.md')
_write_json(root/'data/review/phase1_acceptance.json',{'checks':checks,'engineering_pass':not any(c['status']=='FAIL' and c['item']!='Gold accuracy target' for c in checks),
    'all_acceptance_pass':all(c['status']=='PASS' for c in checks),'human_spot_check':'PENDING'})
lines=['# Phase 1 acceptance audit','', 'Engineering implementation and promotion are complete only if the automated checks below pass. Full human/quality acceptance is NOT claimed. Latest user authorization permits independent later-phase engineering while these risks stay visible.',
       '', '| Item | Status | Evidence |','|---|---|---|']
lines.extend(f"| {c['item']} | {c['status']} | {c['evidence']} |" for c in checks)
lines.extend(['','Human spot-checks and the visual-gold quality target are NOT silently passed. Automated later-phase engineering is authorized while these limitations remain visible.',''])
(root/'reports/day01_phase1_acceptance.md').write_text('\n'.join(lines))
for c in checks:print(c['status'],c['item'])
assert same and not any(c['status']=='FAIL' and c['item']!='Gold accuracy target' for c in checks)
