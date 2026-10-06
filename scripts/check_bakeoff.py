"""Verify completed bake-off evidence, source preservation and all current alignments."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from praatio import textgrid
import yaml
from speecheval.align.base import Alignment
from speecheval.align.pipeline import run_alignment
from speecheval.evaluate import evaluate_alignment, expand_numbers, load_recordings, validate_dataset, validate_migration
from speecheval.transcripts import _body_text, normalize_tokens

root=Path.cwd();audit=json.loads((root/'data/review/alignment_bakeoff.json').read_text())
config=yaml.safe_load((root/'configs/default.yaml').read_text())
rows=list(csv.DictReader((root/'data/manifest/recordings.csv').open()))
assert len(rows)==30
hashes=validate_dataset(root,config,load_recordings(root,[r['recording_id'] for r in rows]))
assert hashes==audit['inputs']['scored_artifact_hashes']
excerpts=yaml.safe_load((root/'data/manifest/excerpts.yaml').read_text())
changed=set(json.loads((root/'data/review/number_expansion.json').read_text())['changed_recordings'])
for row in rows:
    rid=row['recording_id'];window_path=root/'data/alignment/windows'/f'{rid}.json'
    windows=json.loads(window_path.read_text())
    assert windows['source_asr_sha256']==hashlib.sha256((root/'data/alignment/asr'/f'{rid}.json').read_bytes()).hexdigest()
    for edge in ('cut_start_s','cut_end_s'):
        assert windows[edge]==float(row[edge])==excerpts[rid][edge]
    if rid not in changed:
        assert window_path.read_bytes()==(root/'data/review/before_number_expansion/windows'/f'{rid}.json').read_bytes()
    for name in ('mfa','whisperx'):
        payload=json.loads((root/'data/alignment'/name/f'{rid}.json').read_text())
        tg=textgrid.openTextgrid(str(root/'data/alignment'/name/f'{rid}.TextGrid'),includeEmptyIntervals=False)
        assert set(tg.tierNames)=={'words','sentences'}
        assert len(tg.getTier('words').entries)==sum(w['end']>w['start'] for w in payload['words'])
for row in csv.DictReader((root/'data/manifest/raw_files.csv').open()):
    assert hashlib.sha256((root/row['raw_path']).read_bytes()).hexdigest()==row['sha256']
selection=json.loads((root/'data/gold/alignment/todo/selection.json').read_text())
migration=json.loads((root/'data/review/number_expansion.json').read_text())
validate_migration(root,selection,migration)
for rid,record in migration['recordings'].items():
    old=root/'data/review/before_number_expansion/transcripts'/f'{rid}.txt'
    current=root/'data/transcripts/as_spoken'/f'{rid}.txt'
    expected,mapping=expand_numbers(old.read_text())
    assert current.read_text()==expected
    assert record['old_to_new']=={str(k):v for k,v in mapping.items()}
    assert record['input_sha256']==hashlib.sha256(old.read_bytes()).hexdigest()
    assert record['output_sha256']==hashlib.sha256(current.read_bytes()).hexdigest()
    assert normalize_tokens(_body_text(old.read_text()))==normalize_tokens(_body_text(expected))
for filename,sha in selection['template_hashes'].items():
    assert hashlib.sha256((root/'data/gold/alignment/todo'/filename).read_bytes()).hexdigest()==sha
pack=Path('/mnt/c/Users/msrir/Downloads/gold_pack')
for rid,g in audit['gold'].items():
    filename=rid+'.TextGrid'
    assert (root/'data/gold/alignment'/filename).read_bytes()==(pack/'done'/filename).read_bytes()
    assert (root/'data/audio/hq'/f'{rid}.wav').read_bytes()==(pack/'audio'/f'{rid}.wav').read_bytes()
    tg=textgrid.openTextgrid(str(root/'data/gold/alignment'/filename),includeEmptyIntervals=True)
    assert len(tg.getTier('gold').entries)==41 and g['labelled']==20
assert sum(g['excluded_question'] for g in audit['gold'].values())==23
assert (root/'data/gold/alignment/ANNOTATION_NOTES.md').read_bytes()==(pack/'done/ANNOTATION_NOTES.md').read_bytes()
for name,e in audit['evidence'].items():
    rows=[d for d in audit['details'] if d['aligner']==name]
    assert len(rows)==e['words_scored']==37
    for edge in ('start','end'):
        values=np.array([abs(d[f'predicted_{edge}']-d[f'gold_{edge}'])*1000 for d in rows])
        assert round(float(np.median(values)),3)==e[edge]['median_ms']
        assert round(float(np.mean(values)),3)==e[edge]['mean_ms']
    for rid,pair in e['run_hashes'].items():
        actual=[]
        for repeat in (1,2):
            path=root/'data/review/bakeoff'/audit['input_identity']/name/str(repeat)/f'{rid}.json'
            payload=json.loads(path.read_text());Alignment.model_validate(payload)
            actual.append(hashlib.sha256(path.read_bytes()).hexdigest())
        assert pair==actual
    assert e['deterministic']==all(pair[0]==pair[1] for pair in e['run_hashes'].values())
def snapshot():
    directories=('data/alignment/windows','data/alignment/mfa','data/alignment/whisperx','data/transcripts/as_spoken')
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for directory in directories for p in (root/directory).iterdir() if p.is_file()}
before=snapshot();run_alignment('both');assert snapshot()==before
report_paths=[root/'data/review/alignment_bakeoff.json',root/'reports/day01_aligner_bakeoff.md']
before_reports=[p.read_bytes() for p in report_paths]
evaluate_alignment(root)
assert snapshot()==before and [p.read_bytes() for p in report_paths]==before_reports
print('PASS: supplied files/HQ audio/todo/raw preserved; 30 frozen cuts/windows and 60 current JSON/TextGrids; cached alignment and bake-off reruns byte-identical; 23 exclusions / 37 scored words; metrics and 12 actual run JSON hashes verified')
