"""Independent visual-gold validation and deterministic word-boundary evaluation."""
from __future__ import annotations

import csv
import importlib.metadata
import hashlib
import json
import logging
import math
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from num2words import num2words
from praatio import textgrid
from speecheval.align.base import Alignment, transcript_words
from speecheval.transcripts import _body_text
from speecheval.verify import _hash_bytes, _write_json

LOGGER=logging.getLogger(__name__)

FLAW_TYPES=('rushing','dragging','monotone','too_quiet','mumbling','awkward_pause','missing_pause')


def temporal_iou(a: dict,b: dict) -> float:
    """Intersection/union of second-based intervals; two zero-duration intervals have no IoU."""
    intersection=max(0.,min(a['end'],b['end'])-max(a['start'],b['start']))
    union=max(a['end'],b['end'])-min(a['start'],b['start'])
    return intersection/union if union>0 else 0.


def match_regions(predicted: list[dict], truth: list[dict], iou_min: float = .3, pause_tolerance_s: float = .25) -> list[tuple[int,int]]:
    """Greedy one-to-one highest IoU; pause eligibility uses centre distance."""
    candidates=[]
    for p,region in enumerate(predicted):
        for t,target in enumerate(truth):
            if region['type']!=target['type']:continue
            iou=temporal_iou(region,target)
            if region['type'] in ('awkward_pause','missing_pause'):
                distance=abs((region['start']+region['end']-target['start']-target['end'])/2)
                if distance<=pause_tolerance_s:candidates.append((-iou,p,t))
            elif iou>=iou_min:candidates.append((-iou,p,t))
    used_p=set();used_t=set();pairs=[]
    for _,p,t in sorted(candidates):
        if p not in used_p and t not in used_t:pairs.append((p,t));used_p.add(p);used_t.add(t)
    return pairs


def detection_metrics(items: list[dict], iou_min: float = .3, pause_tolerance_s: float = .25) -> dict:
    """File-aggregated counts, matched boundary errors in ms and clean false alarms/minute."""
    from scipy.stats import spearmanr
    buckets={kind:{'predicted':0,'truth':0,'matched':0,'pairs':[],'severities':{str(i):[0,0] for i in range(1,6)},'clean_predictions':0,'clean_minutes':0.} for kind in (*FLAW_TYPES,'overall')}
    confusion={true:{pred:0 for pred in FLAW_TYPES} for true in FLAW_TYPES}
    for item in items:
        predicted=item['predicted'];truth=item['truth'];pairs=match_regions(predicted,truth,iou_min,pause_tolerance_s)
        for kind,bucket in buckets.items():
            chosen_p=[p for p in predicted if kind=='overall' or p['type']==kind]
            chosen_t=[t for t in truth if kind=='overall' or t['type']==kind]
            chosen_pairs=[(predicted[p],truth[t]) for p,t in pairs if kind=='overall' or truth[t]['type']==kind]
            bucket['predicted']+=len(chosen_p);bucket['truth']+=len(chosen_t);bucket['matched']+=len(chosen_pairs);bucket['pairs'].extend(chosen_pairs)
            for t in chosen_t:bucket['severities'][str(t['severity'])][1]+=1
            for p,t in chosen_pairs:bucket['severities'][str(t['severity'])][0]+=1
            if item.get('clean',False):
                bucket['clean_predictions']+=len(chosen_p);bucket['clean_minutes']+=item['duration_s']/60
        for p in predicted:
            overlaps=[(temporal_iou(p,t),i,t) for i,t in enumerate(truth)]
            if not overlaps:continue
            iou,_,t=max(overlaps,key=lambda x:(x[0],-x[1]))
            if iou>=iou_min and t['type']!=p['type']:confusion[t['type']][p['type']]+=1
    result={}
    for kind,bucket in buckets.items():
        n_p,n_t,tp=bucket['predicted'],bucket['truth'],bucket['matched'];pairs=bucket['pairs']
        precision=tp/n_p if n_p else (0. if n_t else None);recall=tp/n_t if n_t else None
        f1=2*tp/(n_p+n_t) if n_p+n_t else None
        severity_rho=None
        if len(pairs)>=2 and len({p['severity'] for p,t in pairs})>1 and len({t['severity'] for p,t in pairs})>1:
            severity_rho=float(spearmanr([p['severity'] for p,t in pairs],[t['severity'] for p,t in pairs]).statistic)
        result[kind]={'predicted':n_p,'truth':n_t,'matched':tp,'precision':precision,'recall':recall,'f1':f1,
            'recall_by_severity':{i:tp_s/n_s if n_s else None for i,(tp_s,n_s) in bucket['severities'].items()},
            'onset_median_ms':float(np.median([abs(p['start']-t['start'])*1000 for p,t in pairs])) if pairs else None,
            'offset_median_ms':float(np.median([abs(p['end']-t['end'])*1000 for p,t in pairs])) if pairs else None,
            'mean_iou':float(np.mean([temporal_iou(p,t) for p,t in pairs])) if pairs else None,
            'false_alarms_per_minute':bucket['clean_predictions']/bucket['clean_minutes'] if bucket['clean_minutes'] else None,
            'severity_spearman':severity_rho}
    result['confusion']=confusion;return result


