"""Speaker-disjoint frozen splits and reproducible synthetic dataset construction."""
from __future__ import annotations
import csv
import copy
import difflib
import hashlib
import json
import logging
import shutil
import time
import importlib.metadata
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing
import os
import numpy as np
import yaml
import soundfile as sf
from speecheval.transcripts import _body_text, normalize_tokens

LOGGER=logging.getLogger(__name__)


def assign_splits(rows: list[dict], excluded: dict[str,str]) -> dict:
    """Reserve dev/test readers before assigning every remaining reader to train."""
    result={'schema':'splits/v1','train':[],'dev':[],'test':[],'excluded':dict(sorted(excluded.items()))}
    texts=sorted({r['text_id'] for r in rows})
    owners={}
    for text in texts:
        group=sorted([r for r in rows if r['text_id']==text and r['recording_id'] not in excluded],key=lambda r:r['speaker_slug'])
        if text in ('jfk_rice','reagan_challenger'):
            groups={'test':group}
        else:
            test_count=3 if text=='gettysburg' else 2
            if len(group)<test_count+3:raise ValueError(f'Too few readers to split {text}')
            remaining=group[:-test_count]
            dev_start=min(10 if text=='gettysburg' else 8,len(remaining)-2)
            groups={'dev':remaining[dev_start:dev_start+2],'test':group[-test_count:],
                    'train':remaining[:dev_start]+remaining[dev_start+2:]}
        for split,entries in groups.items():
            for row in entries:
                speaker=row['speaker_slug']
                if speaker in owners and owners[speaker]!=split:raise ValueError(f'speaker leakage: {speaker}')
                owners[speaker]=split;result[split].append(row['recording_id'])
    for split in ('train','dev','test'):result[split].sort()
    return result


def freeze_splits(path: Path, value: dict) -> None:
    """Write once; reject any later membership or exclusion change without overwriting."""
    if path.exists():
        if yaml.safe_load(path.read_text())!=value:raise ValueError('Dataset splits are frozen; explicit versioning is required')
        return
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(yaml.safe_dump(value,sort_keys=True),encoding='utf-8')


def source_splits(root: Path) -> dict:
    """Apply clipping/pitch/transcript exclusions before freezing speaker membership."""
    rows=list(csv.DictReader((root/'data/manifest/recordings.csv').open()))
    qa={r['recording_id']:r for r in json.loads((root/'data/features/qa.json').read_text())['recordings']}
    versions=yaml.safe_load((root/'data/manifest/transcript_versions.yaml').read_text());excluded={}
    for row in rows:
        rid=row['recording_id'];reasons=[]
        if float(row['clipped_fraction'])>0:reasons.append('clipped source samples')
        if qa[rid]['flagged']:reasons.append('pitch QA: octave jumps or out-of-range median')
        canonical=root/'data/transcripts/canonical'/f"{row['text_id']}.txt"
        if row['text_id']=='gettysburg':
            version=versions[rid]['applied_version'];canonical=root/'data/transcripts/canonical/gettysburg_versions'/f'{version}.txt'
        expected=normalize_tokens(_body_text(canonical.read_text()));spoken=normalize_tokens(_body_text((root/'data/transcripts/as_spoken'/f'{rid}.txt').read_text()))
        edits,denominator=transcript_difference(expected,spoken,excerpt=row['text_id']=='jfk_rice')
        if edits/max(1,denominator)>.1:reasons.append(f'transcript deviation {edits}/{denominator} exceeds 10%')
        if reasons:excluded[rid]='; '.join(reasons)
    value=assign_splits(rows,excluded);freeze_splits(root/'configs/splits.yaml',value)
    return value


