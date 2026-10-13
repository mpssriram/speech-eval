"""DEV-only activation audit, with frozen v1 code/config and no benchmark evaluation."""
from __future__ import annotations
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import yaml
from speecheval.detect import TYPES, detect
from speecheval.mode_c import SUPPORTED, sentence_regions
from speecheval.pipeline import analyze

CASES = {
    'rushing': 'o_captain__lv_s__rushing_s5_01',
    'dragging': 'gettysburg__lv_pc__dragging_s5_01',
    'monotone': 'o_captain__lv_sjs__monotone_s5_01',
    'too_quiet': 'o_captain__lv_s__too_quiet_s4_01',
    'mumbling': 'gettysburg__lv_rk__mumbling_s5_01',
    'awkward_pause': 'o_captain__lv_s__awkward_pause_s5_01',
    'missing_pause': 'o_captain__lv_s__missing_pause_s5_01',
}


def hashes(root: Path) -> dict[str, str]:
    """Pin scientific code/configuration and previously frozen evaluation outputs."""
    paths = [p for p in (root/'src/speecheval').rglob('*.py') if p.name not in ('display.py','service.py')]
    paths += list((root/'configs').glob('*.yaml'))
    paths += list((root/'data/review').glob('*.json')) + [root/'data/human/evaluation.json']
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def activation_probes(settings: dict) -> dict:
    """Isolate rule directions on fabricated feature rows; never alter real measurements."""
    result = {}
    for kind in CASES:
        rows = [{'i': i, 'text': 'word', 'sentence': 0, 'start': i+.5, 'end': i+.8,
                 'ref_i': i, 'values': {}, 'reference': {}, 'z': {}} for i in range(4)]
        if kind in TYPES:
            feature, direction = TYPES[kind]
            for row in rows:
                row['z'][feature] = direction*10.
                row['values'][feature] = 1.
                row['reference'][feature] = 0.
        else:
            row = rows[1]
            row['z']['pause'] = 10. if kind=='awkward_pause' else -10.
            row['values']['pause'] = __import__('math').log(1. if kind=='awkward_pause' else .05)
            row['reference']['pause'] = __import__('math').log(.05 if kind=='awkward_pause' else 1.)
        fired = {r['type'] for r in detect(rows, 5., settings)}
        assert kind in fired, (kind, fired)
        result[kind] = {'A': True, 'B': True, 'C': None}
    norms = {'features': {key: {'median': 0., 'robust_sd': .1,
             'percentiles': {'25': -.1, '75': .1}} for key in ('rate','pitchrange','final_drop','end_pause')}}
    base = {'i':0,'start':0.,'end':4.,'word_start':0,'word_end':3,'n_words':4,
            'articulation_rate_syl_s':1.,'f0_st_range':.5,'final_int_drop_db':0.,'pause_after_s':.95}
    edits = {'rushing':('articulation_rate_syl_s',3.),'dragging':('articulation_rate_syl_s',.3),
             'monotone':('f0_st_range',0.),'too_quiet':('final_int_drop_db',-10.),
             'missing_pause':('pause_after_s',0.)}
    for kind, (column,value) in edits.items():
        sentence = {**base, column:value}
        fired = {r['type'] for r in sentence_regions([sentence,{**base,'i':1}],norms,settings)}
        assert kind in fired, (kind,fired)
        result[kind]['C'] = True
    return result


def main() -> None:
    root=Path.cwd(); before=hashes(root)
    rows={r['recording_id']:r for r in csv.DictReader((root/'data/manifest/dataset_index.csv').open())}
    settings=yaml.safe_load((root/'configs/detector.yaml').read_text())
    norms=json.loads((root/'data/reference/norms_v1.json').read_text())
    probes=activation_probes(settings); results=[]
    for kind,rid in CASES.items():
        row=rows[rid]; assert row['split']=='dev' and row['kind']=='synthetic'
        labels=json.loads((root/row['label_path']).read_text())['flaws']
        assert len(labels)==1 and labels[0]['type']==kind
        source_id=rid.rsplit('__',1)[0]+'__orig'
        assert rows[source_id]['split']=='dev'
        source=json.loads((root/f'data/alignment/{source_id}.json').read_text())
        for mode in ('A','B','C'):
            if mode=='C':
                from speecheval.mode_c import analyze_mode_c
                a=analyze_mode_c(root/row['audio_path'],row['text_id'],root=root,norms=norms)
            else:
                a=analyze(root/row['audio_path'],row['text_id'],mode,
                          exclude_speaker=rid.split('__')[1] if mode=='A' else None,
                          previous=root/source['audio'] if mode=='B' else None,root=root)
            gold=labels[0]; matches=[]
            for i,p in enumerate(a['regions']):
                overlap=max(0.,min(p['end'],gold['end'])-max(p['start'],gold['start']))
                union=max(p['end'],gold['end'])-min(p['start'],gold['start'])
                if p['type']==kind and union and overlap/union>=.3:matches.append(i)
            counts=Counter(p['type'] for p in a['regions'])
            result={'injected_type':kind,'severity':gold['severity'],'mode':mode,'recording_id':rid,
                    'analysis_id':a['analysis_id'],'supported':mode!='C' or kind in SUPPORTED,
                    'flags_by_type':dict(sorted(counts.items())),'target_type_fired':counts[kind]>0,
                    'strict_interval_hit_indices':matches,'reference':a['reference'],
                    'regions':a['regions']}
            results.append(result)
            print(f'{kind} {mode}: supported={result["supported"]}; flags={dict(counts)}; target fired={counts[kind]>0}',flush=True)
    assert before==hashes(root),'Frozen scientific inputs changed'
    out={'schema':'rule-coverage-diagnosis/v1','split':'DEV only','synthetic_files':7,'mode_runs':21,
         'threshold_AB':3.5,'threshold_C':settings['mode_c']['k'],'supported_C':sorted(SUPPORTED),
         'activation_probes':probes,'results':results,'detector_activation_bug_found':False,
         'post_hoc_bug_fix':None,'benchmark_test_evaluations':0,'frozen_hashes':before}
    (root/'reports/phase10_rule_coverage.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
