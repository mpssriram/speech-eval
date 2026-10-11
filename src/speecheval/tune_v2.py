"""Bounded post-hoc DEV-only search; no test or human data is loaded by tuning."""
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path
import time

import yaml


def dev_rows(root: Path) -> list[dict]:
    """Filter manifest metadata before opening evidence; refuse participant/human paths."""
    rows=[];allowed=set(yaml.safe_load((root/'configs/splits.yaml').read_text())['dev'])
    for row in csv.DictReader((root/'data/manifest/dataset_index.csv').open()):
        if row['split']!='dev':continue
        if '__user__' in row['recording_id'] or any('human' in Path(row.get(k,'')).parts for k in ('audio_path','label_path')):
            raise ValueError('Never tune on human recordings')
        parts=row['recording_id'].split('__')
        if len(parts)!=3 or f'{parts[0]}__{parts[1]}__orig' not in allowed:
            raise ValueError('Manifest DEV speaker does not belong to the frozen DEV split')
        for key in ('audio_path','label_path'):
            relative=row.get(key,'')
            if relative and not (root/relative).resolve().is_relative_to(root.resolve()):raise ValueError('Dev evidence path escapes project')
            if relative and 'human' in (root/relative).resolve().relative_to(root.resolve()).parts:raise ValueError('Never tune on human recordings')
        if row['text_id'] in ('gettysburg','o_captain'):rows.append(row)
    if not rows:raise ValueError('No eligible DEV recordings')
    return rows


def promotion_allowed(baseline_f1: float,candidate_f1: float,clean_alarms: float) -> bool:
    """Predeclared practical margin, not a statistical significance claim."""
    return clean_alarms<=.5 and candidate_f1-baseline_f1>=.020-1e-12 and candidate_f1>=baseline_f1*1.10-1e-12


def first_stage(base: dict) -> list[dict]:
    """Eighteen predeclared threshold/contrast/effect configurations."""
    result=[]
    for k,within,profile in itertools.product((2.,3.5,5.),(.5,1.,1.5),('lenient','moderate')):
        cfg=copy.deepcopy(base);cfg['k']={kind:k for kind in cfg['k']}
        cfg['within_k']=within;cfg['effect_profile']=profile
        cfg['effects']=({'rate_fraction':.1,'pitch_fraction':.2,'loud_db':2.,'clarity_db':2.,'pause_excess_s':.25,'pause_deficit_s':.1}
                        if profile=='lenient' else {'rate_fraction':.2,'pitch_fraction':.35,'loud_db':4.,'clarity_db':4.,'pause_excess_s':.6,'pause_deficit_s':.25})
        cfg['region_min_duration_s']=.4;cfg['merge_gap_s']=.2;result.append(cfg)
    return result


def second_stage(best: dict,previous: list[dict]) -> list[dict]:
    """At most twelve morphology configurations around the dev-selected first-stage candidate."""
    result=[];seen={json.dumps(c,sort_keys=True) for c in previous}
    for duration,gap in itertools.product((.15,.4,.8,1.2),(.05,.2,.5)):
        cfg=copy.deepcopy(best);cfg['region_min_duration_s']=duration;cfg['merge_gap_s']=gap
        key=json.dumps(cfg,sort_keys=True)
        if key not in seen:result.append(cfg);seen.add(key)
    return result


def select_best(history: list[dict]) -> dict:
    """Global dev F1 under clean guard; otherwise best F1 with explicit failed guard."""
    feasible=[h for h in history if h['metrics']['overall']['false_alarms_per_minute']<=.5]
    return max(feasible or history,key=lambda h:(h['metrics']['overall']['f1'],
               -h['metrics']['overall']['false_alarms_per_minute'],-h['id']))


def guard_repair_config(best: dict,evaluated: list[dict]) -> dict:
    """One final adaptive dev candidate: raise pause excess to fit the remaining clean budget.

    Choose the smallest next 50-ms grid point removing enough *clean-dev* awkward
    alarms; never inspect synthetic truth or held-out observations to choose it.
    """
    clean=[item for item in evaluated if item['clean']]
    minutes=sum(item['duration_s'] for item in clean)/60.
    budget=math.floor(.5*minutes+1e-12)
    other=sum(p['type']!='awkward_pause' for item in clean for p in item['predicted'])
    excess=sorted(p['evidence']['participant']-p['evidence']['reference']
                  for item in clean for p in item['predicted'] if p['type']=='awkward_pause')
    allowed=max(0,budget-other);cfg=copy.deepcopy(best)
    if len(excess)>allowed:
        cutoff=excess[len(excess)-allowed-1]
        cfg['effects']['pause_excess_s']=max(cfg['effects']['pause_excess_s'],math.ceil((cutoff+1e-9)/.05)*.05)
    cfg['effect_profile']='guard-repair'
    return cfg


