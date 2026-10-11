"""Fixed recorder-confirmed label geometry and matching, separate from detectors."""
from __future__ import annotations
import math
from itertools import product
from speecheval.human_recording_inputs import norm


def grounded_regions(take_id: str, detail: dict, alignment: dict,
                     units: list[dict]) -> tuple[list[dict],list[dict],list[str]]:
    """Map fixed canonical units/word anchors to actual MFA seconds; never flags."""
    if detail.get('excluded_from_scoring'):return [],[],['excluded; unknown flaws, not clean']
    words=alignment['words'];primary=[];secondary=[];basis=[]
    def selected(number: int) -> list[dict]:
        unit=next((u for u in units if u['canonical_unit']==number),None)
        if unit is None:raise ValueError(f'Missing canonical unit {number}')
        result=words[unit['word_start']:unit['word_end']+1]
        if not result or any(w['sentence']!=number-1 for w in result):
            raise ValueError('Canonical unit word mapping does not match actual MFA transcript')
        if any(w['i'] in alignment.get('uncertain_words',[]) for w in result):
            raise ValueError('Intended unit has uncertain word evidence; cannot invent a label')
        return result
    def phrase(local: list[dict], wanted: list[str]) -> list[dict]:
        matches=[local[i:i+len(wanted)] for i in range(len(local)-len(wanted)+1)
                 if [norm(w['norm']) for w in local[i:i+len(wanted)]]==wanted]
        if len(matches)!=1:raise ValueError(f'Missing/ambiguous fixed anchor {"|".join(wanted)} in {take_id}')
        return matches[0]
    for note in detail['flaws']:
        number=note['sentence'];kind=note['type'];local=selected(number)
        start,end=local[0]['start'],local[-1]['end'];first,last=local[0]['i'],local[-1]['i']
        secondary.append({'type':kind,'start':start,'end':end,'canonical_unit':number})
        description=f'canonical unit {number}, actual MFA whole-unit interval'
        if kind=='awkward_pause':
            wanted=['larger','sense'] if take_id=='gettysburg__user__take02' else ['were','daring']
            pair=phrase(local,wanted);start,end=pair[0]['end'],pair[1]['start']
            first,last=pair[0]['i'],pair[1]['i'];description='fixed phrase-internal gap '+ '|'.join(wanted)
        elif kind=='missing_pause':
            following=selected(number+1);start,end=local[-1]['end'],following[0]['start']
            first,last=local[-1]['i'],following[0]['i'];description=f'fixed canonical boundary {number}/{number+1}'
        elif kind=='too_quiet':
            if len(local)<4:raise ValueError('Trail-off unit contains fewer than four words')
            start=local[-4]['start'];first=local[-4]['i'];description=f'fixed last four words of canonical unit {number}'
        elif kind=='dragging' and take_id=='gettysburg__user__take03':
            positions=[[i for i,w in enumerate(local) if norm(w['norm'])==target]
                       for target in ('have','thus','far')]
            matches=[p for p in product(*positions) if p[0]<p[1]<p[2]]
            if len(matches)!=1:raise ValueError(f'Missing/ambiguous fixed anchor have|thus|far in {take_id}')
            part=[local[matches[0][0]],local[matches[0][-1]]]
            start,end=part[0]['start'],part[-1]['end']
            first,last=part[0]['i'],part[-1]['i'];description='fixed ordered word span have thus far, including intervening ASR insertions'
        if kind in ('awkward_pause','missing_pause') and end-start<.03:
            centre=(start+end)/2;start=max(0.,centre-.015);end=min(alignment['duration_s'],centre+.015)
            description+='; 30 ms event representation for sub-30 ms MFA gap'
        if not all(math.isfinite(v) for v in (start,end)) or not 0<=start<end<=alignment['duration_s']:
            raise ValueError('Fixed label interval lies outside the actual recording')
        primary.append({'type':kind,'start':round(start,3),'end':round(end,3),
                        'word_start':first,'word_end':last,'canonical_unit':number})
        basis.append(description)
    return primary,secondary,basis


def compare_grounded(predicted: list[dict], truth: list[dict], unit_truth: list[dict]) -> dict:
    """Primary IoU .3; historical pause-centre .25 s; secondary positive unit overlap."""
    from speecheval.human_takes import compare_regions
    from speecheval.evaluate import temporal_iou
    result=compare_regions(predicted,truth)
    candidates=[(-temporal_iou(p,t),i,j) for i,p in enumerate(predicted) for j,t in enumerate(unit_truth)
                if p['type']==t['type'] and temporal_iou(p,t)>0]
    ps=set();ts=set()
    for _,i,j in sorted(candidates):
        if i not in ps and j not in ts:ps.add(i);ts.add(j)
    return {'primary':result['strict_iou'],'historical_pause_policy':result['synthetic_policy'],
            'secondary':{'hits':len(ts),'misses':len(unit_truth)-len(ts),
                         'false_positives':len(predicted)-len(ps)}}
