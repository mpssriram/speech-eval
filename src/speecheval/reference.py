"""Train-only robust reference distributions; transformed feature units are explicit."""
from __future__ import annotations

import difflib
import hashlib
import importlib.metadata
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

FEATURES={'rate':('windows','rate_syl_s'),'pitchvar':('windows','f0_st_std'),
          'loud':('windows','int_rel_db_mean'),'clarity':('windows','hiband_ratio_db_mean'),
          'pause':('words','pause_before_s')}
SCALE_FLOOR=.001


def validate_identifier(value: str) -> None:
    if not re.fullmatch('[a-z][a-z0-9_]*',value):raise ValueError('Invalid identifier')


def mask_pause_evidence(values: list[dict], mapping: list[int | None]) -> list[dict]:
    """A pause belongs to two endpoints; only the same adjacent reference boundary is comparable."""
    result=[dict(v) for v in values]
    for j,i in enumerate(mapping):
        if j==0 or i is None or mapping[j-1] is None or i!=mapping[j-1]+1:result[j]['pause']=float('nan')
    return result


def validate_measurement_provenance(root: Path,rid: str) -> None:
    """Reject audio/boundaries/features not bound to their actual producer inputs and artifacts."""
    def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    alignment_path=root/'data/alignment'/f'{rid}.json';alignment=json.loads(alignment_path.read_text())
    audio=(root/alignment['audio']).resolve()
    if not audio.is_relative_to(root.resolve()):raise ValueError('Audio provenance path escapes project')
    outputs=[f'data/features/{folder}/{rid}.parquet' for folder in ('frames','words','windows','sentences')]+[f'data/features/speaker_stats/{rid}.json']
    versions={p:importlib.metadata.version(p) for p in ('librosa','praat-parselmouth','numpy','pandas','pyarrow','cmudict')}
    settings=yaml.safe_load((root/'configs/default.yaml').read_text())['features']
    code_sha=digest(Path(__file__).parent/'features.py')
    source=root/'data/features/provenance.json'
    if source.exists():
        saved=json.loads(source.read_text());inputs=saved.get('inputs',{})
        if rid in inputs.get('recordings',{}):
            expected={'audio':digest(audio),'alignment':digest(alignment_path)}
            code={f'src/speecheval/{name}':digest(Path(__file__).parent/name) for name in ('features.py','transcripts.py')}
            valid=inputs['recordings'][rid]==expected and inputs.get('settings')==settings and inputs.get('versions')==versions and inputs.get('code')==code
            valid=valid and all(saved.get('artifacts',{}).get(p)==digest(root/p) for p in outputs)
            if not valid:raise ValueError(f'Stale source feature provenance: {rid}; run features all')
            return
    text,speaker,variant=rid.split('__',2)
    work=root/'data/.cache/dataset'/f'{text}__{speaker}__orig'/'features.json'
    if work.exists():
        saved=json.loads(work.read_text());inputs=saved.get('inputs',{})
        if rid in inputs.get('hq_audio_hashes',{}):
            valid=inputs['hq_audio_hashes'][rid]==digest(audio) and inputs.get('real_alignment_artifacts',{}).get(str(alignment_path.relative_to(root)))==digest(alignment_path)
            valid=valid and inputs.get('settings')==settings and inputs.get('versions')==versions and inputs.get('code_sha256')==code_sha
            valid=valid and all(saved.get('artifacts',{}).get(p)==digest(root/p) for p in outputs)
            if not valid:raise ValueError(f'Stale dataset feature provenance: {rid}; resume dataset build')
            return
    for state in (root/'data/.cache/participants').glob('*/state.json'):
        saved=json.loads(state.read_text());artifacts=saved.get('artifacts',{})
        if str(alignment_path.relative_to(root)) not in artifacts:continue
        from speecheval.pipeline import participant_code_identity,participant_model_identity
        valid=saved.get('inputs',{}).get('producer')==participant_code_identity()
        valid=valid and saved.get('inputs',{}).get('settings')==yaml.safe_load((root/'configs/default.yaml').read_text())
        valid=valid and saved.get('inputs',{}).get('models')==participant_model_identity(root,yaml.safe_load((root/'configs/default.yaml').read_text()),saved.get('transcript_source')=='automatic_as_read')
        valid=valid and all(artifacts.get(p)==digest(root/p) for p in outputs+[str(audio.relative_to(root)),str(alignment_path.relative_to(root))])
        if not valid:raise ValueError(f'Stale participant feature provenance: {rid}; regenerate participant input')
        return
    raise ValueError(f'Missing measurement provenance for {rid}')


