"""Deterministic participant preparation and real-alignment delivery analysis."""
from __future__ import annotations
import hashlib
import importlib.metadata
import json
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml

LOGGER=logging.getLogger(__name__)


def participant_code_identity(code_dir: Path | None = None) -> dict:
    """Bind preparation, alignment, feature producers and pinned runtime versions."""
    base=code_dir or Path(__file__).parent
    return {'code':{name:hashlib.sha256((base/name).read_bytes()).hexdigest() for name in ('pipeline.py','features.py','transcripts.py','align/mfa.py','align/base.py')},
            'versions':{name:importlib.metadata.version(name) for name in ('torch','torchaudio','whisperx','ctranslate2','numpy','scipy','praat-parselmouth','librosa','pyarrow','praatio','cmudict')}}


def participant_model_identity(root: Path, settings: dict, include_asr: bool) -> dict:
    """Stream model/dictionary SHA256 checks without loading checkpoints into RAM."""
    mfa=settings['alignment']['mfa'];pretrained=Path('/home/sriram/Documents/MFA/pretrained_models')
    paths=[pretrained/'acoustic'/f"{mfa['acoustic_model']}.zip",pretrained/'dictionary'/f"{mfa['dictionary']}.dict",pretrained/'g2p'/f"{mfa['g2p_model']}.zip",root/mfa['custom_dictionary']]
    if include_asr:
        base=root/'data/.cache/whisperx'/f"models--Systran--faster-whisper-{settings['asr']['model']}"
        revision=(base/'refs/main').read_text().strip();snapshot=base/'snapshots'/revision
        paths.extend(sorted(snapshot.glob('*')))
    result={}
    for path in paths:
        if path.is_file():
            with path.open('rb') as stream:result[str(path)]=hashlib.file_digest(stream,'sha256').hexdigest()
        else:raise FileNotFoundError(f'Installed inference artifact missing: {path}')
    return result


