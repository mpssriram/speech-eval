"""Seeded development smoke checks; never tune or measure held-out test accuracy here."""
import csv
import json
from pathlib import Path
import numpy as np
from speecheval.pipeline import analyze
from speecheval.verify import _write_json


def main():
    root=Path.cwd();rows=list(csv.DictReader((root/'data/manifest/dataset_index.csv').open()))
    eligible=[r for r in rows if r['split']=='dev' and r['kind']=='synthetic' and r['text_id'] in ('gettysburg','o_captain')]
    if len(eligible)<20:raise ValueError('Full development dataset must exist first')
    sample=np.random.default_rng(20261001).choice(len(eligible),size=20,replace=False)
    results=[]
    for number,i in enumerate(sample):
        row=eligible[i];path=root/row['audio_path']
        result=analyze(path,row['text_id'],exclude_speaker=row['speaker_slug'],plot=number<3,root=root)
        output=root/'data/analyses'/f"{result['analysis_id']}.json";before=output.read_bytes()
        assert analyze(path,row['text_id'],exclude_speaker=row['speaker_slug'],root=root)==result
        assert output.read_bytes()==before
        true=json.loads((root/row['label_path']).read_text())['flaws']
        results.append({'recording_id':row['recording_id'],'analysis_id':result['analysis_id'],'true_labels':true,'regions':result['regions']})
    # A Mode B functional smoke is not a test-set accuracy estimate.
    candidates=[r for r in rows if r['kind']=='synthetic' and r['text_id']=='jfk_rice']
    if not candidates:raise ValueError('JFK variants missing')
    chosen=next((r for r in candidates if '__rushing_s3_' in r['recording_id']),candidates[0])
    baseline=root/'data/audio/hq/jfk_rice__jfk__orig.wav'
    rehearsal=analyze(root/chosen['audio_path'],'jfk_rice',mode='B',previous=baseline,root=root)
    output=root/'data/analyses'/f"{rehearsal['analysis_id']}.json";before=output.read_bytes()
    assert analyze(root/chosen['audio_path'],'jfk_rice',mode='B',previous=baseline,root=root)==rehearsal
    assert output.read_bytes()==before and rehearsal['progress'] is not None
    _write_json(root/'data/review/analysis_smoke.json',{'schema':'analysis_smoke/v1','seed':20261001,'passed':True,
                'development':results,'rehearsal_analysis_id':rehearsal['analysis_id'],'human_take':'PENDING',
                'accuracy_estimate':False})
    print('PASS: 20 development analyses, 3 plots, one Mode B comparison, byte-identical replay; human validation pending')


if __name__=='__main__':main()
