"""One-shot post-hoc sensitivity; read retained inputs and write Phase 13 artifacts only."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import time
import csv
import yaml
from speecheval.detect import detect, z_table
from speecheval.reference import recording_values, map_words
from speecheval.pause_floor import floor_z_table
from speecheval.calibration import exclude_uncertain_predictions
from speecheval.evaluate import FLAW_TYPES, detection_metrics, bootstrap_detection, match_regions

LABEL='post-hoc sensitivity check; test split previously seen with v1'
PROTOCOL='17a15e4f726dabd29d3ba1e7cc4df5de0783532a'


def sha(path: Path) -> str:
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def save(path: Path,value: dict) -> None:
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


def primary_hashes(root: Path) -> dict:
    """Freeze primary scientific outputs/config/code, excluding the website's independent edits."""
    paths=[]
    for folder,pattern in (('configs','*.yaml'),('src/speecheval','*.py'),('data/analyses','*.json'),
                           ('data/reference','*.json'),('data/review','*.json'),('reports','phase*.md')):
        paths.extend((root/folder).glob(pattern))
    paths.append(root/'data/human/evaluation.json')
    return {str(p.relative_to(root)):sha(p) for p in paths if p.name not in ('display.py','service.py')}


def pairs(predicted: list[dict],truth: list[dict],strict: bool=False) -> list[tuple[int,int]]:
    """Synthetic uses frozen pause-centre policy; genuine uses frozen strict IoU for every type."""
    if strict:
        retag=lambda rows:[{**r,'type':'interval:'+r['type']} for r in rows]
        return match_regions(retag(predicted),retag(truth),.3,.25)
    return match_regions(predicted,truth,.3,.25)


def summary(items: list[dict],strict: bool=False) -> dict:
    """Compute genuine counts without inventing severity; preserve clean/current-only denominators."""
    result={}; flags=Counter(); hits=Counter(); truth=Counter();clean_flags=Counter();clean_minutes=0.
    for item in items:
        flags.update(r['type'] for r in item['predicted']);truth.update(r['type'] for r in item['truth'])
        hits.update(item['truth'][t]['type'] for _,t in pairs(item['predicted'],item['truth'],strict))
        if item['clean']:
            clean_flags.update(r['type'] for r in item['predicted']);clean_minutes+=item['duration_s']/60
    for kind in (*FLAW_TYPES,'overall'):
        n_p=sum(flags.values()) if kind=='overall' else flags[kind]
        n_t=sum(truth.values()) if kind=='overall' else truth[kind]
        tp=sum(hits.values()) if kind=='overall' else hits[kind]
        cf=sum(clean_flags.values()) if kind=='overall' else clean_flags[kind]
        result[kind]={'predicted':n_p,'truth':n_t,'matched':tp,'hits':tp,'misses':n_t-tp,'false_positives':n_p-tp,
                      'precision':tp/n_p if n_p else (0. if n_t else None),'recall':tp/n_t if n_t else None,
                      'f1':2*tp/(n_p+n_t) if n_p+n_t else None,
                      'false_alarms_per_minute':cf/clean_minutes if clean_minutes else None}
    return {'files':len(items),'metrics':result,'flags_by_type':{k:flags[k] for k in FLAW_TYPES},
            'current_minutes':sum(i['duration_s'] for i in items)/60,'clean_minutes':clean_minutes,
            'false_positives_per_current_minute':result['overall']['false_positives']/(sum(i['duration_s'] for i in items)/60)}


def compare_file(rid: str,alignment: dict,values: list[dict],reference: dict,
                 truth: list[dict],excluded: list[dict],clean: bool,settings: dict,floor: dict,
                 strict: bool=False,stored: list[dict] | None=None) -> tuple[dict,dict,dict]:
    """Detect ON exactly once; prove OFF identity and no non-pause detection drift per file."""
    mapping=map_words([w['norm'] for w in alignment['words']],reference['words'])
    old_table=z_table(alignment,values,reference,mapping)
    off_table=floor_z_table(alignment,values,reference,mapping,{})
    assert json.dumps(old_table,sort_keys=True)==json.dumps(off_table,sort_keys=True),'OFF evidence differs'
    old=exclude_uncertain_predictions(detect(old_table,alignment['duration_s'],settings),excluded)
    new=exclude_uncertain_predictions(detect(floor_z_table(alignment,values,reference,mapping,floor),alignment['duration_s'],settings),excluded)
    nonpause=lambda regions:[r for r in regions if r['type'] not in ('awkward_pause','missing_pause')]
    assert nonpause(old)==nonpause(new),f'Non-pause regions changed: {rid}'
    if stored is not None:
        # Retained published regions add tags/explanation and rounded physical evidence.
        keys=('type','start','end','word_start','word_end','severity','mean_abs_z')
        assert [{k:p[k] for k in keys} for p in old]==[{k:p[k] for k in keys} for p in stored],rid
    base={'recording_id':rid,'duration_s':alignment['duration_s'],'truth':truth,'clean':clean}
    old_pairs=pairs(old,truth,strict);new_pairs=pairs(new,truth,strict)
    previous_hits={t for _,t in old_pairs};new_hits={t for _,t in new_pairs}
    changed={k for k in FLAW_TYPES if [p for p in old if p['type']==k]!=[p for p in new if p['type']==k]}
    audit={'recording_id':rid,'reference_version':reference['reference_version'],
           'v1_regions':old,'floor_regions':new,'truth':truth,'excluded_truth':excluded,
           'v1_pairs':old_pairs,'floor_pairs':new_pairs,'changed_types':sorted(changed),
           'new_hits':[{'label_index':t,'type':truth[t]['type']} for t in sorted(new_hits-previous_hits)],
           'lost_hits':[{'label_index':t,'type':truth[t]['type']} for t in sorted(previous_hits-new_hits)]}
    return {**base,'predicted':old},{**base,'predicted':new},audit


