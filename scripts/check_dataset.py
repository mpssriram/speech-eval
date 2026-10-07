"""Check full synthetic corpus integrity and optionally replay 20 seeded bundles."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import soundfile as sf
import yaml

from speecheval.align.base import Alignment
from speecheval.dataset import generate_mixed
from speecheval.inject import Label, generate_one, map_time


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fresh',action='store_true')
    args=parser.parse_args()
    root=Path.cwd()
    build=json.loads((root/'data/manifest/dataset_build.json').read_text())
    assert not build['partial_sources'] and build['real_alignment_completed'] and build['features_completed']
    assert build['synthetic_files']==build['expected_before_skips']-len(build['skipped'])
    splits=yaml.safe_load((root/'configs/splits.yaml').read_text())
    membership={rid:s for s in ('train','dev','test') for rid in splits[s]}
    rows=list(csv.DictReader((root/'data/manifest/dataset_index.csv').open()))
    assert len({r['recording_id'] for r in rows})==len(rows)
    speakers={}
    for row in rows:
        if row['split']!='excluded':speakers.setdefault(row['speaker_slug'],set()).add(row['split'])
    assert all(len(s)==1 for s in speakers.values())
    generated=[r for r in rows if r['kind']=='synthetic']
    assert len(generated)==build['synthetic_files']
    for row in rows:
        assert hashlib.sha256((root/row['audio_path']).read_bytes()).hexdigest()==row['sha256']
    for row in generated:
        rid=row['recording_id']
        label=json.loads((root/row['label_path']).read_text());Label.model_validate(label)
        source=json.loads((root/'data/alignment'/f"{label['reference_id']}.json").read_text())
        real=json.loads((root/'data/alignment'/f'{rid}.json').read_text());Alignment.model_validate(real)
        oracle=json.loads((root/'data/alignment/oracle'/f'{rid}.json').read_text());Alignment.model_validate(oracle)
        assert row['split']==membership[label['reference_id']]
        assert [w['norm'] for w in real['words']]==[w['norm'] for w in source['words']]
        assert real.get('uncertain_words',[])==source.get('uncertain_words',[])
        mapping=json.loads((root/'data/flawed/timemaps'/f'{rid}.json').read_text())['breakpoints']
        assert np.all(np.diff(np.asarray(mapping),axis=0)>=-1e-9)
        slopes=[(b[1]-a[1])/(b[0]-a[0]) for a,b in zip(mapping,mapping[1:]) if b[0]>a[0]]
        tolerance=.001+.0005*max(slopes)+1e-8
        for before,after in zip(source['words'],oracle['words']):
            assert abs(map_time(before['start'],mapping)-after['start'])<=tolerance
            assert abs(map_time(before['end'],mapping,side='left')-after['end'])<=tolerance
        for folder,rate in [('hq',44100),('align16k',16000)]:
            wave,sr=sf.read(root/'data/flawed'/folder/f'{rid}.flac')
            assert sr==rate and wave.ndim==1 and np.max(np.abs(wave))<1
            assert abs(len(wave)/sr-real['duration_s'])<=.0011
        for folder in ('frames','words','windows','sentences'):
            table=pd.read_parquet(root/'data/features'/folder/f'{rid}.parquet')
            assert len(table)>0
            if folder=='words':
                assert len(table)==len(real['words'])
                for i in real.get('uncertain_words',[]):assert np.isnan(table.iloc[i]['f0_st_median'])
        assert (root/'data/features/speaker_stats'/f'{rid}.json').exists()
    for shard in (root/'data/manifest/dataset_shards').glob('*.json'):
        result=json.loads(shard.read_text())
        for state in ('alignment_state','feature_state'):
            for path,expected in result[state]['artifacts'].items():
                assert hashlib.sha256((root/path).read_bytes()).hexdigest()==expected
    replayed=[]
    if args.fresh:
        cfg=yaml.safe_load((root/'configs/flaws.yaml').read_text())
        sample=np.random.default_rng(20261001).choice(len(generated),size=min(20,len(generated)),replace=False)
        for i in sample:
            row=generated[i];rid=row['recording_id']
            prior=json.loads((root/'data/flawed/provenance'/f'{rid}.json').read_text())
            label=json.loads((root/row['label_path']).read_text())
            reference=label['reference_id'];alignment=json.loads((root/'data/alignment'/f'{reference}.json').read_text())
            audio=root/'data/audio/hq'/f'{reference}.wav'
            stats=json.loads((root/'data/features/speaker_stats'/f'{reference}.json').read_text())
            if '__mixed_' in rid:
                record=generate_mixed(root,audio,alignment,stats,cfg,int(rid.rsplit('_',1)[1]),force=True)
            else:
                flaw=label['flaws'][0]
                record=generate_one(root,audio,alignment,stats,cfg,flaw['type'],flaw['severity'],1,
                                    force=True,shape='trail' if flaw['type']=='too_quiet' and flaw['severity']%2==0 else 'flat')
            assert record['artifacts']==prior['artifacts']
            replayed.append(rid)
    evidence={'schema':'dataset_integrity/v1','passed':True,'sources':len(build['sources']),
              'synthetic_files':len(generated),'index_rows':len(rows),'skipped':len(build['skipped']),
              'fresh_replayed':replayed,'human_acceptance':'PENDING'}
    from speecheval.verify import _write_json
    _write_json(root/'data/review/dataset_integrity.json',evidence)
    print(f"PASS: {len(generated)} synthetic files, hashes, real/oracle maps, features, speaker separation; fresh replay {len(replayed)}")


if __name__=='__main__':main()