def bootstrap_detection(items: list[dict],resamples: int = 1000,seed: int = 20261001,
                        iou_min: float = .3,pause_tolerance_s: float = .25) -> dict:
    """Paired file-level bootstrap for F1 and recall; absent truths have no invented CI."""
    if not items:raise ValueError('Cannot bootstrap no files')
    counts={kind:[] for kind in (*FLAW_TYPES,'overall')}
    for item in items:
        metrics=detection_metrics([item],iou_min,pause_tolerance_s)
        for kind in counts:counts[kind].append([metrics[kind][k] for k in ('matched','predicted','truth')])
    rng=np.random.default_rng(seed);indices=rng.integers(0,len(items),(resamples,len(items)));result={}
    for kind,values in counts.items():
        totals=np.asarray(values)[indices].sum(axis=1);tp,n_p,n_t=totals.T
        with np.errstate(divide='ignore',invalid='ignore'):f1=2*tp/(n_p+n_t);recall=tp/n_t
        def ci(values):
            valid=values[np.isfinite(values)]
            return np.quantile(valid,[.025,.975]).tolist() if len(valid) else None
        result[kind]={'f1_95ci':ci(f1),'recall_95ci':ci(recall)}
    return result


def validate_dataset(root: Path, config: dict, recordings: list[dict]) -> dict[str,str]:
    """Reject stale or misfiled scored alignments and return hashes of actual artifacts."""
    identities={r['recording_id']:_hash_bytes(json.dumps(r,sort_keys=True).encode()) for r in recordings}
    hashes={}
    for name in ('mfa','whisperx'):
        directory=root/'data/alignment'/name
        provenance=json.loads((directory/'provenance.json').read_text())
        settings=config['alignment']['mfa'] if name=='mfa' else {'threads':1,'model':'WAV2VEC2_ASR_BASE_960H'}
        if provenance['input_hashes']!=identities or provenance['settings']!=settings:
            raise ValueError(f'Stale dataset alignment provenance: {name}; rerun alignment first')
        hashes[str((directory/'provenance.json').relative_to(root))]=_hash_bytes((directory/'provenance.json').read_bytes())
        for r in recordings:
            rid=r['recording_id'];path=directory/f'{rid}.json'
            payload=json.loads(path.read_text());Alignment.model_validate(payload)
            if payload['recording_id']!=rid or payload['aligner']['name']!=name:
                raise ValueError(f'Dataset alignment identity mismatch: {path}')
            if [w['text'] for w in payload['words']]!=[w[0] for w in transcript_words(r['body'])] or payload['uncertain_words']!=r['uncertain']:
                raise ValueError(f'Stale dataset transcript or word mask: {path}')
            hashes[str(path.relative_to(root))]=_hash_bytes(path.read_bytes())
    return hashes


