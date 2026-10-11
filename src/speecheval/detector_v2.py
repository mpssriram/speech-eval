"""Post-hoc v2 rules, separate from the byte-frozen v1 detector and pipeline."""
from __future__ import annotations

from decimal import Decimal
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from speecheval.detect import TYPES,make_region,resolve_conflicts,z_table
from speecheval.reference import inverse


def sentence_contrast(sentences: list[dict],rows: list[dict],settings: dict) -> dict[int,dict[str,float]]:
    """Own-sentence robust z: log articulation rate/range, median local loudness in dB.

    Uncertain sentence aggregates are excluded. Fewer than the configured valid
    sentences gives unavailable contrast, not zero/infinite evidence.
    """
    values={}
    for sentence in sentences:
        i=int(sentence['i']);valid=not sentence.get('invalid_evidence',False) and not sentence.get('uncertain',False) and sentence['n_words']>=4
        local=[r['values'].get('loud',np.nan) for r in rows if r['sentence']==i]
        finite=[v for v in local if np.isfinite(v)]
        rate=sentence.get('articulation_rate_syl_s',np.nan);pitch=sentence.get('f0_st_range',np.nan)
        values[i]={
            'rate':float(np.log(rate)) if valid and np.isfinite(rate) and rate>0 else np.nan,
            'pitchvar':float(np.log(pitch+.5)) if valid and np.isfinite(pitch) and pitch>=0 else np.nan,
            'loud':float(np.median(finite)) if valid and finite else np.nan,
        }
    result={i:{} for i in values}
    for feature in ('rate','pitchvar','loud'):
        x=np.asarray([v[feature] for v in values.values()]);x=x[np.isfinite(x)]
        median=float(np.median(x)) if len(x) else np.nan
        scale=max(settings['within_scale_floor'][feature],float(1.4826*np.median(np.abs(x-median)))) if len(x) else np.nan
        for i in result:
            result[i][feature]=(values[i][feature]-median)/scale if len(x)>=settings['within_min_sentences'] else np.nan
    return result


def practical_effect(kind: str,feature: str,row: dict,settings: dict) -> tuple[bool,float]:
    """Directional minimum effect: fractions for rate/range, dB for level/clarity, seconds for pauses."""
    p=inverse(feature,row['values'][feature]);r=inverse(feature,row['reference'][feature]);effects=settings['effects']
    if kind=='rushing':effect=p/r-1.;threshold=effects['rate_fraction']
    elif kind=='dragging':effect=1.-p/r;threshold=effects['rate_fraction']
    elif kind=='monotone':effect=1.-p/r if r>0 else -np.inf;threshold=effects['pitch_fraction']
    elif kind=='too_quiet':effect=r-p;threshold=effects['loud_db']
    elif kind=='mumbling':effect=r-p;threshold=effects['clarity_db']
    elif kind=='awkward_pause':effect=p-r;threshold=effects['pause_excess_s']
    else:effect=r-p;threshold=effects['pause_deficit_s']
    return bool(np.isfinite(effect) and effect>=threshold),float(effect)


def detect_v2(rows: list[dict],duration_s: float,settings: dict,contrast: dict[int,dict]) -> list[dict]:
    """AND reference/own sentence contrast for rate, pitch and loudness; practical effects for all types."""
    regions=[]
    for kind,(feature,direction) in TYPES.items():
        runs=[];current=[]
        for row in rows:
            valid=row.get('ref_i') is not None and np.isfinite(row['z'].get(feature,np.nan))
            own=contrast.get(row['sentence'],{}).get(feature,np.nan)
            if feature in ('rate','pitchvar','loud'):
                valid=valid and np.isfinite(own) and direction*own>=settings['within_k']
            if not valid:
                if current:runs.append(current);current=[]
                continue
            effect_ok,_=practical_effect(kind,feature,row,settings)
            if direction*row['z'][feature]<settings['k'][kind] or not effect_ok:continue
            if current and (row['sentence']!=current[-1]['sentence'] or
                            row['i']-current[-1]['i']-1>settings['region_max_gap_words'] or
                            row['start']-current[-1]['end']>settings['merge_gap_s']):
                runs.append(current);current=[]
            current.append(row)
        if current:runs.append(current)
        for run in runs:
            if len(run)<settings['region_min_words'] or run[-1]['end']-run[0]['start']<settings['region_min_duration_s']:continue
            region=make_region(kind,feature,run,run[0]['start'],run[-1]['end'],settings)
            region['v2']={'sentence':run[0]['sentence'],
                          'within_recording_z':float(contrast[run[0]['sentence']][feature]) if feature in ('rate','pitchvar','loud') else None,
                          'minimum_effect_met':True}
            regions.append(region)
    for position,row in enumerate(rows):
        if not position or row.get('ref_i') is None or not np.isfinite(row['z'].get('pause',np.nan)):continue
        before=rows[position-1]
        if before.get('ref_i') is None or row['ref_i']!=before['ref_i']+1:continue
        p=inverse('pause',row['values']['pause']);r=inverse('pause',row['reference']['pause']);z=row['z']['pause']
        kind=None
        if z>=settings['k']['awkward_pause'] and p>=settings['awkward_pause_min_s']:kind='awkward_pause'
        elif z<=-settings['k']['missing_pause'] and r>=settings['missing_pause_ref_min_s'] and p<=settings['missing_pause_max_frac']*r:kind='missing_pause'
        if kind is None or not practical_effect(kind,'pause',row,settings)[0]:continue
        start,end=before['end'],row['start']
        if end-start<.03:
            centre=(start+end)/2;start=max(0.,centre-.015);end=min(duration_s,centre+.015)
        region=make_region(kind,'pause',[row],start,end,settings);region['word_start']=before['i']
        region['v2']={'minimum_effect_met':True,'within_recording_z':None}
        regions.append(region)
    return sorted(resolve_conflicts(regions),key=lambda r:(r['start'],r['end'],r['type']))