def v2_metrics(items: list[dict],settings: dict) -> tuple[dict,list[dict]]:
    """Same uncertainty filter/matcher/denominator as v1; only candidate regions differ."""
    from speecheval.detector_v2 import detect_v2
    from speecheval.calibration import exclude_uncertain_predictions
    from speecheval.evaluate import detection_metrics
    evaluated=[{**item,'predicted':exclude_uncertain_predictions(
        detect_v2(item['table'],item['duration_s'],settings,item['contrast']),item.get('excluded_truth',[]))} for item in items]
    return detection_metrics(evaluated),evaluated


def write_log(root: Path,audit: dict) -> None:
    """Write only the authorised Phase11 narrative; full precision stays in JSON."""
    path=root/'reports/phase11_v2.md';text=path.read_text().split('\n## V2 DEV configuration log')[0]
    lines=['','## V2 DEV configuration log','',
           '| ID | Reader k | Own k | Effects | Min s | Gap s | Precision | Recall | F1 | Clean/min | Guard |',
           '|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|']
    for entry in audit['history']:
        cfg=entry['config'];m=entry['metrics']['overall']
        lines.append(f"| {entry['id']} | {cfg['k']['rushing']:g} | {cfg['within_k']:g} | {cfg['effect_profile']} | {cfg['region_min_duration_s']:g} | {cfg['merge_gap_s']:g} | {m['precision']:.3f} | {m['recall']:.3f} | {m['f1']:.3f} | {m['false_alarms_per_minute']:.3f} | {m['false_alarms_per_minute']<=.5} |")
    path.write_text(text+'\n'.join(lines)+'\n',encoding='utf-8')


def tune(root: Path) -> dict:
    """One bounded DEV search, with an audit written after every measured configuration."""
    from speecheval.reproduce import comparison_items,file_sha
    from speecheval.calibration import evaluate_settings,calibration_identity
    from speecheval.detector_v2 import recording_contrast
    from speecheval.evaluate import bootstrap_detection
    started=time.monotonic();audit_path=root/'data/review/detector_v2_dev.json'
    if audit_path.exists():raise ValueError('DEV tuning already recorded; do not silently start a second search')
    rows=dev_rows(root)
    settings=yaml.safe_load((root/'configs/detector.yaml').read_text())
    base=copy.deepcopy(settings);base.update(version='post-hoc-v2',within_k=.5,within_min_sentences=3,
        within_scale_floor={'rate':.05,'pitchvar':.05,'loud':.5},region_min_duration_s=.4,merge_gap_s=.2)
    items=comparison_items(root,rows,'A-LOSO')
    for item in items:item['contrast']=recording_contrast(root,item['recording_id'],item['table'],base)
    baseline,baseline_items=evaluate_settings(items,settings)
    inputs=calibration_identity(root)
    # Sentence Parquet is an additional v2 dependency; v1's identity is untouched.
    for row in rows:
        relative=f"data/features/sentences/{row['recording_id']}.parquet";inputs['inputs'][relative]=file_sha(root/relative)
    audit={'schema':'detector-v2-dev/v1','split':'dev','setting':'A-LOSO','files':len(items),
           'recording_ids':[item['recording_id'] for item in items],
           'v1_metrics':baseline,'v1_confidence_intervals':bootstrap_detection(baseline_items),
           'inputs':inputs,'implementation':{name:file_sha(root/'src/speecheval'/name) for name in ('detector_v2.py','tune_v2.py')},
           'config_limit':30,'time_limit_seconds':14400,'history':[]}
    def save():audit_path.parent.mkdir(parents=True,exist_ok=True);audit_path.write_text(json.dumps(audit,sort_keys=True,indent=2,allow_nan=False)+'\n')
    def measure(cfg):
        if len(audit['history'])>=30 or time.monotonic()-started>=14400:raise TimeoutError('V2 configuration/time limit reached')
        metrics,_=v2_metrics(items,cfg)
        entry={'id':len(audit['history'])+1,'config':cfg,'metrics':metrics,
               'config_sha256':hashlib.sha256(json.dumps(cfg,sort_keys=True).encode()).hexdigest()}
        audit['history'].append(entry);save();write_log(root,audit)
        print(f"DEV config {entry['id']}: F1={metrics['overall']['f1']:.3f}, clean/min={metrics['overall']['false_alarms_per_minute']:.3f}",flush=True)
    candidates=first_stage(base)
    for cfg in candidates:measure(cfg)
    for cfg in second_stage(select_best(audit['history'])['config'],candidates):measure(cfg)
    best=select_best(audit['history']);audit['selected_id']=best['id'];audit['selected_config']=best['config']
    audit['selected_metrics']=best['metrics'];m=best['metrics']['overall']
    audit['promotion_allowed']=promotion_allowed(baseline['overall']['f1'],m['f1'],m['false_alarms_per_minute'])
    _,selected_items=v2_metrics(items,best['config'])
    audit['selected_confidence_intervals']=bootstrap_detection(selected_items)
    audit['elapsed_seconds']=time.monotonic()-started
    (root/'configs/detector_v2.yaml').write_text('# POST-HOC v2: selected on DEV only; v1 remains frozen.\n'+yaml.safe_dump(best['config'],sort_keys=False))
    audit['selected_yaml_sha256']=file_sha(root/'configs/detector_v2.yaml');save();write_log(root,audit)
    return audit


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--finish-guard-repair',action='store_true',help='Consume the sole remaining trial after a 29-config failed-guard search')
    args=parser.parse_args()
    audit=finish_guard_repair(Path.cwd()) if args.finish_guard_repair else tune(Path.cwd())
    print(json.dumps({'selected_id':audit['selected_id'],'promotion_allowed':audit['promotion_allowed'],
                      'v1':audit['v1_metrics']['overall'],'v2':audit['selected_metrics']['overall']},indent=2))