def validate_migration(root: Path, selection: dict, migration: dict) -> dict[str,dict[int,list[int]]]:
    """Validate complete index remapping against frozen pre-number and current texts."""
    result={}
    for rid,plan in selection['recordings'].items():
        record=migration.get('recordings',{}).get(rid)
        if record is None:raise ValueError(f'Missing number migration record: {rid}')
        old_path=root/'data/review/before_number_expansion/transcripts'/f'{rid}.txt'
        current_path=root/'data/transcripts/as_spoken'/f'{rid}.txt'
        if _hash_bytes(old_path.read_bytes())!=record['input_sha256'] or _hash_bytes(current_path.read_bytes())!=record['output_sha256']:
            raise ValueError(f'Stale number migration provenance: {rid}')
        expected,mapping=expand_numbers(old_path.read_text())
        actual={int(k):v for k,v in record['old_to_new'].items()}
        if current_path.read_text()!=expected or actual!=mapping:
            raise ValueError(f'Incomplete or stale number mapping: {rid}')
        old_words=transcript_words(_body_text(old_path.read_text()))
        for item in plan['items']:
            index=item['word_index']
            if not 0<=index<len(old_words) or old_words[index][0]!=item['text']:
                raise ValueError(f'Original gold word identity mismatch: {rid}')
        result[rid]=actual
    return result


def inference_fingerprint(paths: dict[str,Path], versions: dict[str,str]) -> dict:
    """Fingerprint checkpoint/dictionary contents and the actual inference environment."""
    return {'model_sha256':{name:_hash_bytes(path.read_bytes()) for name,path in paths.items()},'versions':versions}


def installed_inference_fingerprint(root: Path, config: dict) -> dict:
    """Read installed models only; never install or modify the inference environment."""
    mfa=config['alignment']['mfa'];pretrained=Path('/home/sriram/Documents/MFA/pretrained_models')
    paths={'mfa_acoustic':pretrained/'acoustic'/f"{mfa['acoustic_model']}.zip",
           'mfa_dictionary':pretrained/'dictionary'/f"{mfa['dictionary']}.dict",
           'mfa_g2p':pretrained/'g2p'/f"{mfa['g2p_model']}.zip",
           'whisperx_checkpoint':root/'data/.cache/torch/wav2vec2_fairseq_base_ls960_asr_ls960.pth'}
    if mfa.get('custom_dictionary'):paths['custom_dictionary']=root/mfa['custom_dictionary']
    versions={name:importlib.metadata.version(name) for name in ('torch','torchaudio','whisperx','numpy','scipy','praatio','cmudict')}
    # Kalpy is conda-native here and has no Python distribution metadata.
    command=['/home/sriram/miniforge3/bin/conda','list','-n','aligner','--json']
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    conda_records=json.loads(subprocess.check_output(command,env=env,cwd=root,text=True))
    versions['mfa_environment']=json.dumps(sorted((r['name'],r['version'],r['build_string']) for r in conda_records))
    return inference_fingerprint(paths,versions)


def expand_numbers(text: str) -> tuple[str,dict[int,list[int]]]:
    """Spell numbers in the body only and map old whitespace-word indices to new ones."""
    def expand(line: str) -> str:
        return re.sub(r'\d+(?:,\d{3})*',lambda m:str(num2words(int(m.group().replace(',','')))),line)
    expanded=''.join(line if line.lstrip().startswith('#') else expand(line) for line in text.splitlines(keepends=True))
    mapping={};cursor=0
    for index,(word,_,_) in enumerate(transcript_words(_body_text(text))):
        length=len(transcript_words(expand(word)))
        mapping[index]=list(range(cursor,cursor+length));cursor+=length
    return expanded,mapping