def transcript_difference(expected: list[str], spoken: list[str], excerpt: bool = False) -> tuple[int,int]:
    """Token differences; intentional JFK excerpts ignore unrecorded canonical bookends."""
    if not excerpt:
        edits=sum(max(b-a,d-c) for tag,a,b,c,d in difflib.SequenceMatcher(None,expected,spoken,autojunk=False).get_opcodes() if tag!='equal')
        return edits,len(expected)
    # Semiglobal Levenshtein: free canonical prefix/suffix, ordinary costs inside.
    # Ties prefer the longer covered span, not deleting a troublesome edge word.
    previous=[(0,j) for j in range(len(expected)+1)]
    for i,word in enumerate(spoken,1):
        current=[(i,0)]
        for j,canonical in enumerate(expected,1):
            current.append(min((previous[j][0]+1,previous[j][1]),
                               (current[j-1][0]+1,current[j-1][1]),
                               (previous[j-1][0]+(word!=canonical),previous[j-1][1])))
        previous=current
    candidates=[(cost,-(end-start),end,start) for end,(cost,start) in enumerate(previous)]
    cost,negative_length,_,_=min(candidates)
    return cost,-negative_length


def compose_maps(first: list[list[float]], second: list[list[float]]) -> list[list[float]]:
    """Compose source-to-intermediate and intermediate-to-output seconds, retaining steps."""
    from speecheval.inject import map_time
    knots={p[0] for p in first}
    for t,_ in second:
        for (a,c),(b,d) in zip(first,first[1:]):
            if b>a and d>c and c<=t<=d:knots.add(a+(t-c)*(b-a)/(d-c))
    result=[]
    for t in sorted(knots):
        left=map_time(map_time(t,first,side='left'),second,side='left')
        right=map_time(map_time(t,first,side='right'),second,side='right')
        result.append([t,left])
        if abs(right-left)>1e-9:result.append([t,right])
    return result


def choose_mixed_sites(alignment: dict, config: dict, index: int) -> list[dict] | None:
    """Choose three distinct seeded effects, chronologically ordered and at least 2 s apart."""
    from speecheval.inject import choose_site
    digest=hashlib.sha256(f"{config['seed']}|{alignment['recording_id']}|mixed|{index}".encode()).digest()
    rng=np.random.default_rng(int.from_bytes(digest[:8],'big'));words=alignment['words']
    for attempt in range(128):
        chosen=[]
        for position,kind in enumerate(rng.choice(sorted(config['types']),3,replace=False)):
            severity=int(rng.integers(2,6));shape='trail' if kind=='too_quiet' and severity%2==0 else 'flat'
            placement=index*1000+attempt*3+position
            site=choose_site(alignment,config,str(kind),severity,placement,shape)
            if site is None:break
            chosen.append({'type':str(kind),'severity':severity,'site':site,'shape':shape,'placement':placement})
        if len(chosen)!=3:continue
        chosen.sort(key=lambda item:item['site'][0])
        if all(words[b['site'][0]]['start']-words[a['site'][1]]['end']>=config['min_gap_between_flaws_s'] for a,b in zip(chosen,chosen[1:])):return chosen
    return None


