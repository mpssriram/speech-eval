"""Deterministic, unreviewed gold-boundary templates; all times are seconds."""
from __future__ import annotations

import csv
import json
import logging
import math
from pathlib import Path
from typing import Any

import yaml
from praatio import textgrid
from speecheval.align.base import Alignment
from speecheval.verify import _hash_bytes, _write_json

LOGGER=logging.getLogger(__name__)


def choose_recordings(rows: list[dict[str,str]]) -> list[str]:
    """Pick the clean highest-LUFS Gettysburg reader and both government excerpts."""
    clean=[row for row in rows if row['text_id']=='gettysburg' and not row['qa_flags'].strip()
           and math.isfinite(float(row['integrated_lufs']))]
    if not clean:raise ValueError('No clean Gettysburg reader with measured LUFS')
    clean.sort(key=lambda row:(-float(row['integrated_lufs']),row['recording_id']))
    return [clean[0]['recording_id'],'jfk_rice__jfk__orig','reagan_challenger__reagan__orig']


def candidate_boundaries(a: dict[str,Any], b: dict[str,Any], count: int = 20,
                         min_duration_s: float = .15, padding_s: float = .15) -> list[dict[str,Any]]:
    """Select evenly spaced eligible words; average aligner edges, widen, clip in seconds."""
    if count<2 or min_duration_s<=0 or padding_s<0:raise ValueError('Invalid gold selection settings')
    if len(a['words'])!=len(b['words']) or a['duration_s']!=b['duration_s']:
        raise ValueError('Aligners do not describe the same recording')
    excluded=set(a.get('uncertain_words',[]))|set(b.get('uncertain_words',[]))
    for payload in (a,b):
        excluded.update(w['word'] for w in payload.get('warnings',[]) if w['type']=='interpolated')
    eligible=[]
    for index,(left,right) in enumerate(zip(a['words'],b['words'])):
        if left['i']!=index or right['i']!=index or left['text']!=right['text']:
            raise ValueError('Aligner transcript indices/text disagree')
        if index not in excluded and all(w['end']-w['start']>=min_duration_s-1e-9 for w in (left,right)):
            eligible.append(index)
    if len(eligible)<count:raise ValueError(f'Need {count} eligible words; found {len(eligible)}')
    # Fractional stride gives 20 unique samples spanning the entire eligible list.
    selected=[eligible[round(j*(len(eligible)-1)/(count-1))] for j in range(count)]
    result=[]
    for index in selected:
        left,right=a['words'][index],b['words'][index]
        result.append({'word_index':index,'text':left['text'],
            'start':round(max(0.,(left['start']+right['start'])/2-padding_s),3),
            'end':round(min(a['duration_s'],(left['end']+right['end'])/2+padding_s),3),
            'mfa_start':left['start'],'mfa_end':left['end'],
            'whisperx_start':right['start'],'whisperx_end':right['end']})
    if any(x['end']>y['start'] for x,y in zip(result,result[1:])):
        raise ValueError('Expanded gold candidates overlap; do not silently remove annotation padding')
    return result


def prepare_gold(root: Path | None = None) -> None:
    """Write only todo templates, never human gold; preserve edits and reject stale reuse."""
    root=root or Path.cwd()
    config=yaml.safe_load((root/'configs/default.yaml').read_text())
    settings=config.get('gold_alignment',{'words_per_recording':20,'min_duration_s':.15,'padding_s':.15})
    manifest=root/'data/manifest/recordings.csv'
    rows=list(csv.DictReader(manifest.open()))
    rids=choose_recordings(rows)
    if not set(rids).issubset({r['recording_id'] for r in rows}):raise ValueError('Selected recording missing from manifest')
    todo=root/config['paths']['gold']/'todo'
    selection=todo/'selection.json'
    inputs={'data/manifest/recordings.csv':_hash_bytes(manifest.read_bytes())}
    plans={}
    for rid in rids:
        payloads=[]
        for name in ('mfa','whisperx'):
            path=root/config['paths']['alignment']/name/f'{rid}.json'
            inputs[str(path.relative_to(root))]=_hash_bytes(path.read_bytes())
            payload=json.loads(path.read_text())
            Alignment.model_validate(payload)
            if payload['recording_id']!=rid or payload['aligner'].get('name')!=name:
                raise ValueError(f'Alignment identity mismatch: {path}')
            payloads.append(payload)
        plans[rid]={'duration_s':payloads[0]['duration_s'],
                    'items':candidate_boundaries(*payloads,count=settings['words_per_recording'],
                                                min_duration_s=settings['min_duration_s'],padding_s=settings['padding_s'])}
    if selection.exists():
        saved=json.loads(selection.read_text())
        if saved['input_hashes']!=inputs or saved['settings']!=settings:
            raise ValueError('Gold inputs changed; preserve existing annotations and resolve explicitly')
        for filename,sha in saved['template_hashes'].items():
            path=todo/filename
            if not path.exists() or _hash_bytes(path.read_bytes())!=sha:
                raise ValueError(f'Gold template changed: {filename}; preserve manual edits')
        LOGGER.info('Reusing three unreviewed gold templates; waiting for human boundaries');return
    if any((todo/f'{rid}.TextGrid').exists() for rid in rids):
        raise ValueError('Gold template changed or predates provenance; preserve manual edits')
    todo.mkdir(parents=True,exist_ok=True)
    hashes={}
    for rid,plan in plans.items():
        tg=textgrid.Textgrid()
        tg.addTier(textgrid.IntervalTier('gold',[(x['start'],x['end'],x['text']) for x in plan['items']],0,plan['duration_s']))
        path=todo/f'{rid}.TextGrid'
        tg.save(str(path),format='long_textgrid',includeBlankSpaces=True)
        hashes[path.name]=_hash_bytes(path.read_bytes())
    _write_json(selection,{'schema':'gold_candidates/v1','status':'unreviewed_template_not_gold',
        'settings':settings,'selection_method':'rounded_fractional_stride_over_eligible_words',
        'input_hashes':inputs,'template_hashes':hashes,'recordings':plans})
    LOGGER.info('Prepared %d unreviewed templates (%d words each); STOP for human annotation',len(plans),settings['words_per_recording'])