def energy_bounds(wave: np.ndarray, sr: int, padding_s: float = .25) -> tuple[float,float]:
    """Trim by 10 ms RMS, loudest-half median minus 25 dB, sustained at least 100 ms."""
    if wave.ndim!=1 or not len(wave) or np.max(np.abs(wave))==0:raise ValueError('No sustained speech energy')
    width=round(sr*.01);n=int(np.ceil(len(wave)/width))
    padded=np.pad(wave,(0,n*width-len(wave))).reshape(n,width)
    rms=np.sqrt(np.mean(padded*padded,axis=1));db=20*np.log10(np.maximum(rms,1e-12))
    upper=np.sort(db)[len(db)//2:];active=db>np.median(upper)-25
    changes=np.diff(np.r_[False,active,False].astype(int));starts=np.where(changes==1)[0];ends=np.where(changes==-1)[0]
    sustained=[(a,b) for a,b in zip(starts,ends) if b-a>=10]
    if not sustained:raise ValueError('No sustained speech energy')
    return max(0.,sustained[0][0]*.01-padding_s),min(len(wave)/sr,sustained[-1][1]*.01+padding_s)


def prepare_participant(audio: Path, text_id: str, root: Path, transcript: Path | None = None) -> tuple[str,str]:
    """Reuse hash-matching stored audio; otherwise decode, energy-trim, real-MFA and feature-extract."""
    from speecheval.reference import recording_values
    candidate=root/'data/alignment'/f'{audio.stem}.json'
    if transcript is None and candidate.exists():
        saved=json.loads(candidate.read_text());stored=root/saved['audio']
        if stored.exists() and hashlib.sha256(stored.read_bytes()).digest()==hashlib.sha256(audio.read_bytes()).digest():
            if audio.stem.split('__')[0]!=text_id:raise ValueError('Stored recording belongs to another text')
            recording_values(root,audio.stem)
            return audio.stem,'stored_as_spoken'
    from speecheval.align.mfa import run_mfa,ensure_adoption
    from speecheval.align.base import write_textgrid
    from speecheval.features import extract_features
    from speecheval.transcripts import _body_text
    from speecheval.verify import _write_json,sentence_units
    cfg=yaml.safe_load((root/'configs/default.yaml').read_text());settings=cfg['alignment']['mfa'];ensure_adoption(root,settings)
    if cfg['alignment']['primary']!='mfa':raise ValueError('Participant pipeline currently requires promoted MFA')
    if not re.fullmatch('[a-z][a-z0-9_]*',text_id):raise ValueError('Invalid text ID')
    transcript_bytes=transcript.read_bytes() if transcript else b'automatic_as_read_configured_whisperx_gpu_preferred'
    identity={'audio_sha256':hashlib.sha256(audio.read_bytes()).hexdigest(),'text_id':text_id,
              'transcript_sha256':hashlib.sha256(transcript_bytes).hexdigest(),'settings':cfg,
              'producer':participant_code_identity(),'models':participant_model_identity(root,cfg,transcript is None)}
    digest=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest();rid=f'{text_id}__user__input_{digest[:12]}'
    work=root/'data/.cache/participants'/digest;work.mkdir(parents=True,exist_ok=True)
    state=work/'state.json'
    if state.exists():
        previous=json.loads(state.read_text())
        if previous['inputs']==identity and all((root/p).exists() and hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in previous['artifacts'].items()):return rid,previous['transcript_source']
    decoded=work/'decoded.wav'
    subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-i',str(audio),'-vn','-ac','1','-ar','44100','-c:a','pcm_s16le',str(decoded)],check=True)
    wave,sr=sf.read(decoded);start,end=energy_bounds(wave,sr,cfg['audio']['trim_padding_s'])
    trimmed=wave[round(start*sr):round(end*sr)];hq=root/'data/audio/hq'/f'{rid}.flac';hq.parent.mkdir(parents=True,exist_ok=True);sf.write(hq,trimmed,sr,subtype='PCM_16')
    align=work/'data/audio/align16k'/f'{rid}.wav';align.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y','-i',str(hq),'-ar','16000','-c:a','pcm_s16le',str(align)],check=True)
    if transcript:
        body=_body_text(transcript.read_text());source='supplied'
    else:
        body=participant_asr(hq,root,cfg['asr']);source='automatic_as_read'
        if not body.strip():raise ValueError('ASR returned no participant words; supply --transcript')
    target=root/'data/transcripts/as_spoken'/f'{rid}.txt';target.parent.mkdir(parents=True,exist_ok=True);target.write_text(body+'\n')
    dictionary=work/settings['custom_dictionary'];dictionary.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/settings['custom_dictionary'],dictionary)
    duration=round(len(trimmed)/sr,3)
    recording={'recording_id':rid,'duration_s':duration,'body':body,'uncertain':[],
               'windows':[{'i':0,'start':0.,'end':duration,'valid':True,'text':body,'char_start':0,'char_end':len(body)}]}
    result=run_mfa(work,[recording],settings,isolated=True)[rid]
    units=sentence_units(body,text_id=='o_captain')
    from speecheval.align.base import transcript_words
    for word,(_,a,b) in zip(result['words'],transcript_words(body)):
        word['sentence']=next((i for i,u in enumerate(units) if u['char_start']<=a<u['char_end']),0)
    result['sentences']=[]
    for i in sorted({w['sentence'] for w in result['words']}):
        selected=[w for w in result['words'] if w['sentence']==i]
        result['sentences'].append({'i':i,'start':selected[0]['start'],'end':selected[-1]['end'],'word_start':selected[0]['i'],'word_end':selected[-1]['i']})
    result.update(audio=str(hq.relative_to(root)),transcript=str(target.relative_to(root)))
    if source=='automatic_as_read':result['warnings'].append({'type':'automatic_transcript_unreviewed'})
    path=root/'data/alignment'/f'{rid}.json';_write_json(path,result);write_textgrid(path.with_suffix('.TextGrid'),result)
    hashes=extract_features(root,hq,result,cfg['features'])
    for file in [hq,path,path.with_suffix('.TextGrid'),target]:hashes[str(file.relative_to(root))]=hashlib.sha256(file.read_bytes()).hexdigest()
    _write_json(state,{'inputs':identity,'artifacts':hashes,'transcript_source':source,'trim_start_s':round(start,3),'trim_end_s':round(end,3)})
    return rid,source


