"""Deterministic word-index and pause-region rules, using real participant timings."""
import numpy as np
from speecheval.reference import inverse,mask_pause_evidence

TYPES={'rushing':('rate',1),'dragging':('rate',-1),'monotone':('pitchvar',-1),
       'too_quiet':('loud',-1),'mumbling':('clarity',-1)}
UNITS={'rate':'syllables/s','pitchvar':'semitones','loud':'dB','clarity':'dB','pause':'s'}


def z_table(alignment: dict, values: list[dict], reference: dict, mapping: list[int | None]) -> list[dict]:
    """Attach reference centres and four-significant-digit z scores; missing evidence is absent."""
    rows=[];values=mask_pause_evidence(values,mapping)
    for word,current,i in zip(alignment['words'],values,mapping):
        row={**word,'ref_i':i,'values':current,'reference':{},'z':{}}
        if i is not None:
            for feature,summary in reference['features'][str(i)].items():
                if summary is not None and np.isfinite(current[feature]):
                    row['reference'][feature]=summary['mu']
                    row['z'][feature]=float(f"{(current[feature]-summary['mu'])/summary['sigma']:.4g}")
        rows.append(row)
    return rows


def severity(z: float, settings: dict) -> int:
    """Severity 1–5 from configured inclusive z cut points."""
    return int(np.clip(np.searchsorted(settings['severity_z_bins'],abs(z),side='right'),1,5))


def make_region(kind: str, feature: str, selected: list[dict], start: float, end: float, settings: dict) -> dict:
    """Summarize transformed evidence, restore measured units, use participant seconds."""
    z=float(np.mean([r['z'][feature] for r in selected]))
    mean_abs=float(np.mean([abs(r['z'][feature]) for r in selected]))
    return {'type':kind,'start':round(start,3),'end':round(end,3),
            'word_start':selected[0]['i'],'word_end':selected[-1]['i'],'severity':severity(mean_abs,settings),
            'mean_abs_z':float(f'{mean_abs:.4g}'),
            'evidence':{'feature':feature,'participant':inverse(feature,float(np.mean([r['values'][feature] for r in selected]))),
                        'reference':inverse(feature,float(np.mean([r['reference'][feature] for r in selected]))),
                        'unit':UNITS[feature],'z':z},'tags':[]}


def resolve_conflicts(regions: list[dict]) -> list[dict]:
    """Apply the three ordered containment suppression rules, not overlap suppression."""
    result=list(regions)
    for minor,major,strict in [('missing_pause','rushing',True),('awkward_pause','dragging',True),('too_quiet','mumbling',False)]:
        keep=[]
        for region in result:
            drop=False
            if region['type']==minor:
                for other in result:
                    if other['type']!=major:continue
                    inside=(other['start']<region['start'] and region['end']<other['end']) if strict else (other['start']<=region['start'] and region['end']<=other['end'])
                    if inside and (strict or region['mean_abs_z']<other['mean_abs_z']):drop=True;break
            if not drop:keep.append(region)
        result=keep
    return result


def detect(rows: list[dict], duration_s: float, settings: dict) -> list[dict]:
    """Group signed anomalies within sentences; unknown words are hard comparison barriers."""
    regions=[]
    for kind,(feature,direction) in TYPES.items():
        runs=[];current=[]
        for row in rows:
            valid=row.get('ref_i') is not None and np.isfinite(row['z'].get(feature,np.nan))
            if not valid:
                if current:runs.append(current);current=[]
                continue
            flagged=direction*row['z'][feature]>=settings['k'][kind]
            if not flagged:continue
            if current and (row['sentence']!=current[-1]['sentence'] or row['i']-current[-1]['i']-1>settings['region_max_gap_words']):
                runs.append(current);current=[]
            current.append(row)
        if current:runs.append(current)
        for run in runs:
            if len(run)<settings['region_min_words']:continue
            regions.append(make_region(kind,feature,run,run[0]['start'],run[-1]['end'],settings))
    for position,row in enumerate(rows):
        if position==0 or row.get('ref_i') is None or not np.isfinite(row['z'].get('pause',np.nan)):continue
        if rows[position-1].get('ref_i') is None or row['ref_i']!=rows[position-1]['ref_i']+1:continue
        p=inverse('pause',row['values']['pause']);r=inverse('pause',row['reference']['pause']);z=row['z']['pause']
        kind=None
        if z>=settings['k']['awkward_pause'] and p>=settings['awkward_pause_min_s']:kind='awkward_pause'
        elif z<=-settings['k']['missing_pause'] and r>=settings['missing_pause_ref_min_s'] and p<=settings['missing_pause_max_frac']*r:kind='missing_pause'
        if kind:
            start,end=rows[position-1]['end'],row['start']
            if end-start<.03:
                centre=(start+end)/2;start=max(0.,centre-.015);end=min(duration_s,centre+.015)
            region=make_region(kind,'pause',[row],start,end,settings)
            region['word_start']=rows[position-1]['i'];regions.append(region)
    return sorted(resolve_conflicts(regions),key=lambda r:(r['start'],r['end'],r['type']))