def transform(feature: str, value: float) -> float:
    """Natural-log rate/pitch variation/pause, or identity dB; invalid evidence stays NaN."""
    if not np.isfinite(value):return float('nan')
    if feature in ('rate','pitchvar','pause'):
        if value<0 or (feature=='rate' and value==0):return float('nan')
        return float(np.log(value+{'rate':0.,'pitchvar':.25,'pause':.05}[feature]))
    return float(value)


def inverse(feature: str, value: float) -> float:
    """Restore transformed values to syllables/s, semitones, seconds, or dB."""
    return float(np.exp(value)-{'rate':0.,'pitchvar':.25,'pause':.05}[feature]) if feature in ('rate','pitchvar','pause') else float(value)


def summarize(values: list[float], pool: float, n0: int = 5) -> dict | None:
    """Median/MAD and specified shrinkage; count finite readers separately per feature."""
    x=np.asarray(values,dtype=float);x=x[np.isfinite(x)]
    if not len(x):return None
    mu=float(np.median(x));s=float(1.4826*np.median(np.abs(x-mu)))
    pool=max(SCALE_FLOOR,float(pool));n=len(x)
    return {'mu':mu,'s':s,'sigma':float(np.sqrt((n*s*s+n0*pool*pool)/(n+n0))),'n':n}


def map_words(participant: list[str], reference: list[str]) -> list[int | None]:
    """Map complete normalized words only; inserted/partial/substituted words are unmatched."""
    from speecheval.transcripts import normalize_tokens
    def flatten(words):
        tokens=[];owners=[];indices=[]
        for i,word in enumerate(words):
            normalized=normalize_tokens(word);indices.append(list(range(len(tokens),len(tokens)+len(normalized))))
            tokens.extend(normalized);owners.extend([i]*len(normalized))
        return tokens,owners,indices
    a,ao,ai=flatten(participant);b,bo,bi=flatten(reference)
    matched={}
    for block in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
        for offset in range(block.size):matched[block.a+offset]=block.b+offset
    result=[]
    for group in ai:
        positions=[matched.get(j) for j in group]
        if not group or any(j is None for j in positions):result.append(None);continue
        owner=bo[positions[0]]
        result.append(owner if positions==bi[owner] else None)
    return result


def build_baselines(root: Path) -> dict:
    """Freeze playback choices: smallest train-reader mean absolute leave-one-reader-out z."""
    from speecheval.detect import z_table
    path=root/'configs/baselines.yaml'
    if path.exists():return yaml.safe_load(path.read_text())
    chosen={}
    for text in ('gettysburg','o_captain'):
        readers,_=collect_readers(root,text);scores=[]
        for rid in readers:
            reference=build_reference(text,rid.split('__')[1],root)
            alignment,values=recording_values(root,rid)
            rows=z_table(alignment,values,reference,map_words([w['norm'] for w in alignment['words']],reference['words']))
            z=[abs(value) for row in rows for value in row['z'].values() if np.isfinite(value)]
            if z:scores.append((float(np.mean(z)),rid))
        if not scores:raise ValueError(f'No train-reader baseline evidence for {text}')
        chosen[text]=min(scores)[1]
    chosen.update(jfk_rice='jfk_rice__jfk__orig',reagan_challenger='reagan_challenger__reagan__orig')
    path.write_text(yaml.safe_dump(chosen,sort_keys=True));return chosen


def recording_values(root: Path, rid: str) -> tuple[dict,list[dict]]:
    """Read real promoted word/window features, never oracle alignment."""
    validate_measurement_provenance(root,rid)
    alignment=json.loads((root/'data/alignment'/f'{rid}.json').read_text())
    tables={folder:pd.read_parquet(root/'data/features'/folder/f'{rid}.parquet').set_index('i') for folder in ('words','windows')}
    values=[]
    for word in alignment['words']:
        row={}
        for feature,(folder,col) in FEATURES.items():
            value=float(tables[folder].loc[word['i'],col])
            if word['i'] in alignment.get('uncertain_words',[]):value=float('nan')
            row[feature]=transform(feature,value)
        values.append(row)
    return alignment,values


def canonical_words(root: Path, text_id: str) -> list[str]:
    from speecheval.transcripts import _body_text
    return _body_text((root/'data/transcripts/canonical'/f'{text_id}.txt').read_text()).split()