def participant_asr(audio: Path, root: Path, settings: dict) -> str:
    """Use the visible GPU for ASR, unlike CPU-only MFA; beam/temperature are fixed."""
    import torch
    from speecheval.prepare import _import_whisperx
    cache=root/'data/.cache';os.environ['HF_HOME']=str(cache/'huggingface');os.environ['TORCH_HOME']=str(cache/'torch')
    device='cuda' if torch.cuda.is_available() else 'cpu'
    LOGGER.info('Participant ASR on %s; MFA and Praat remain CPU-only',device)
    whisperx=_import_whisperx()
    model=whisperx.load_model(settings['model'],device,compute_type=settings['compute_type'] if device=='cuda' else 'int8',
                             language=settings['language'],asr_options={'beam_size':settings['beam_size'],'temperatures':[settings['temperature']]},
                             vad_method='silero',download_root=str(cache/'whisperx'),threads=1)
    result=model.transcribe(str(audio),batch_size=1,language=settings['language'])
    text=' '.join(segment['text'].strip() for segment in result.get('segments',[]))
    del model
    if device=='cuda':torch.cuda.empty_cache()
    return text


def rounded(value):
    """Four significant digits for evidence; non-finite evidence must never reach JSON."""
    if isinstance(value,float):return float(f'{value:.4g}') if np.isfinite(value) else None
    if isinstance(value,dict):return {k:rounded(v) for k,v in value.items()}
    if isinstance(value,list):return [rounded(v) for v in value]
    return value


def analyze(audio: Path, text_id: str, mode: str = 'A', transcript: Path | None = None,
            exclude_speaker: str | None = None, previous: Path | None = None, plot: bool = False,
            root: Path | None = None) -> dict:
    """Analyze delivery in participant seconds; no gold/oracle data enters the scoring path."""
    from speecheval.reference import build_reference,recording_values,map_words
    from speecheval.detect import z_table,detect
    from speecheval.explain import explanation
    from speecheval.verify import _write_json
    root=root or Path.cwd();audio=audio.resolve()
    if mode not in ('A','B'):raise ValueError('Supported modes are A and B')
    if mode=='B' and previous is None:raise ValueError('Mode B requires --previous')
    rid,source=prepare_participant(audio,text_id,root,transcript)
    previous_id=prepare_participant(previous.resolve(),text_id,root)[0] if previous else None
    reference=build_reference(text_id,exclude_speaker,root,previous_id if mode=='B' else None)
    alignment,values=recording_values(root,rid)
    mapping=map_words([w['norm'] for w in alignment['words']],reference['words'])
    rows=z_table(alignment,values,reference,mapping)
    settings_path=root/'configs/detector.yaml';settings=yaml.safe_load(settings_path.read_text())
    if settings['engine']!='rules':raise ValueError('Only rules engine is implemented at this stage')
    config_hash=hashlib.sha256(settings_path.read_bytes()).hexdigest()
    regions=detect(rows,alignment['duration_s'],settings)
    number_words=set('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion'.split())
    words=alignment['words'];sentences=alignment['sentences']
    for region in regions:
        selected=words[region['word_start']:region['word_end']+1]
        tags=[]
        if any(w['sentence']==sentences[0]['i'] for w in selected):tags.append('first_sentence')
        if any(w['sentence']==sentences[-1]['i'] for w in selected):tags.append('final_sentence')
        if any(region['word_end']==s['word_end'] for s in sentences):tags.append('sentence_final')
        if any(set(w['norm'].split())&number_words for w in selected):tags.append('contains_number')
        region['tags']=tags;region['explanation']=explanation(region,[w['text'] for w in words],mode)
        region['evidence']=rounded(region['evidence'])
    # Bind actual measured alignment/features as well as the specified identity fields:
    # alternate as-read transcripts must not collide for identical input audio.
    measured=json.dumps({'alignment':alignment,'values':rounded(values),'code':{name:hashlib.sha256((Path(__file__).parent/name).read_bytes()).hexdigest() for name in ('pipeline.py','detect.py','explain.py')}},sort_keys=True).encode()
    analysis_id=hashlib.sha256(audio.read_bytes()+mode.encode()+reference['reference_version'].encode()+config_hash.encode()+measured).hexdigest()[:12]
    baselines=yaml.safe_load((root/'configs/baselines.yaml').read_text()) if (root/'configs/baselines.yaml').exists() else {}
    result={'schema':'analysis/v1','analysis_id':analysis_id,'recording_id':rid,'text_id':text_id,'mode':mode,
            'reference':{'kind':'previous_take' if mode=='B' else 'distribution','text_id':text_id,'exclude_speaker':exclude_speaker,
                         'n_readers':reference['n_readers'],'reference_version':reference['reference_version'],
                         'baseline_recording_id':previous_id if mode=='B' else baselines.get(text_id)},
            'transcript_source':source,'detector':{'engine':'rules','config_hash':config_hash},
            'duration_s':alignment['duration_s'],'regions':regions,'key_moments':[],'scores':{},'progress':None,
            'warnings':alignment['warnings']+[{'type':'unmatched_reference_words','count':mapping.count(None)}]}
    if mode=='B':
        from speecheval.detect import TYPES
        old=analyze(previous,text_id,root=root,exclude_speaker=exclude_speaker)
        current=analyze(audio,text_id,root=root,transcript=transcript,exclude_speaker=exclude_speaker)
        result['progress']={}
        for kind in list(TYPES)+['awkward_pause','missing_pause']:
            def summary(payload):
                found=[r for r in payload['regions'] if r['type']==kind]
                return {'count':len(found),'duration_s':round(sum(r['end']-r['start'] for r in found),3)}
            result['progress'][kind]={'previous':summary(old),'current':summary(current)}
    _write_json(root/'data/analyses'/f'{analysis_id}.json',result)
    if plot:plot_analysis(root,result,alignment,rows,reference)
    LOGGER.info('Analysis %s: %s, %d regions',analysis_id,rid,len(regions))
    return result