def synthetic(root: Path,split: str,setting: str,settings: dict,floor: dict,provenance: dict) -> tuple[list,list,list]:
    """Read the exact frozen cohorts/references; no build_reference or pipeline writes."""
    rows=list(csv.DictReader((root/'data/manifest/dataset_index.csv').open()))
    refs={};old_items=[];new_items=[];audits=[]
    for row in rows:
        if row['split']!=split:continue
        text=row['text_id'];speaker=row['speaker_slug']
        if setting=='A-LOSO':
            if text not in ('gettysburg','o_captain'):continue
            suffix=speaker
        else:
            if text not in ('jfk_rice','reagan_challenger'):continue
            suffix=f'{text}__{speaker}__orig'
        path=root/f'data/reference/{text}__excl-{suffix}.json'
        if path not in refs:
            refs[path]=json.loads(path.read_text());provenance[str(path.relative_to(root))]=sha(path)
            for relative,expected in refs[path]['inputs']['inputs'].items():
                assert sha(root/relative)==expected,relative
        alignment,values=recording_values(root,row['recording_id'])
        labels=json.loads((root/row['label_path']).read_text())['flaws'] if row['label_path'] else []
        uncertain=set(alignment.get('uncertain_words',[]))
        excluded=[f for f in labels if any(i in uncertain for i in range(f['word_start'],f['word_end']+1))]
        truth=[f for f in labels if f not in excluded]
        old,new,audit=compare_file(row['recording_id'],alignment,values,refs[path],truth,excluded,row['kind']=='source',settings,floor)
        old_items.append(old);new_items.append(new);audits.append(audit)
        for rel in [row['audio_path'],row.get('label_path',''),f"data/alignment/{row['recording_id']}.json",
                    *(f"data/features/{folder}/{row['recording_id']}.parquet" for folder in ('words','windows'))]:
            if rel:provenance[rel]=sha(root/rel)
        if len(audits)%25==0:print(f'{split} {setting}: {len(audits)} files',flush=True)
    assert old_items,f'No files: {split} {setting}'
    return old_items,new_items,audits