def collect_readers(root: Path,text_id: str,exclude_speaker: str | None = None) -> tuple[list[str],dict]:
    """Map only clean train readers into canonical words; optional whole-speaker exclusion."""
    splits=yaml.safe_load((root/'configs/splits.yaml').read_text())
    words=canonical_words(root,text_id);collected={i:{f:[] for f in FEATURES} for i in range(len(words))};ids=[]
    for rid in sorted(splits['train']):
        text,speaker,_=rid.split('__',2)
        if text!=text_id or speaker==exclude_speaker:continue
        alignment,values=recording_values(root,rid);ids.append(rid)
        mapping=map_words([w['norm'] for w in alignment['words']],words)
        values=mask_pause_evidence(values,mapping)
        for j,i in enumerate(mapping):
            if i is not None:
                for feature in FEATURES:collected[i][feature].append(values[j][feature])
    return ids,collected


def pooled_sigma(root: Path,exclude_speaker: str | None = None) -> dict:
    """Median wordwise robust spread over Gettysburg/O Captain training sources only."""
    from speecheval.verify import _write_json
    samples={f:[] for f in FEATURES};ids=[]
    for text in ('gettysburg','o_captain'):
        readers,collected=collect_readers(root,text,exclude_speaker);ids.extend(readers)
        for row in collected.values():
            for feature,values in row.items():
                summary=summarize(values,1.)
                if summary and summary['n']>=2:samples[feature].append(summary['s'])
    if not ids:raise ValueError('No training readers available for pooled sigma')
    result={'schema':'pooled_sigma/v1','readers':ids,'exclude_speaker':exclude_speaker,'n0':5,'scale_floor':SCALE_FLOOR,
            'sigma':{f:max(SCALE_FLOOR,float(np.median(v))) if v else SCALE_FLOOR for f,v in samples.items()}}
    _write_json(root/'data/reference'/f"pooled_sigma{'__excl-'+exclude_speaker if exclude_speaker else ''}.json",result);return result


def build_reference(text_id: str, exclude_speaker: str | None = None, root: Path | None = None,
                    previous_id: str | None = None) -> dict:
    """Build hash-versioned robust reference; Mode B uses explicitly selected previous take."""
    from speecheval.verify import _write_json
    validate_identifier(text_id)
    if exclude_speaker is not None:validate_identifier(exclude_speaker)
    if previous_id is not None:
        parts=previous_id.split('__')
        if len(parts)!=3:raise ValueError('Invalid recording identifier')
        for part in parts:validate_identifier(part)
    root=root or Path.cwd();pool=pooled_sigma(root,exclude_speaker);words=canonical_words(root,text_id)
    readers,collected=collect_readers(root,text_id,exclude_speaker)
    if previous_id is not None or not readers:
        if previous_id is None:
            if text_id not in ('jfk_rice','reagan_challenger'):raise ValueError('No eligible reference readers')
            previous_id=f"{text_id}__{'jfk' if text_id=='jfk_rice' else 'reagan'}__orig"
        alignment,values=recording_values(root,previous_id)
        if alignment['recording_id'].split('__',1)[0]!=text_id:raise ValueError('Previous take is a different text')
        if alignment['recording_id'].split('__')[1]==exclude_speaker:raise ValueError('Reference speaker is excluded')
        readers=[previous_id];collected={i:{f:[] for f in FEATURES} for i in range(len(words))}
        mapping=map_words([w['norm'] for w in alignment['words']],words);values=mask_pause_evidence(values,mapping)
        for j,i in enumerate(mapping):
            if i is not None:
                for f in FEATURES:collected[i][f].append(values[j][f])
    inputs={}
    for rid in sorted(set(readers+pool['readers'])):
        for folder in ('words','windows'):
            path=root/'data/features'/folder/f'{rid}.parquet';inputs[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
        path=root/'data/alignment'/f'{rid}.json';inputs[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
    for relative in (f'data/transcripts/canonical/{text_id}.txt','configs/splits.yaml'):
        inputs[relative]=hashlib.sha256((root/relative).read_bytes()).hexdigest()
    identity={'inputs':inputs,'pool':pool,'exclude_speaker':exclude_speaker,'previous_id':previous_id,
              'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    version=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    result={'schema':'reference/v1','text_id':text_id,'exclude_speaker':exclude_speaker,'readers':readers,
            'n_readers':len(readers),'words':words,'reference_version':version,'inputs':identity,
            'features':{str(i):{f:summarize(v,pool['sigma'][f]) for f,v in row.items()} for i,row in collected.items()}}
    suffix=previous_id if previous_id else exclude_speaker or 'none'
    output=root/'data/reference'/f'{text_id}__excl-{suffix}.json'
    if not output.resolve().is_relative_to((root/'data/reference').resolve()):raise ValueError('Reference output escaped directory')
    _write_json(output,result)
    return result