def plot_analysis(root: Path, result: dict, alignment: dict, rows: list[dict], reference: dict) -> None:
    """Waveform plus physical-unit tracks/reference bands and detected regions."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from speecheval.reference import inverse
    wave,sr=sf.read(root/alignment['audio']);fig,axes=plt.subplots(4,1,figsize=(13,10))
    axes[0].plot(np.arange(len(wave))/sr,wave,lw=.3)
    for region in result['regions']:axes[0].axvspan(region['start'],region['end'],alpha=.2,label=region['type'])
    axes[0].set(xlabel='Participant time (s)',ylabel='Amplitude',title=result['recording_id'])
    for axis,feature in zip(axes[1:],('rate','pitchvar','loud')):
        participant=[];centres=[];lower=[];upper=[]
        for row in rows:
            participant.append(inverse(feature,row['values'][feature]))
            summary=reference['features'].get(str(row['ref_i']),{}).get(feature) if row['ref_i'] is not None else None
            if summary:
                centres.append(inverse(feature,summary['mu']));lower.append(inverse(feature,summary['mu']-2*summary['sigma']));upper.append(inverse(feature,summary['mu']+2*summary['sigma']))
            else:centres.append(np.nan);lower.append(np.nan);upper.append(np.nan)
        axis.plot(participant,label='participant');axis.plot(centres,label='reference');axis.fill_between(np.arange(len(rows)),lower,upper,alpha=.2)
        axis.set(xlabel='Participant word index',ylabel=feature);axis.legend()
    fig.text(.01,.005,'; '.join(f"{r['type']} {r['start']:.1f}–{r['end']:.1f}s" for r in result['regions'])[:250],fontsize=8)
    fig.tight_layout();path=root/'reports/img'/f"{result['analysis_id']}.png";path.parent.mkdir(parents=True,exist_ok=True);fig.savefig(path,dpi=130);plt.close(fig)
