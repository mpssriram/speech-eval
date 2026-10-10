"""Agreement on explicitly supplied ratings; no synthetic human evidence."""
from __future__ import annotations
import csv
import itertools
import math
from pathlib import Path
from statistics import mean
from scipy.stats import spearmanr

TYPES={'rushing','dragging','monotone','too_quiet','mumbling','awkward_pause','missing_pause'}
FIELDS=('rater_id','clip','overall','flaw_type','flaw_time_s')


def _types(value: str) -> set[str]:
    found={part.strip() for part in value.split(';')}
    if found=={'none'}: return set()
    if not found or not found<=TYPES: raise ValueError('Use none or semicolon-separated known flaw types')
    return found


def _validated(rows: list[dict], key: dict) -> list[dict]:
    selected=[];seen=set()
    for row in rows:
        if not str(row.get('overall','')).strip():
            if any(str(row.get(k,'')).strip() for k in ('rater_id','flaw_type','flaw_time_s')):
                raise ValueError('Partially filled rating without overall score')
            continue
        name=str(row.get('clip','')).strip();rater=str(row.get('rater_id','')).strip()
        if not rater or name not in key['clips']:raise ValueError('Missing rater ID or unknown clip')
        value=float(row['overall'])
        if not math.isfinite(value) or value not in (1,2,3,4,5):raise ValueError('Overall must be an integer from 1 to 5')
        types=_types(str(row.get('flaw_type','')))
        times=str(row.get('flaw_time_s','')).strip()
        if not types and times:raise ValueError('No flaw time allowed for none')
        if types:
            if not times:raise ValueError('Approximate flaw time is required')
            values=[float(t.strip()) for t in times.split(';')]
            if len(values)!=len(types) or any(not math.isfinite(t) or not 0<=t<=key['clips'][name]['duration_s'] for t in values):
                raise ValueError('Provide one in-clip time for each declared flaw type')
        identity=(rater,name)
        if identity in seen:raise ValueError('Duplicate rater/clip rating')
        # Preserve paired annotation order; set equality is only for agreement.
        declared=';'.join(part.strip() for part in str(row['flaw_type']).split(';')) if types else 'none'
        seen.add(identity);selected.append({**row,'rater_id':rater,'clip':name,'overall':int(value),'flaw_type':declared,'flaw_time_s':times})
    return selected


def read_ratings(path: Path, key: dict) -> list[dict]:
    """Validate completed CSV rows; blank clip rows are pending, not ratings."""
    with path.open(newline='',encoding='utf-8-sig') as stream:
        reader=csv.DictReader(stream)
        if not set(FIELDS)<=set(reader.fieldnames or []):raise ValueError('Missing rating CSV columns')
        return _validated(list(reader),key)


def _rho(x: list[float], y: list[float]) -> dict:
    n=len(x)
    reason='fewer than three shared clips' if n<3 else 'constant score ranks' if len(set(x))<2 or len(set(y))<2 else None
    return {'n':n,'rho':None if reason else round(float(spearmanr(x,y).statistic),6),'undefined_reason':reason}


def agreement(key: dict, ratings: list[dict]) -> dict:
    """Spearman on shared clips; exact flaw-set agreement, not perceptual validation."""
    ratings=_validated(ratings,key);by_rater={};by_clip={}
    for row in ratings:
        by_rater.setdefault(row['rater_id'],{})[row['clip']]=row
        by_clip.setdefault(row['clip'],[]).append(row)
    clips=sorted(by_clip)
    system=_rho([key['clips'][c]['system']['scores']['overall'] for c in clips],
                [mean(r['overall'] for r in by_clip[c]) for c in clips])
    per_rater={r:_rho([key['clips'][c]['system']['scores']['overall'] for c in sorted(rows)],
                      [rows[c]['overall'] for c in sorted(rows)]) for r,rows in sorted(by_rater.items())}
    pairs=[];hh_type=[]
    for a,b in itertools.combinations(sorted(by_rater),2):
        shared=sorted(by_rater[a].keys()&by_rater[b].keys())
        pairs.append({'raters':[a,b],**_rho([by_rater[a][c]['overall'] for c in shared],[by_rater[b][c]['overall'] for c in shared])})
        hh_type.extend(_types(by_rater[a][c]['flaw_type'])==_types(by_rater[b][c]['flaw_type']) for c in shared)
    def exact(values):
        return {'matches':sum(values),'comparisons':len(values),'fraction':round(sum(values)/len(values),6) if values else None}
    truth=[_types(r['flaw_type'])=={f['type'] for f in key['clips'][r['clip']]['truth']} for r in ratings]
    predicted=[_types(r['flaw_type'])=={f['type'] for f in key['clips'][r['clip']]['system'].get('regions',[])} for r in ratings]
    valid=[p['rho'] for p in pairs if p['rho'] is not None]
    return {'schema':'rating-agreement/v1','source':'explicitly supplied ratings; authenticity not independently verified',
            'ratings':len(ratings),'raters':len(by_rater),'rated_clips':len(clips),'total_clips':len(key['clips']),
            'ratings_per_clip':{c:len(by_clip.get(c,[])) for c in sorted(key['clips'])},
            'system_vs_mean_human':system,'system_vs_each_human':per_rater,
            'human_vs_human':{'pairs':pairs,'defined_pairs':len(valid),'mean_pairwise_rho':round(mean(valid),6) if valid else None},
            'flaw_type_agreement':{'definition':'exact set equality (including none); pooled shared clip/rater comparisons',
                'human_vs_injection_key':exact(truth),'system_vs_human':exact(predicted),'human_vs_human':exact(hh_type)},
            'caveat':'Small convenience pack; no confidence interval or population-validity claim. Undefined correlations are not zero.'}


def clip_measurement(analysis: dict, alignment: dict, start: float, end: float, rubric: dict) -> dict:
    """Project full-context detection into clip seconds, score visible speech span."""
    from speecheval.score import rubric_scores
    speech_start=max(start,alignment['words'][0]['start']);speech_end=min(end,alignment['words'][-1]['end'])
    if not 0<=start<end or speech_start>=speech_end:raise ValueError('Clip must contain positive aligned speech')
    regions=[]
    for region in analysis['regions']:
        a=max(start,region['start']);b=min(end,region['end'])
        if a<b:regions.append({'type':region['type'],'start':round(a-start,3),'end':round(b-start,3),'severity':region['severity']})
    duration=round(speech_end-speech_start,3)
    return {'analysis_id':analysis['analysis_id'],'context':'frozen full-source Mode A, speaker excluded; visible-span rescore',
            'speech_duration_s':duration,'regions':regions,'scores':rubric_scores(regions,duration,rubric)}