def recording_contrast(root: Path,rid: str,rows: list[dict],settings: dict) -> dict[int,dict]:
    """Read the provenance-validated real sentence bundle, never human/oracle labels."""
    sentences=pd.read_parquet(root/'data/features/sentences'/f'{rid}.parquet').to_dict('records')
    return sentence_contrast(sentences,rows,settings)


def analyze_v2(audio: Path,text_id: str,mode: str='A',transcript: Path | None=None,
               exclude_speaker: str | None=None,previous: Path | None=None,plot: bool=False,
               root: Path | None=None) -> dict:
    """Separate content-addressed post-hoc A/B inference; v1 files and inference remain untouched."""
    if mode not in ('A','B'):raise ValueError('v2 supports modes A and B; Mode C remains frozen v1')
    if mode=='B' and previous is None:raise ValueError('Mode B requires --previous')
    from speecheval.pipeline import prepare_participant,rounded,plot_analysis
    from speecheval.reference import build_reference,recording_values,map_words
    from speecheval.explain import explanation
    from speecheval.score import rubric_scores
    from speecheval.verify import _write_json
    root=root or Path.cwd();audio=audio.resolve()
    rid,source=prepare_participant(audio,text_id,root,transcript)
    previous_id=prepare_participant(previous.resolve(),text_id,root)[0] if previous else None
    reference=build_reference(text_id,exclude_speaker,root,previous_id if mode=='B' else None)
    alignment,values=recording_values(root,rid)
    mapping=map_words([w['norm'] for w in alignment['words']],reference['words'])
    rows=z_table(alignment,values,reference,mapping)
    path=root/'configs/detector_v2.yaml';settings=yaml.safe_load(path.read_text());config_hash=hashlib.sha256(path.read_bytes()).hexdigest()
    contrast=recording_contrast(root,rid,rows,settings)
    regions=detect_v2(rows,alignment['duration_s'],settings,contrast)
    words=alignment['words'];sentences=alignment['sentences']
    numbers=set('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion'.split())
    for region in regions:
        selected=words[region['word_start']:region['word_end']+1];tags=[]
        if any(w['sentence']==sentences[0]['i'] for w in selected):tags.append('first_sentence')
        if any(w['sentence']==sentences[-1]['i'] for w in selected):tags.append('final_sentence')
        if any(region['word_end']==s['word_end'] for s in sentences):tags.append('sentence_final')
        if any(set(w['norm'].split())&numbers for w in selected):tags.append('contains_number')
        region['tags']=tags;region['explanation']=explanation(region,[w['text'] for w in words],mode)
        own=region['v2']['within_recording_z']
        region['explanation']+=' Post-hoc v2: practical effect and region constraints passed.'
        if own is not None:region['explanation']+=f' Own-sentence robust z={own:.2g}.'
        region['evidence']=rounded(region['evidence']);region['v2']=rounded(region['v2'])
    rubric_path=root/'configs/rubric.yaml';rubric=yaml.safe_load(rubric_path.read_text())
    identity={'version':'post-hoc-v2','mode':mode,'alignment':alignment,'values':rounded(values),
              'sentences_sha256':hashlib.sha256((root/'data/features/sentences'/f'{rid}.parquet').read_bytes()).hexdigest(),
              'reference':reference['reference_version'],'config_sha256':config_hash,
              'rubric_sha256':hashlib.sha256(rubric_path.read_bytes()).hexdigest(),
              'code':{name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in
                      ('detector_v2.py','pipeline.py','detect.py','reference.py','explain.py','score.py')}}
    aid=hashlib.sha256(audio.read_bytes()+json.dumps(identity,sort_keys=True).encode()).hexdigest()[:12]
    baselines=yaml.safe_load((root/'configs/baselines.yaml').read_text())
    result={'schema':'analysis/v1','analysis_id':aid,'recording_id':rid,'text_id':text_id,'mode':mode,
            'reference':{'kind':'previous_take' if mode=='B' else 'distribution','text_id':text_id,'exclude_speaker':exclude_speaker,
                         'n_readers':reference['n_readers'],'reference_version':reference['reference_version'],
                         'baseline_recording_id':previous_id if mode=='B' else baselines.get(text_id)},
            'transcript_source':source,'detector':{'engine':'rules','version':'post-hoc-v2','config_hash':config_hash},
            'duration_s':alignment['duration_s'],'regions':regions,'key_moments':[],
            'scores':rubric_scores(regions,Decimal(str(words[-1]['end']))-Decimal(str(words[0]['start'])),rubric),
            'progress':None,'warnings':alignment['warnings']+[{'type':'post_hoc_detector_v2'},
                            {'type':'unmatched_reference_words','count':mapping.count(None)}]}
    if mode=='B':
        old=analyze_v2(previous,text_id,exclude_speaker=exclude_speaker,root=root)
        current=analyze_v2(audio,text_id,transcript=transcript,exclude_speaker=exclude_speaker,root=root)
        result['progress']={}
        for kind in list(TYPES)+['awkward_pause','missing_pause']:
            def summary(payload):
                found=[r for r in payload['regions'] if r['type']==kind]
                return {'count':len(found),'duration_s':round(sum(r['end']-r['start'] for r in found),3)}
            result['progress'][kind]={'previous':summary(old),'current':summary(current)}
    _write_json(root/'data/analyses_v2'/f'{aid}.json',result)
    if plot:plot_analysis(root,result,alignment,rows,reference)
    return result
