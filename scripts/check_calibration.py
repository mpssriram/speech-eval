"""Verify masks, proxy-control constraints, seeded replay and fresh CPU inference."""
import csv
import gc
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from collections import Counter

import cmudict
import yaml
from rapidfuzz.distance import Levenshtein
from speecheval.calibrated import calibration_controls, lexical_spans, LocalScorer
from speecheval.transcripts import _body_text, normalize_tokens
from speecheval.verify import _write_json

root=Path.cwd()
audit=json.loads((root/'data/review/acoustic_verification_calibrated.json').read_text())
controls=json.loads((root/'data/review/ctc_calibration.json').read_text())['controls']
inputs=json.loads((root/'data/review/verification_input.json').read_text())
config=yaml.safe_load((root/'configs/default.yaml').read_text())
rows={r['recording_id']:r for r in csv.DictReader((root/'data/manifest/recordings.csv').open())}
assert len(controls)==300 and len({c['recording_id'] for c in controls})==30
assert Counter(c['kind'] for c in controls)=={'substitution':100,'deletion':100,'insertion':100}
pronunciations=cmudict.dict()
for control in controls:
    if control['kind']=='substitution':
        body=_body_text(inputs['transcripts'][control['recording_id']]);a,b=lexical_spans(body)[control['word_index']]
        word=''.join(normalize_tokens(body[a:b]))
        assert any(1<=Levenshtein.distance(x,y)<=2 for x in pronunciations[word] for y in pronunciations[control['variant']])
assert len(audit['items'])==85
assert sum(audit['counts'].values())==85
assert sum(c['delta_nats']>=audit['margin_total_nats'] for c in controls)/300<=.02
for rid,sha in audit['output_transcript_sha256'].items():
    path=root/'data/transcripts/as_spoken'/f'{rid}.txt'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sha
    assert '# reviewed: auto-acoustic-calibrated' in path.read_text()
    uncertain=json.loads((root/'data/transcripts/uncertain'/f'{rid}.json').read_text())
    assert uncertain['transcript_sha256']==sha
    assert all(0<=i<len(lexical_spans(_body_text(path.read_text()))) for i in uncertain['uncertain_words'])
    windows=json.loads((root/'data/alignment/windows'/f'{rid}.json').read_text())
    assert windows['transcript_sha256']==sha
alignments={rid:json.loads((root/'data/review/original_alignment'/f'{rid}.json').read_text()) for rid in rows}
with tempfile.TemporaryDirectory(prefix='seed-replay-',dir=root/'data/.cache') as tmp:
    replay=Path(tmp)
    for directory in ('data/alignment/asr','data/audio/align16k'):
        target=replay/directory;target.mkdir(parents=True)
        for source in (root/directory).glob('*'):
            if source.is_file():shutil.copyfile(source,target/source.name)
    for source in ('data/review/acoustic_verification_legacy.json','data/review/calibration_medium_asr.json'):
        target=replay/source;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/source,target)
    shutil.copytree(root/'data/review/medium_full_asr',replay/'data/review/medium_full_asr')
    sampled=calibration_controls(replay,inputs,rows,alignments,config['transcript_verification'])
    assert sampled==json.loads((root/'data/review/calibration_controls.json').read_text())['controls']
item=next(i for i in audit['items'] if i.get('score_a') is not None and i['window']['end_s']-i['window']['start_s']<5.)
w=item['window'];results=[]
for _ in range(2):
    with tempfile.TemporaryDirectory(prefix='ctc-fresh-',dir=root/'data/.cache') as tmp:
        scorer=LocalScorer(root,config['transcript_verification']);scorer.directory=Path(tmp)
        emission,_=scorer.emissions(root/'data/audio/align16k'/f"{item['recording_id']}.wav",w['start_s'],w['end_s'])
        results.append({'emission_sha256':hashlib.sha256(emission.numpy().tobytes()).hexdigest(),
                        'a':scorer.score(emission,w['candidate_a']),'b':scorer.score(emission,w['candidate_b'])})
        del scorer,emission;gc.collect()
assert results[0]==results[1]
assert abs(results[0]['a']-item['score_a'])<1e-8 and abs(results[0]['b']-item['score_b'])<1e-8
_write_json(root/'data/review/calibration_checks.json',{'controls':300,'all_recordings':30,'phonetic_substitutions_checked':100,
    'seed_replay_identical':True,'fresh_cpu_identical':True,'fresh_cpu_scores':results[0],
    'mask_and_window_hashes_match_all_transcripts':True})
print('PASS: 300 controls/30 recordings, 100 phonetic substitutions, all masks/windows, exact seed replay, uncached CPU emissions/scores')