def validate_gold_intervals(intervals: list, boxes: list[dict], duration_s: float) -> dict[str,Any]:
    """Validate labelled words, including blank gap intervals; preserve independent edges."""
    labelled=[];previous_end=0.
    for start,end,label in intervals:
        if not all(math.isfinite(v) for v in (start,end)) or not 0<=start<end<=duration_s+1e-6:
            raise ValueError('Gold interval bounds outside recording')
        if start<previous_end-1e-6:raise ValueError('Gold intervals overlap')
        previous_end=end
        if label.strip():labelled.append((start,end,label.strip()))
    if len(labelled)!=len(boxes):raise ValueError('Gold labelled interval count differs from templates')
    scored=[];outside=0;excluded=0;all_words=[]
    for (start,end,label),box in zip(labelled,boxes):
        unclear=label.endswith('?');clean=label[:-1] if unclear else label
        if clean!=box['text']:raise ValueError(f'Gold label mismatch: {clean!r} != {box["text"]!r}')
        is_outside=start<box['start']-1e-6 or end>box['end']+1e-6
        outside+=is_outside;excluded+=unclear
        item={'word_index':box['word_index'],'text':clean,'start':start,'end':end,
              'unclear':unclear,'outside_template':bool(is_outside)}
        all_words.append(item)
        if not unclear:scored.append(item)
    return {'total_intervals':len(intervals),'labelled':len(labelled),'excluded_question':excluded,
            'outside_template':outside,'scored':scored,'all_words':all_words}


def mapped_boundary(words: list[dict], indices: list[int]) -> tuple[float,float]:
    """Cover every word of a spelled-out number rather than scoring its first component."""
    return min(words[i]['start'] for i in indices),max(words[i]['end'] for i in indices)


def error_metrics(errors_s: list[float]) -> dict[str,float]:
    """Absolute boundary errors in milliseconds; thresholds are inclusive."""
    if not errors_s:raise ValueError('No eligible gold boundaries')
    values=np.abs(np.asarray(errors_s,dtype=float))*1000
    return {'median_ms':round(float(np.median(values)),3),'mean_ms':round(float(values.mean()),3),
            'within_20_ms_pct':round(float(np.mean(values<=20+1e-8)*100),3),
            'within_50_ms_pct':round(float(np.mean(values<=50+1e-8)*100),3)}


def recommend_aligner(evidence: dict[str,dict]) -> str:
    """Lower pooled median wins; within 10 ms prefer a deterministic CPU aligner."""
    ordered=sorted(evidence,key=lambda name:(evidence[name]['overall']['median_ms'],name))
    if abs(evidence['mfa']['overall']['median_ms']-evidence['whisperx']['overall']['median_ms'])<10:
        eligible=[name for name in ('mfa','whisperx') if evidence[name]['deterministic'] and evidence[name]['device']=='cpu']
        if eligible:return eligible[0]
    return ordered[0]


def load_recordings(root: Path, ids: list[str]) -> list[dict]:
    """Read current transcripts, masks and frozen prepared-clip sentence windows."""
    rows={r['recording_id']:r for r in csv.DictReader((root/'data/manifest/recordings.csv').open())}
    result=[]
    for rid in ids:
        path=root/'data/transcripts/as_spoken'/f'{rid}.txt'
        mask=json.loads((root/'data/transcripts/uncertain'/f'{rid}.json').read_text())
        if mask['transcript_sha256']!=_hash_bytes(path.read_bytes()):raise ValueError(f'Stale uncertainty mask: {rid}')
        windows=json.loads((root/'data/alignment/windows'/f'{rid}.json').read_text())
        if windows['transcript_sha256']!=mask['transcript_sha256']:raise ValueError(f'Stale windows: {rid}')
        result.append({'recording_id':rid,'body':_body_text(path.read_text()),'duration_s':float(rows[rid]['duration_s']),
            'windows':windows['sentences'],'uncertain':mask['uncertain_words'],
            'transcript_sha256':mask['transcript_sha256'],
            'audio_sha256':_hash_bytes((root/'data/audio/align16k'/f'{rid}.wav').read_bytes())})
    return result


def worker(root: Path, name: str, output: Path, ids: list[str]) -> None:
    """Actually rerun an installed aligner, never reuse its prior outputs."""
    recordings=load_recordings(root,ids);config=yaml.safe_load((root/'configs/default.yaml').read_text())
    started=time.monotonic()
    if name=='mfa':
        from speecheval.align.mfa import run_mfa
        results=run_mfa(root,recordings,config['alignment']['mfa'],isolated=True)
    else:
        from speecheval.align.whisperx_align import align_recording
        results={r['recording_id']:align_recording(root,r['recording_id'],r['body'],r['windows'],r['duration_s'],r['uncertain']) for r in recordings}
    output.mkdir(parents=True,exist_ok=True)
    for rid,payload in results.items():_write_json(output/f'{rid}.json',payload)
    _write_json(output/'run.json',{'aligner':name,'device':'cpu','recordings':len(results),'runtime_s':round(time.monotonic()-started,3)})