def human(root: Path,mode: str,settings: dict,floor: dict,provenance: dict) -> tuple[list,list,list]:
    """Re-evaluate retained genuine measurements with the same localized recorder labels."""
    from diagnose_human_near_misses import stored_values
    from speecheval.human_demo_evidence import row_breakdown
    refs={json.loads(p.read_text()).get('reference_version'):p for p in (root/'data/reference').glob('*.json')}
    old_items=[];new_items=[];audits=[]
    for row in json.loads((root/'data/human/evaluation.json').read_text())['results']:
        if row['detector']!='v1' or row['mode']!=mode or row['excluded_from_scoring']:continue
        jobpath=root/f"data/app/jobs/{row['job_id']}.json";job=json.loads(jobpath.read_text())
        path=refs[job['analysis']['reference']['reference_version']];reference=json.loads(path.read_text())
        provenance[str(jobpath.relative_to(root))]=sha(jobpath);provenance[str(path.relative_to(root))]=sha(path)
        for rel,expected in reference['inputs']['inputs'].items():assert sha(root/rel)==expected,rel
        alignment,values=stored_values(root,row['recording_id'],provenance)
        old,new,audit=compare_file(row['recording_id'],alignment,values,reference,row['intended_regions'],[],
                                 not row['intended_regions'],settings,floor,strict=True,stored=row['regions'])
        assert audit['v1_pairs']==[list(p) if isinstance(p,list) else p for p in row_breakdown(row)['matched_pairs']]
        audit.update(take_id=row['take_id'],mode=mode,job_id=row['job_id'])
        old_items.append(old);new_items.append(new);audits.append(audit)
        print(f'Genuine {mode}: {row["take_id"]}',flush=True)
    return old_items,new_items,audits


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=('dev','test','human'))
    parser.add_argument('--data-root',type=Path,required=True)
    args=parser.parse_args();root=args.data_root.resolve();project=Path(__file__).resolve().parents[1]
    out=project/'reports';floor=yaml.safe_load((project/'configs/pause_floor_sensitivity.yaml').read_text())
    assert floor=={'pause_sigma_floor_s':.052},'Only the predeclared floor is allowed'
    settings=yaml.safe_load((root/'configs/detector.yaml').read_text())
    assert all(v==3.5 for v in settings['k'].values())
    subprocess.run(['git','merge-base','--is-ancestor',PROTOCOL,'HEAD'],cwd=project,check=True)
    for predecessor in {'dev':[],'test':['dev'],'human':['dev','test']}[args.stage]:
        assert (out/f'phase13_{predecessor}.json').exists(),f'{predecessor} must finish first'
    dirty=subprocess.check_output(['git','status','--porcelain','--','src','configs','tests','scripts/run_pause_floor_sensitivity.py'],cwd=project,text=True)
    assert not dirty.strip(),'Commit the implementation before the one-shot run'
    before=primary_hashes(root);started=time.monotonic()
    marker=out/f'phase13_{args.stage}_started.json'
    with marker.open('x') as f:json.dump({'stage':args.stage,'disclaimer':LABEL,'protocol_commit':PROTOCOL,
         'implementation_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=project,text=True).strip(),
         'floor':floor,'primary_hashes':before},f,indent=2)
    result={'schema':'pause-floor-sensitivity/v1','stage':args.stage,'disclaimer':LABEL,
            'protocol_commit':PROTOCOL,'floor':floor,'evaluation_count':1,'settings':{},'provenance':{}}
    cohorts=('A-LOSO',) if args.stage=='dev' else ('A-LOSO','B-same-speaker') if args.stage=='test' else ('A','B')
    for cohort in cohorts:
        old,new,audits=human(root,cohort,settings,floor,result['provenance']) if args.stage=='human' else synthetic(root,args.stage,cohort,settings,floor,result['provenance'])
        strict=args.stage=='human';entry={'v1':summary(old,strict),'v1+floor':summary(new,strict),'files':audits,
              'excluded_uncertain_truth':sum(len(a['excluded_truth']) for a in audits)}
        if args.stage!='human':
            old_metrics=detection_metrics(old);new_metrics=detection_metrics(new)
            for version,metrics,items in (('v1',old_metrics,old),('v1+floor',new_metrics,new)):
                for kind in (*FLAW_TYPES,'overall'):
                    for key in ('predicted','truth','matched','precision','recall','f1','false_alarms_per_minute'):
                        assert entry[version]['metrics'][kind][key]==metrics[kind][key]
                entry[version]['frozen_matcher_metrics']=metrics
                if args.stage=='test':entry[version]['confidence_intervals']=bootstrap_detection(items)
            if args.stage=='test':
                frozen=json.loads((root/'data/review/final_evaluation.json').read_text())['settings'][cohort]
                assert entry['v1']['frozen_matcher_metrics']==frozen['metrics'],f'Frozen v1 metrics differ: {cohort}'
                assert entry['v1']['confidence_intervals']==frozen['confidence_intervals'],f'Frozen v1 CI differs: {cohort}'
                assert entry['v1']['files']==frozen['files']
                assert entry['excluded_uncertain_truth']==frozen['excluded_uncertain_truth']
        entry['changed_types']=sorted({k for a in audits for k in a['changed_types']})
        entry['new_hits']=[{'recording_id':a['recording_id'],**h} for a in audits for h in a['new_hits']]
        entry['lost_hits']=[{'recording_id':a['recording_id'],**h} for a in audits for h in a['lost_hits']]
        result['settings'][cohort]=entry
        save(out/f'phase13_{args.stage}.partial.json',result)
        print(cohort,json.dumps({v:entry[v]['metrics']['overall'] for v in ('v1','v1+floor')}),flush=True)
    assert primary_hashes(root)==before,'Primary artifacts changed'
    result['primary_hashes_verified']=len(before);result['elapsed_seconds']=time.monotonic()-started
    save(out/f'phase13_{args.stage}.json',result)
    print(f'Completed {args.stage} exactly once, {result["elapsed_seconds"]:.1f} s',flush=True)


if __name__=='__main__':main()