def generate_mixed(root: Path, audio: Path, alignment: dict, stats: dict, config: dict,
                   index: int, force: bool = False) -> dict | None:
    """Generate three separated effects and a composed oracle, without real-aligner leakage."""
    from speecheval.inject import inject_once, map_time, safe_output_pair, Label, rubberband_version
    from speecheval.align.base import Alignment
    from speecheval.verify import _write_json
    rid=alignment['recording_id'].rsplit('__',1)[0]+f'__mixed_{index:02d}'
    cache=root/'data/flawed/provenance'/f'{rid}.json'
    def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
    identity={'audio_sha256':hashlib.sha256(audio.read_bytes()).hexdigest(),'alignment_sha256':digest(alignment),
        'stats_sha256':digest(stats),'config':config,'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'inject_code_sha256':hashlib.sha256((Path(__file__).parent/'inject.py').read_bytes()).hexdigest(),
        'rubberband':rubberband_version(),'versions':{p:importlib.metadata.version(p) for p in ('numpy','scipy','praat-parselmouth','soundfile')}}
    if cache.exists() and not force:
        old=json.loads(cache.read_text())
        if old.get('inputs')==identity and all((root/p).exists() and hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in old['artifacts'].items()):return old
    sites=choose_mixed_sites(alignment,config,index)
    if sites is None:return None
    wet,sr=sf.read(audio,dtype='float32')
    if sr!=44100 or wet.ndim!=1:raise ValueError('Mixed injection requires 44.1 kHz mono')
    current=copy.deepcopy(alignment);mapping=[[0.,0.],[len(wet)/sr,len(wet)/sr]];flaws=[];global_db=0.
    for site in sites:
        wet,label,step,current=inject_once(wet,sr,current,stats,config,site['type'],site['severity'],
            site['placement'],root/'data/.cache/inject',site=site['site'],shape=site['shape'])
        for flaw in flaws:
            flaw['start']=round(map_time(flaw['start'],step),3);flaw['end']=round(map_time(flaw['end'],step,side='left'),3)
        flaws.append(label['flaws'][0]);global_db+=label['flaws'][0]['parameters'].get('peak_normalised_db',0.)
        mapping=compose_maps(mapping,step)
    wet,down,adjustment=safe_output_pair(wet,sr);global_db+=adjustment
    for flaw in flaws:
        if global_db<0:flaw['parameters']['peak_normalised_db']=global_db
        flaw['parameters']={k:(round(v,3) if k.endswith('_s') else float(f'{v:.4g}')) if isinstance(v,float) else v for k,v in flaw['parameters'].items()}
    label={'schema':'labels/v1','recording_id':rid,'reference_id':alignment['recording_id'],
           'text_id':rid.split('__')[0],'source':'synthetic','flaws':flaws};Label.model_validate(label)
    oracle=copy.deepcopy(alignment);oracle.update(recording_id=rid,audio=f'data/flawed/hq/{rid}.flac',
        duration_s=round(len(wet)/sr,3),aligner={'name':'oracle','version':'1'})
    for word in oracle['words']:
        word['start']=round(map_time(word['start'],mapping),3);word['end']=round(map_time(word['end'],mapping,side='left'),3)
    for sentence in oracle['sentences']:
        sentence['start']=oracle['words'][sentence['word_start']]['start'];sentence['end']=oracle['words'][sentence['word_end']]['end']
    Alignment.model_validate(oracle)
    paths=[root/'data/flawed'/folder/f'{rid}.flac' for folder in ('hq','align16k')]
    for path in paths:path.parent.mkdir(parents=True,exist_ok=True)
    sf.write(paths[0],wet,44100,subtype='PCM_16');sf.write(paths[1],down,16000,subtype='PCM_16')
    paths.extend([root/'data/labels'/f'{rid}.json',root/'data/flawed/timemaps'/f'{rid}.json',root/'data/alignment/oracle'/f'{rid}.json'])
    _write_json(paths[2],label);_write_json(paths[3],{'schema':'timemap/v1','source_id':alignment['recording_id'],
        'recording_id':rid,'breakpoints':[[round(a,3),round(b,3)] for a,b in mapping]});_write_json(paths[4],oracle)
    record={'schema':'injection_provenance/v1','recording_id':rid,'inputs':identity,
            'artifacts':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    _write_json(cache,record);return record


def restore_sentences(real: dict, source: dict) -> dict:
    """Restore text-based sentence membership; boundaries come ONLY from real MFA words."""
    from speecheval.align.base import Alignment
    if [w['norm'] for w in real['words']]!=[w['norm'] for w in source['words']]:raise ValueError('Real alignment transcript coverage changed')
    result=copy.deepcopy(real)
    for word,original in zip(result['words'],source['words']):word['sentence']=original['sentence']
    result['sentences']=copy.deepcopy(source['sentences']);result['uncertain_words']=source.get('uncertain_words',[])
    for sentence in result['sentences']:
        sentence['start']=result['words'][sentence['word_start']]['start'];sentence['end']=result['words'][sentence['word_end']]['end']
    Alignment.model_validate(result);return result


def extract_dataset_features(root: Path, records: list[dict], alignment_artifacts: dict, settings: dict, state: Path) -> dict:
    """Reuse features only when real boundaries AND the measured HQ signal match."""
    from speecheval.features import extract_features
    from speecheval.verify import _write_json
    inputs={'real_alignment_artifacts':alignment_artifacts,'settings':settings,
            'hq_audio_hashes':{r['recording_id']:hashlib.sha256((root/'data/flawed/hq'/f"{r['recording_id']}.flac").read_bytes()).hexdigest() for r in records},
            'code_sha256':hashlib.sha256((Path(__file__).parent/'features.py').read_bytes()).hexdigest(),
            'versions':{p:importlib.metadata.version(p) for p in ('librosa','praat-parselmouth','numpy','pandas','pyarrow','cmudict')}}
    previous=json.loads(state.read_text()) if state.exists() else {}
    cached=previous.get('inputs')==inputs and len(previous.get('artifacts',{}))==5*len(records) and all((root/p).exists() and hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in previous.get('artifacts',{}).items())
    if not cached:
        hashes={}
        for record in records:
            rid=record['recording_id'];real=json.loads((root/'data/alignment'/f'{rid}.json').read_text())
            hashes.update(extract_features(root,root/'data/flawed/hq'/f'{rid}.flac',real,settings))
        _write_json(state,{'inputs':inputs,'artifacts':hashes})
    return json.loads(state.read_text())


def build_source(root: Path, source_id: str, flaws_config: dict, config: dict, stage: str = 'all') -> dict:
    """Generate one reader's variants, then align real audio without oracle windows and extract features."""
    from speecheval.inject import generate_one,choose_site
    from speecheval.align.mfa import run_mfa,ensure_adoption
    from speecheval.align.base import write_textgrid
    from speecheval.features import extract_features
    from speecheval.verify import _write_json
    logging.basicConfig(level=logging.INFO,format='%(processName)s %(message)s')
    if stage not in ('generate','align','all'):raise ValueError('Unknown dataset stage')
    LOGGER.info('Dataset source %s: generating',source_id)
    source=json.loads((root/'data/alignment'/f'{source_id}.json').read_text())
    audio=root/'data/audio/hq'/f'{source_id}.wav';stats=json.loads((root/'data/features/speaker_stats'/f'{source_id}.json').read_text())
    records=[];skipped=[]
    for kind in flaws_config['types']:
        for severity in range(1,6):
            shape='trail' if kind=='too_quiet' and severity%2==0 else 'flat'
            if choose_site(source,flaws_config,kind,severity,1,shape) is None:
                skipped.append({'source_id':source_id,'type':kind,'severity':severity,'reason':'no eligible site'});continue
            try:records.append(generate_one(root,audio,source,stats,flaws_config,kind,severity,1,shape=shape))
            except ValueError as error:
                if 'No 300 ms inter-word room tone' not in str(error):raise
                skipped.append({'source_id':source_id,'type':kind,'severity':severity,'reason':str(error)})
    for index in range(1,config.get('dataset',{}).get('mixed_per_source',2)+1):
        record=generate_mixed(root,audio,source,stats,flaws_config,index)
        if record is None:skipped.append({'source_id':source_id,'type':'mixed','index':index,'reason':'no three separated eligible sites'})
        else:records.append(record)
    records.sort(key=lambda r:r['recording_id'])
    result={'source_id':source_id,'records':records,'skipped':skipped,'real_alignment_completed':False,'features_completed':False}
    if stage=='generate':return result
    settings=config['alignment']['mfa'];ensure_adoption(root,settings)
    work=root/'data/.cache/dataset'/source_id;work.mkdir(parents=True,exist_ok=True)
    dictionary=work/settings['custom_dictionary'];dictionary.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(root/settings['custom_dictionary'],dictionary)
    body=_body_text((root/'data/transcripts/as_spoken'/f'{source_id}.txt').read_text())
    inference=[]
    for record in records:
        rid=record['recording_id'];path=root/'data/flawed/align16k'/f'{rid}.flac'
        info=sf.info(path);duration=round(info.frames/info.samplerate,3)
        wav=work/'data/audio/align16k'/f'{rid}.wav';wav.parent.mkdir(parents=True,exist_ok=True)
        samples,sr=sf.read(path,dtype='int16')
        identical=False
        if wav.exists():
            previous,previous_sr=sf.read(wav,dtype='int16');identical=previous_sr==sr and np.array_equal(previous,samples)
        if not identical:sf.write(wav,samples,sr,subtype='PCM_16')
        inference.append({'recording_id':rid,'duration_s':duration,'body':body,'uncertain':source.get('uncertain_words',[]),
                          'windows':[{'i':0,'start':0.,'end':duration,'valid':True,'text':body,'char_start':0,'char_end':len(body)}]})
    identity={'settings':settings,'source_alignment_sha256':hashlib.sha256((root/'data/alignment'/f'{source_id}.json').read_bytes()).hexdigest(),
        'transcript_sha256':hashlib.sha256(body.encode()).hexdigest(),
        'audio_hashes':{r['recording_id']:r['artifacts'][f"data/flawed/align16k/{r['recording_id']}.flac"] for r in records},
        'code':{name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ('dataset.py','align/mfa.py','align/base.py','transcripts.py')}}
    pretrained=Path('/home/sriram/Documents/MFA/pretrained_models')
    model_paths=[pretrained/'acoustic'/f"{settings['acoustic_model']}.zip",pretrained/'dictionary'/f"{settings['dictionary']}.dict",pretrained/'g2p'/f"{settings['g2p_model']}.zip"]
    identity['model_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in model_paths}
    state=work/'real_alignment.json';old=json.loads(state.read_text()) if state.exists() else {}
    cached=old.get('inputs')==identity and len(old.get('artifacts',{}))==2*len(records) and all((root/p).exists() and hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in old.get('artifacts',{}).items())
    began=time.monotonic()
    if not cached:
        LOGGER.info('Dataset source %s: real MFA on %d files',source_id,len(inference))
        results=run_mfa(work,inference,settings,isolated=True)
        hashes={}
        for rid,payload in results.items():
            payload=restore_sentences(payload,source);payload.update(audio=f'data/flawed/hq/{rid}.flac',transcript=f'data/transcripts/as_spoken/{source_id}.txt')
            _write_json(root/'data/alignment'/f'{rid}.json',payload);write_textgrid(root/'data/alignment'/f'{rid}.TextGrid',payload)
            for extension in ('json','TextGrid'):
                path=root/'data/alignment'/f'{rid}.{extension}';hashes[str(path.relative_to(root))]=hashlib.sha256(path.read_bytes()).hexdigest()
        _write_json(state,{'inputs':identity,'artifacts':hashes,'runtime_s':round(time.monotonic()-began,3),'device':'cpu','jobs':1})
    result['real_alignment_completed']=True;result['alignment_state']=json.loads(state.read_text())
    if stage=='align':return result
    result['feature_state']=extract_dataset_features(root,records,result['alignment_state']['artifacts'],config['features'],work/'features.json')
    result['features_completed']=True
    return result


def write_dataset_index(root: Path, rows: list[dict], results: list[dict], splits: dict) -> list[dict]:
    """Stable one-row-per-HQ-audio CSV, including prepared sources and generated variants."""
    membership={rid:split for split in ('train','dev','test') for rid in splits[split]};index=[]
    row_map={row['recording_id']:row for row in rows}
    for row in sorted(rows,key=lambda r:r['recording_id']):
        rid=row['recording_id'];path=root/'data/audio/hq'/f'{rid}.wav'
        index.append({'recording_id':rid,'kind':'source','text_id':row['text_id'],'speaker_slug':row['speaker_slug'],
            'split':membership.get(rid,'excluded'),'flaw_types':'','max_severity':0,'duration_s':f"{float(row['duration_s']):.3f}",
            'audio_path':str(path.relative_to(root)),'label_path':'','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    for result in results:
        source=result['source_id'];row=row_map[source]
        for record in result['records']:
            rid=record['recording_id'];path=root/'data/flawed/hq'/f'{rid}.flac';label_path=root/'data/labels'/f'{rid}.json'
            label=json.loads(label_path.read_text());info=sf.info(path)
            index.append({'recording_id':rid,'kind':'synthetic','text_id':row['text_id'],'speaker_slug':row['speaker_slug'],
                'split':membership[source],'flaw_types':';'.join(sorted({f['type'] for f in label['flaws']})),
                'max_severity':max(f['severity'] for f in label['flaws']),'duration_s':f'{info.frames/info.samplerate:.3f}',
                'audio_path':str(path.relative_to(root)),'label_path':str(label_path.relative_to(root)),
                'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    index.sort(key=lambda r:r['recording_id']);path=root/'data/manifest/dataset_index.csv';path.parent.mkdir(parents=True,exist_ok=True)
    fields=['recording_id','kind','text_id','speaker_slug','split','flaw_types','max_severity','duration_s','audio_path','label_path','sha256']
    with path.open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=fields,lineterminator='\n');writer.writeheader();writer.writerows(index)
    return index


def dataset_alignment_qa(root: Path, results: list[dict]) -> dict:
    """Real-vs-oracle boundary errors on affected words, excluding uncertain evidence."""
    groups={};files=0
    for result in results:
        if not result['real_alignment_completed']:continue
        for record in result['records']:
            rid=record['recording_id'];real=json.loads((root/'data/alignment'/f'{rid}.json').read_text())
            oracle=json.loads((root/'data/alignment/oracle'/f'{rid}.json').read_text())
            label=json.loads((root/'data/labels'/f'{rid}.json').read_text());uncertain=set(real.get('uncertain_words',[]));files+=1
            for flaw in label['flaws']:
                values=groups.setdefault(flaw['type'],[])
                for i in range(flaw['word_start'],flaw['word_end']+1):
                    if i in uncertain:continue
                    values.extend(abs(real['words'][i][edge]-oracle['words'][i][edge])*1000 for edge in ('start','end'))
    return {'schema':'dataset_alignment_qa/v1','files_scored':files,'by_type':{
        kind:{'edges':len(values),'median_absolute_error_ms':round(float(np.median(values)),3),
              'p90_absolute_error_ms':round(float(np.quantile(values,.9)),3),'risk_above_60ms':bool(np.median(values)>60)}
        for kind,values in sorted(groups.items()) if values},'limitations':['Oracle agreement is not human boundary accuracy.']}


def dataset_build(stage: str = 'all', limit_sources: int = 0) -> None:
    """Build fixed-speaker source batches with deterministic independent CPU workers."""
    from speecheval.features import features_all
    from speecheval.verify import _write_json
    root=Path.cwd();config=yaml.safe_load((root/'configs/default.yaml').read_text())
    flaws=yaml.safe_load((root/'configs/flaws.yaml').read_text())
    if config['alignment']['primary']!='mfa':raise ValueError('This approved dataset pipeline requires primary MFA')
    features_all();splits=source_splits(root)
    all_ids=sorted(splits['train']+splits['dev']+splits['test']);ids=all_ids
    if limit_sources:ids=ids[:limit_sources]
    workers=config['dataset']['workers']
    if workers<1:raise ValueError('Dataset workers must be positive')
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
    temporary=root/'data/.cache/dataset_tmp';temporary.mkdir(parents=True,exist_ok=True);os.environ['TMPDIR']=str(temporary)
    results=[]
    with ProcessPoolExecutor(max_workers=min(workers,len(ids)),mp_context=multiprocessing.get_context('spawn')) as pool:
        futures={pool.submit(build_source,root,rid,flaws,config,stage):rid for rid in ids}
        for future in as_completed(futures):
            result=future.result();results.append(result)
            _write_json(root/'data/manifest/dataset_shards'/f"{result['source_id']}.json",result)
            LOGGER.info('Dataset completed source %d/%d: %s',len(results),len(ids),result['source_id'])
    results.sort(key=lambda r:r['source_id'])
    rows=list(csv.DictReader((root/'data/manifest/recordings.csv').open()));index=write_dataset_index(root,rows,results,splits)
    skipped=[item for result in results for item in result['skipped']]
    _write_json(root/'data/manifest/dataset_build.json',{'schema':'dataset_build/v1','stage':stage,
        'partial_sources':len(ids)<len(all_ids),'sources':ids,'synthetic_files':sum(r['kind']=='synthetic' for r in index),
        'expected_before_skips':len(ids)*(len(flaws['types'])*5+config['dataset']['mixed_per_source']),
        'skipped':skipped,'real_alignment_completed':all(r['real_alignment_completed'] for r in results),
        'features_completed':all(r['features_completed'] for r in results),'human_recordings':'PENDING'})
    _write_json(root/'data/review/dataset_alignment_qa.json',dataset_alignment_qa(root,results))
    write_dataset_card(root,index,splits,flaws,stage,len(ids)<len(all_ids))
    human_script(root,flaws['seed'])


def human_script(root: Path, seed: int) -> dict:
    """Write exact reading texts and twelve deterministic take instructions, not voice data."""
    from speecheval.verify import sentence_units,_write_json
    directory=root/'data/human';(directory/'scripts').mkdir(parents=True,exist_ok=True);(directory/'raw').mkdir(exist_ok=True)
    lines=['# Recording instructions','',
        'Human recordings, listening and consent are pending. This command does not record or synthesize your voice.',
        'Use a quiet room, the same mic/setup for all takes, about 30 cm from your mouth.',
        'Read the saved text exactly. Note slips in data/human/raw/notes.md.',
        'Explicit voice-publication consent is required before publishing recordings.','']
    takes=[];rng=np.random.default_rng(seed);clip_end=None
    for text_id in ('gettysburg','o_captain','reagan_challenger'):
        body=_body_text((root/'data/transcripts/canonical'/f'{text_id}.txt').read_text())
        units=sentence_units(body,poem=text_id=='o_captain')
        if text_id=='reagan_challenger':
            source=json.loads((root/'data/alignment/reagan_challenger__reagan__orig.json').read_text())
            canonical_tokens=[];ends=[]
            for unit in units:canonical_tokens.extend(normalize_tokens(unit['text']));ends.append(len(canonical_tokens)-1)
            source_tokens=[];owners=[]
            for word in source['words']:
                tokens=word['norm'].split();source_tokens.extend(tokens);owners.extend([word['i']]*len(tokens))
            mapping={}
            for block in difflib.SequenceMatcher(None,canonical_tokens,source_tokens,autojunk=False).get_matching_blocks():
                mapping.update({block.a+i:owners[block.b+i] for i in range(block.size)})
            candidates=[]
            for i,end in enumerate(ends):
                start=ends[i-1]+1 if i else 0;matched=[mapping[k] for k in range(start,end+1) if k in mapping]
                if matched:candidates.append((abs(source['words'][matched[-1]]['end']-90),i,source['words'][matched[-1]]['end']))
            if not candidates:raise ValueError('Cannot locate Reagan canonical excerpt from source words')
            _,last,clip_end=min(candidates);units=units[:max(3,last+1)]
        if len(units)<3:raise ValueError(f'Need three sentence/line units for {text_id}')
        selected=('\n' if text_id=='o_captain' else ' ').join(unit['text'] for unit in units)
        (directory/'scripts'/f'{text_id}.txt').write_text(selected+'\n',encoding='utf-8')
        y=int(rng.integers(len(units)-1));z=y+1;x=int(rng.choice([i for i in range(len(units)) if i not in (y,z)]))
        noun='line' if text_id=='o_captain' else 'sentence'
        lines.extend([f'## {text_id}','',f'Read data/human/scripts/{text_id}.txt.',
            f'X = {noun} {x+1}: {units[x]["text"]}',f'Y = {noun} {y+1}: {units[y]["text"]}',f'Z = {noun} {z+1}: {units[z]["text"]}',''])
        instructions=['Best natural delivery.',
            f'Rush {noun} {x+1}; insert a long pause inside {noun} {y+1}; trail off at the end of {noun} {z+1}.',
            f'Read {noun} {x+1} in a flat monotone; mumble {noun} {y+1}; run {noun}s {y+1} and {z+1} together without a pause.',
            'Mix three flaws of your choice; immediately write which flaws and where in notes.md.']
        for number,instruction in enumerate(instructions,1):
            rid=f'{text_id}__user__take{number:02d}';takes.append({'recording_id':rid,'instruction':instruction,'text':f'data/human/scripts/{text_id}.txt'})
            lines.append(f'- {rid}.wav: {instruction}')
        lines.append('')
    (directory/'RECORDING_SCRIPT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    result={'schema':'human_script/v1','seed':seed,'takes':takes,'audio_recorded':False,'reagan_source_excerpt_end_s':clip_end,'publication_consent':'PENDING'}
    _write_json(directory/'script.json',result);return result


def write_dataset_card(root: Path, index: list[dict], splits: dict, flaws: dict, stage: str, partial: bool) -> None:
    """Write the required dataset card from observed composition and supplied license metadata."""
    from collections import Counter
    sources=yaml.safe_load((root/'data/manifest/sources.yaml').read_text())
    lines=['# Speech-eval dataset card','',
        f'Status: {"partial-source smoke run" if partial else "all eligible sources"}, stage `{stage}`. Human takes, consent and labels are PENDING; Dataset v1 is not fully accepted or tagged.',
        '', '## Purpose and contrastive design','',
        'English speech delivery, not content quality. Same-text clean and synthetically flawed recordings support graded, temporally grounded comparisons.','',
        '## Sources and supplied license evidence','',
        '| Source | License metadata | Evidence |','|---|---|---|']
    for source in sources['sources']:
        lines.append(f"| {source['id']} | {str(source.get('license','unspecified')).replace('|','/')} | {source.get('license_evidence',source.get('page',''))} |")
    lines.extend(['','## Construction','',
        'Source audio remains untouched. Prepared mono PCM16 HQ audio is 44.1 kHz, with 16 kHz alignment copies. Source excerpts and transcripts retain Phase 1 provenance. Feature normalisation never changes stored audio.',
        'Injection sites are seeded contiguous 4–12-word within-sentence regions or eligible boundaries, with one-second edge keep-outs. Unknown words are excluded from required evidence. Two mixed files per source contain three distinct effects separated by at least two seconds when eligible sites exist.',
        'Tempo uses Rubber Band fine mode; pitch-range compression uses Praat PSOLA; quietness uses gain envelopes; pauses use looped room tone or central removal with a 30 ms minimum; muffling uses a zero-phase fourth-order Butterworth filter plus gain. Crossfades and common HQ/16 kHz peak attenuation are recorded.',
        'Oracle timestamps use monotone piecewise-linear source-to-flawed maps. The detector MUST use separately computed real MFA alignments and their features. Full-utterance MFA inference uses transcripts, not oracle boundaries. Sentence membership is recovered from text word indices.',
        '', '| Type | Parameter | Severities 1–5 |','|---|---|---|'])
    for kind,spec in flaws['types'].items():lines.append(f"| {kind} | {spec['param']} | {spec['severity']} |")
    lines.extend(['','## Labels','',
        '`labels/v1` stores recording/reference/text IDs, source=synthetic, and flaw type, severity, flawed-timeline start/end, inclusive word bounds and exact parameters. Mixed files contain three flaw entries. Human labels will be explicitly source=human and must not be inferred from intended instructions.',
        '', '## Splits and evaluation','',
        f"Sources: {len(splits['train'])} train, {len(splits['dev'])} dev, {len(splits['test'])} test. Speaker membership is frozen in configs/splits.yaml. Excluded: {splits['excluded']}.",
        'A-LOSO compares Gettysburg/O Captain against other train readers, excluding the source speaker. B-same-speaker uses original JFK/Reagan recordings. C uses good-speaker norms without same-text reference. Test speakers never calibrate thresholds or reference statistics. Human evaluation is pending.',
        '', '## Observed composition','',
        f"{len(index)} HQ audio files, {sum(r['kind']=='synthetic' for r in index)} synthetic; {sum(float(r['duration_s']) for r in index)/3600:.3f} hours (16 kHz copies are not double-counted).",
        '', '| Text | Split | Kind | Files |','|---|---|---|---:|'])
    counts=Counter((r['text_id'],r['split'],r['kind']) for r in index)
    for key,count in sorted(counts.items()):lines.append('| '+' | '.join(key)+f' | {count} |')
    counts=Counter()
    for row in index:
        if row['kind']=='synthetic':
            label=json.loads((root/row['label_path']).read_text())
            for flaw in label['flaws']:counts[(row['text_id'],row['split'],flaw['type'],flaw['severity'])]+=1
    lines.extend(['','| Text | Split | Type | Severity | Events |','|---|---|---|---:|---:|'])
    for key,count in sorted(counts.items()):lines.append('| '+' | '.join(map(str,key))+f' | {count} |')
    lines.extend(['','## Known limitations and attributions','',
        'Synthetic parameter fidelity does not establish perceptual realism. LibriVox reading differs from oratory. English only. Human takes/ratings are missing. Gold boundaries were marked visually by Claude, without listening; the human spot-check is pending and neither aligner met the Phase 1 gold accuracy target. Uncertain word evidence is excluded. Real-vs-oracle errors and >60 ms risks are saved in data/review/dataset_alignment_qa.json.',
        'Required source attributions: LibriVox, US government works and Internet Archive, with evidence links above. User voice must not be published without explicit consent.'])
    (root/'docs').mkdir(exist_ok=True);(root/'docs/DATASET.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