def evaluate_alignment(root: Path | None = None, force: bool = False) -> None:
    """Validate visual annotation, run both aligners twice, and report errors in ms."""
    root=root or Path.cwd()
    selection=json.loads((root/'data/gold/alignment/todo/selection.json').read_text())
    migration_path=root/'data/review/number_expansion.json'
    if not migration_path.exists():raise ValueError('Missing numeric migration audit; refuse ambiguous gold word indices')
    migration=json.loads(migration_path.read_text())
    mappings=validate_migration(root,selection,migration)
    gold={};ids=list(selection['recordings'])
    for rid,plan in selection['recordings'].items():
        tg=textgrid.openTextgrid(str(root/'data/gold/alignment'/f'{rid}.TextGrid'),includeEmptyIntervals=True)
        if tg.tierNames!=('gold',):raise ValueError('Expected a single gold interval tier')
        gold[rid]=validate_gold_intervals(list(tg.getTier('gold').entries),plan['items'],plan['duration_s'])
        for item in gold[rid]['all_words']:
            item['current_indices']=mappings[rid][item['word_index']]
    recordings=load_recordings(root,ids)
    config=yaml.safe_load((root/'configs/default.yaml').read_text())
    from speecheval.align.mfa import ensure_adoption
    ensure_adoption(root,config['alignment']['mfa'])
    all_ids=[r['recording_id'] for r in csv.DictReader((root/'data/manifest/recordings.csv').open())]
    scored_artifact_hashes=validate_dataset(root,config,load_recordings(root,all_ids))
    inputs={'recordings':recordings,'settings':config['alignment'],
            'scored_artifact_hashes':scored_artifact_hashes,'inference_environment':installed_inference_fingerprint(root,config),
            'gold_hashes':{rid:_hash_bytes((root/'data/gold/alignment'/f'{rid}.TextGrid').read_bytes()) for rid in ids},
            'selection_sha256':_hash_bytes((root/'data/gold/alignment/todo/selection.json').read_bytes()),
            'migration_sha256':_hash_bytes(migration_path.read_bytes()) if migration_path.exists() else None,
            'implementation_sha256':{str(p.relative_to(root)):_hash_bytes(p.read_bytes()) for p in
                [root/'src/speecheval/evaluate.py',root/'src/speecheval/alignment_analysis.py',root/'src/speecheval/align/mfa.py',root/'src/speecheval/align/whisperx_align.py',root/'src/speecheval/align/base.py',root/'src/speecheval/transcripts.py']}}
    identity=_hash_bytes(json.dumps(inputs,sort_keys=True).encode())
    cache=root/'data/review/bakeoff'/identity
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    env.update(PYTHONHASHSEED='0',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1')
    evidence={};details=[]
    for name in ('mfa','whisperx'):
        pairs={};runtimes=[]
        for repeat in (1,2):
            directory=cache/name/str(repeat);metadata=directory/'run.json'
            if force or not metadata.exists():
                LOGGER.info('Independent %s run %d/2 on three gold recordings',name,repeat)
                subprocess.run([sys.executable,'-m','speecheval.evaluate','worker',str(root),name,str(directory),*ids],env=env,check=True,cwd=root)
            runtimes.append(json.loads(metadata.read_text())['runtime_s'])
            for rid in ids:
                path=directory/f'{rid}.json'
                payload=json.loads(path.read_text());Alignment.model_validate(payload)
                if payload['recording_id']!=rid or payload['aligner']['name']!=name:raise ValueError('Rerun identity mismatch')
                pairs.setdefault(rid,[]).append(_hash_bytes(path.read_bytes()))
        starts=[];ends=[]
        for rid in ids:
            payload=json.loads((root/'data/alignment'/name/f'{rid}.json').read_text());Alignment.model_validate(payload)
            excluded=set(payload.get('uncertain_words',[]));omitted_uncertain=0
            for item in gold[rid]['scored']:
                if excluded.intersection(item['current_indices']):omitted_uncertain+=1;continue
                start,end=mapped_boundary(payload['words'],item['current_indices'])
                starts.append(abs(start-item['start']));ends.append(abs(end-item['end']))
                details.append({'aligner':name,'recording_id':rid,'original_word_index':item['word_index'],
                    'current_indices':item['current_indices'],'word':item['text'],'gold_start':item['start'],'gold_end':item['end'],
                    'predicted_start':start,'predicted_end':end,'start_error_ms':round(abs(start-item['start'])*1000,3),
                    'end_error_ms':round(abs(end-item['end'])*1000,3)})
            gold[rid]['excluded_transcript_uncertain']=omitted_uncertain
        total_interpolated=total_oov=0
        for row in csv.DictReader((root/'data/manifest/recordings.csv').open()):
            payload=json.loads((root/'data/alignment'/name/f"{row['recording_id']}.json").read_text())
            total_interpolated+=len({w['word'] for w in payload['warnings'] if w['type']=='interpolated'})
            oov={w['text'] for w in payload['warnings'] if w['type']=='oov'}
            total_oov+=sum(any(token in oov for token in w['norm'].split()) for w in payload['words'])
        evidence[name]={'start':error_metrics(starts),'end':error_metrics(ends),'overall':error_metrics(starts+ends),
            'words_scored':len(starts),'interpolated_words':total_interpolated,'oov_words':total_oov,'device':'cpu',
            'deterministic':all(hashes[0]==hashes[1] for hashes in pairs.values()),'run_hashes':pairs,'gold_run_runtime_s':runtimes,
            'dataset_run':json.loads((root/'data/alignment'/name/'provenance.json').read_text())}
    recommendation=recommend_aligner(evidence)
    audit={'schema':'alignment_bakeoff/v1','input_identity':identity,'inputs':inputs,'gold':gold,'evidence':evidence,
           'recommendation':recommendation,'details':details,'annotation_method':'Claude visual, not listened; human spot-check PENDING'}
    from speecheval.alignment_analysis import annotate_audit
    analysis_settings=config['alignment']['bakeoff']
    annotate_audit(root,audit,analysis_settings['bootstrap_seed'],analysis_settings['bootstrap_resamples'])
    _write_json(root/'data/review/alignment_bakeoff.json',audit)
    write_bakeoff_report(root,audit)
    LOGGER.info('Bake-off complete: recommended %s; STOP after report',recommendation)


def write_bakeoff_report(root: Path, audit: dict) -> None:
    """Write the evidence and annotation limitations without claiming human-listened gold."""
    lines=['# Day 1 aligner bake-off','',
        'Annotator: **Claude**, visually from waveform/spectrogram/intensity/pitch, **without listening**. Human spot-check: **PENDING**. This is not fully human-listened gold. The notes suggest seven spot-check words but contain no human boundary measurements or measured annotation-error estimate. Independence from MFA/WhisperX is asserted by the annotator, not independently established by this evaluation.',
        '', '## Validation and exclusions','',
        '| Recording | Total intervals | Labelled words | Excluded ? | Excluded transcript uncertainty | Scored | Outside old template |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for rid,g in audit['gold'].items():
        lines.append(f"| {rid} | {g['total_intervals']} | {g['labelled']} | {g['excluded_question']} | {g['excluded_transcript_uncertain']} | {len(g['scored'])-g['excluded_transcript_uncertain']} | {g['outside_template']} |")
    lines.extend(['','All labelled intervals match the frozen template labels after removing only a trailing ?. Blank gaps do not count as annotated words. Bounds are finite, ordered, non-overlapping and inside the same prepared audio. Seventeen supplied boundaries extend outside old model-derived boxes; they are flagged and retained, never clipped or changed. The 41-interval grids are copied unchanged.',
        '', '## Error table — 37 scored words, 74 pooled edges','', '| Aligner | Start median ms | Start mean ms | End median ms | End mean ms | Pooled median ms | ≤20 ms % (74 edges) | ≤50 ms % (74 edges) | Interpolated gold words /37 | OOV gold words /37 | Deterministic 3/3 | Hardware |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|'])
    for name,e in audit['evidence'].items():
        s,t,o=e['start'],e['end'],e['overall']
        lines.append(f"| {name} | {s['median_ms']} | {s['mean_ms']} | {t['median_ms']} | {t['mean_ms']} | {o['median_ms']} | {o['within_20_ms_pct']} | {o['within_50_ms_pct']} | {e['gold_interpolated_words']} | {e['gold_oov_words']} | {e['deterministic']} | CPU |")
    lines.extend(['','Threshold percentages above pool start/end boundaries. OOV counts count actual word occurrences, not unique dictionary entries.',
        '', '| Aligner | Starts within 20 ms % | Starts within 50 ms % | Ends within 20 ms % | Ends within 50 ms % |',
        '|---|---:|---:|---:|---:|'])
    for name,e in audit['evidence'].items():
        s,t=e['start'],e['end']
        lines.append(f"| {name} | {s['within_20_ms_pct']} | {s['within_50_ms_pct']} | {t['within_20_ms_pct']} | {t['within_50_ms_pct']} |")
    lines.extend(['', 'Measured hardware: Intel Core Ultra 9 275HX, 24 logical CPUs visible in WSL Ubuntu 24.04. Both aligners use CPU with one inference thread/job; the RTX 5080 GPU is not used for this comparison.',
        '', '## Runtime and independent determinism','', '| Aligner | Recorded dataset alignment runtime s | Gold rerun 1 s | Gold rerun 2 s |', '|---|---:|---:|---:|'])
    for name,e in audit['evidence'].items():
        lines.append(f"| {name} | {e['dataset_run']['runtime_s']} | {e['gold_run_runtime_s'][0]} | {e['gold_run_runtime_s'][1]} |")
    lines.extend(['', 'Two independent fresh Python processes actually rerun each installed aligner on the three annotated recordings, with fixed CPU settings. Runtime is measured separately from deterministic JSON; exact per-recording SHA256 pairs are below.', '', '| Aligner | Recording | Run 1 SHA256 | Run 2 SHA256 |', '|---|---|---|---|'])
    for name,e in audit['evidence'].items():
        for rid,pair in e['run_hashes'].items():lines.append(f'| {name} | {rid} | {pair[0]} | {pair[1]} |')
    lines.extend(['', '## Recommendation and risks','', f"Recommended: **{audit['recommendation']}** under the specified pooled median rule; when medians differ by less than 10 ms, deterministic CPU aligners win the tie, with MFA preferred if both qualify. This report does not set alignment.primary or promote files."])
    lines.append('')
    for name,e in audit['evidence'].items():
        if e['overall']['within_50_ms_pct']<90:lines.append(f"- RISK: {name} has {e['overall']['within_50_ms_pct']}% within 50 ms, below 90%.")
    lines.extend(['', '## Limits and reproducibility','',
        'Only 37 of 60 visually annotated words are potentially scorable after 23 question-mark exclusions; this is a small selected sample, especially Reagan (7 words). Unclear-word exclusion creates selection bias. Human spot-check extent/error is not quantified, no inter-annotator study was done, and visual annotation without listening may miss acoustic ambiguity. Results compare models against this supplied reference, not an established human error-free ground truth.',
        '', 'Numeric transcript rendering was changed for alignment. Original bodies, hashes, old-to-new word spans and number edits are preserved in data/review/number_expansion.json and before_number_expansion/. Frozen templates and gold labels were NOT rewritten. Numeric gold labels map to the complete expanded word span, not just its first token. ASR, audio, raw recordings and frozen cuts are unchanged; affected diffs/windows/alignments were regenerated.',
        '', 'Reproduce inside WSL: `env -u PYTHONPATH ~/.local/bin/uv run speecheval evaluate alignment`. Cached evidence is tied to current audio/transcript/window/config/gold/code hashes. `--force` reruns all four real inference passes. Full scoring rows and per-edge metrics: data/review/alignment_bakeoff.json.', ''])
    from speecheval.alignment_analysis import report_lines
    lines.extend(report_lines(audit))
    (root/'reports/day01_aligner_bakeoff.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),sys.argv[3],Path(sys.argv[4]),sys.argv[5:])