def finish_guard_repair(root: Path) -> dict:
    """Continue the recorded search once, without rerunning its 29 configurations."""
    from speecheval.reproduce import comparison_items,file_sha
    from speecheval.detector_v2 import recording_contrast
    from speecheval.evaluate import bootstrap_detection
    started=time.monotonic();path=root/'data/review/detector_v2_dev.json';audit=json.loads(path.read_text())
    if len(audit['history'])!=29 or audit['promotion_allowed'] or any(h['metrics']['overall']['false_alarms_per_minute']<=.5 for h in audit['history']):
        raise ValueError('Final guard repair requires precisely 29 trials and no feasible configuration')
    if audit['elapsed_seconds']>=14400:raise TimeoutError('DEV time limit reached')
    for relative,sha in audit['inputs']['inputs'].items():
        if file_sha(root/relative)!=sha:raise ValueError(f'DEV evidence changed: {relative}')
    if file_sha(root/'src/speecheval/detector_v2.py')!=audit['implementation']['detector_v2.py']:
        raise ValueError('Detector changed during bounded search')
    items=comparison_items(root,dev_rows(root),'A-LOSO')
    for item in items:item['contrast']=recording_contrast(root,item['recording_id'],item['table'],audit['selected_config'])
    _,existing=v2_metrics(items,audit['selected_config'])
    candidate=guard_repair_config(audit['selected_config'],existing)
    metrics,evaluated=v2_metrics(items,candidate)
    audit['history'].append({'id':30,'config':candidate,'metrics':metrics,
        'config_sha256':hashlib.sha256(json.dumps(candidate,sort_keys=True).encode()).hexdigest(),
        'selection_reason':'Adaptive final clean-DEV pause-excess guard repair; no new truth/test inspection'})
    best=select_best(audit['history']);audit['selected_id']=best['id'];audit['selected_config']=best['config']
    audit['selected_metrics']=best['metrics'];m=best['metrics']['overall']
    audit['promotion_allowed']=promotion_allowed(audit['v1_metrics']['overall']['f1'],m['f1'],m['false_alarms_per_minute'])
    audit['selected_confidence_intervals']=bootstrap_detection(evaluated) if best['id']==30 else audit['selected_confidence_intervals']
    audit['elapsed_seconds']+=time.monotonic()-started
    if audit['elapsed_seconds']>=14400:raise TimeoutError('DEV time limit reached')
    (root/'configs/detector_v2.yaml').write_text('# POST-HOC v2: selected on DEV only; v1 remains frozen.\n'+yaml.safe_dump(best['config'],sort_keys=False))
    audit['selected_yaml_sha256']=file_sha(root/'configs/detector_v2.yaml')
    audit['guard_repair_implementation_sha256']=file_sha(Path(__file__))
    path.write_text(json.dumps(audit,sort_keys=True,indent=2,allow_nan=False)+'\n');write_log(root,audit)
    return audit


if __name__=='__main__':main()
