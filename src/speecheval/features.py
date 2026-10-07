"""Acoustic feature extraction."""
from __future__ import annotations
import csv
import hashlib
import importlib.metadata
import json
import logging
import os
import re
from pathlib import Path
from functools import lru_cache
import numpy as np
import pandas as pd
import parselmouth
from parselmouth.praat import call
import soundfile as sf
import yaml
from speecheval.align.base import Alignment
from speecheval.verify import _write_json

os.environ.setdefault('NUMBA_CACHE_DIR',str(Path.cwd()/'data/.cache/numba'))
LOGGER=logging.getLogger(__name__)


def octave_jumps(frames: pd.DataFrame) -> int:
    """Count octave-like Hz jumps only between adjacent voiced 10 ms frames."""
    hz=frames.f0_hz.to_numpy();voiced=frames.voiced.to_numpy()
    with np.errstate(divide='ignore',invalid='ignore'):
        ratios=hz[1:]/hz[:-1]
    return int(np.count_nonzero(voiced[1:] & voiced[:-1] & ((ratios>1.8)|(ratios<.55))))


def features_qa() -> None:
    """Save QA data and a pitch-normalised Gettysburg overlay without prose reports."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    root=Path.cwd();base=root/'data/features';rows=[]
    for path in sorted((base/'speaker_stats').glob('*.json')):
        stats=json.loads(path.read_text());rid=stats['recording_id']
        frames=pd.read_parquet(base/'frames'/f'{rid}.parquet')
        jumps=octave_jumps(frames);rate=jumps/max(1,int(frames.voiced.sum()))
        median=stats['f0_median_hz']
        rows.append({**stats,'octave_jumps':jumps,'octave_jump_rate':rate,
                     'flagged':rate>.01 or median is None or not 70<=median<=300})
    _write_json(base/'qa.json',{'schema':'features_qa/v1','recordings':rows,
                              'proposed_flag_fix':'Inspect pitch tracks, then try pitch_ceiling_q3_factor=2.0; do not silently repair audio.',
                              'human_overlay_review':'waived','docker':'deferred to Phase 9'})
    candidates=sorted([r for r in rows if r['recording_id'].startswith('gettysburg__') and r['f0_median_hz']],key=lambda r:r['f0_median_hz'])
    if len(candidates)<2:raise ValueError('Two Gettysburg readers are required for the overlay')
    fig,axes=plt.subplots(3,1,figsize=(14,9),sharex=True)
    for stats in (candidates[0],candidates[-1]):
        rid=stats['recording_id'];words=pd.read_parquet(base/'words'/f'{rid}.parquet')
        label=f"{rid} ({stats['f0_median_hz']} Hz)"
        for ax,col in zip(axes,('f0_st_median','int_rel_db_mean','log_dur_per_syl')):
            ax.plot(words.i,words[col],label=label,alpha=.8,lw=.8)
            for boundary in words.loc[words.sentence.ne(words.sentence.shift()),'i']:
                ax.axvline(boundary,color='grey',alpha=.15)
            ax.set_ylabel(col);ax.grid(alpha=.15)
    axes[0].legend(fontsize=8);axes[-1].set_xlabel('As-spoken word index (reader texts can differ)')
    fig.suptitle('Gettysburg: shared semitone/dB scales, not identical delivery curves')
    fig.tight_layout();output=root/'reports/img/phase02_gettysburg_overlay.png';output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(output,dpi=120,metadata={'Software':'speech-eval'});plt.close(fig)
    LOGGER.info('Feature QA: %d recordings, %d flagged',len(rows),sum(r['flagged'] for r in rows))


def semitones(f0: np.ndarray, median: float) -> np.ndarray:
    """Semitones relative to speaker median Hz; invalid pitch stays NaN."""
    return 12*np.log2(np.asarray(f0)/median) if median and median>0 else np.full(len(f0),np.nan)


def frame_tracks(signal: np.ndarray, sr: int, ceiling_factor: float) -> tuple[pd.DataFrame,dict]:
    """Shared 10 ms centre grid, two-pass Praat F0, intensity/HNR and STFT/MFCC tracks."""
    import librosa
    y=np.asarray(signal,dtype=float);sound=parselmouth.Sound(y,sampling_frequency=sr)
    hop=round(sr*.01);window=round(sr*.025);nfft=2**int(np.ceil(np.log2(window)))
    spec=librosa.stft(y,n_fft=nfft,hop_length=hop,win_length=window,window='hann',center=True)
    power=np.abs(spec)**2;times=np.arange(power.shape[1])*hop/sr
    first=sound.to_pitch_ac(time_step=.01,pitch_floor=60,pitch_ceiling=600)
    valid=first.selected_array['frequency'];valid=valid[valid>0]
    q1,q3=np.quantile(valid,[.25,.75]) if len(valid) else (80.,400.)
    floor=max(30.,float(.75*q1));ceiling=max(floor*1.1,float(ceiling_factor*q3))
    pitch=sound.to_pitch_ac(time_step=.01,pitch_floor=floor,pitch_ceiling=ceiling)
    frequency=pitch.selected_array['frequency'].copy();frequency[frequency<=0]=np.nan
    f0=np.interp(times,pitch.xs(),frequency,left=np.nan,right=np.nan)
    intensity=sound.to_intensity(minimum_pitch=75,time_step=.01)
    harmonic=sound.to_harmonicity_cc(time_step=.01,minimum_pitch=75)
    hnr=harmonic.values[0].copy();hnr[hnr<=-199]=np.nan
    intens=np.interp(times,intensity.xs(),intensity.values[0],left=np.nan,right=np.nan)
    hnr=np.interp(times,harmonic.xs(),hnr,left=np.nan,right=np.nan)
    hz=librosa.fft_frequencies(sr=sr,n_fft=nfft)
    lo=power[(hz>=0)&(hz<2000)].sum(axis=0);hi=power[(hz>=2000)&(hz<=6000)].sum(axis=0)
    with np.errstate(divide='ignore',invalid='ignore'):
        hiband=10*np.log10(hi/lo)
        centroid=(np.abs(spec)*hz[:,None]).sum(axis=0)/np.abs(spec).sum(axis=0)
    hiband[~np.isfinite(hiband)]=np.nan;centroid[~np.isfinite(centroid)]=np.nan
    mel=librosa.feature.melspectrogram(S=power,sr=sr,n_fft=nfft,n_mels=40)
    mfcc=librosa.feature.mfcc(S=librosa.power_to_db(mel),n_mfcc=13)
    data={'t':times,'f0_hz':f0,'voiced':np.isfinite(f0),'intensity_db':intens,'hnr_db':hnr,
          'centroid_hz':centroid,'hiband_ratio_db':hiband}
    data.update({f'mfcc_{k+1}':mfcc[k] for k in range(13)})
    return pd.DataFrame(data),{'pitch_floor_hz':floor,'pitch_ceiling_hz':ceiling}


@lru_cache(maxsize=1)
def pronunciation_dictionary() -> dict:
    import cmudict
    return cmudict.dict()


def syllables(norm: str) -> int:
    """CMU first-pronunciation vowel phones, else vowel groups, minimum one per token."""
    count=0
    for word in norm.lower().split():
        pronunciations=pronunciation_dictionary().get(word)
        count+=sum(p[-1:] in '012' for p in pronunciations[0]) if pronunciations else max(1,len(re.findall('[aeiouy]+',word)))
    return max(1,count)


def window_rate(words: pd.DataFrame, pause_threshold: float) -> float:
    """Syllables/second excluding only internal pauses above the configured threshold."""
    if words.empty:return float('nan')
    if 'uncertain' in words and words.uncertain.any():return float('nan')
    if (words.end<=words.start).any():return float('nan')
    gaps=words.start.to_numpy()[1:]-words.end.to_numpy()[:-1]
    duration=float(words.end.iloc[-1]-words.start.iloc[0]-gaps[gaps>pause_threshold].sum())
    return float(words.syllables.sum()/duration) if duration>0 else float('nan')


def finite_reduce(values: np.ndarray, kind: str) -> float:
    """NaN-safe acoustic aggregate; absent evidence remains NaN, never an invented zero."""
    v=np.asarray(values);v=v[np.isfinite(v)]
    if not len(v):return float('nan')
    if kind=='range':return float(np.quantile(v,.9)-np.quantile(v,.1))
    return float({'median':np.median,'mean':np.mean,'max':np.max,'std':np.std}[kind](v))


def write_parquet(path: Path, table: pd.DataFrame) -> None:
    """Deterministic pinned PyArrow Parquet; times 1 ms, floats four significant digits."""
    result=table.copy()
    for col in result.select_dtypes(include='floating'):
        if col in ('t','start','end','dur_s','pause_before_s','pause_after_s'):
            result[col]=result[col].round(3)
        else:result[col]=result[col].map(lambda x:float(f'{x:.4g}') if np.isfinite(x) else np.nan)
    path.parent.mkdir(parents=True,exist_ok=True)
    result.to_parquet(path,index=False,engine='pyarrow',compression='zstd')


def aggregate_features(frames: pd.DataFrame, alignment: dict, ranges: dict, pause_threshold: float) -> tuple[pd.DataFrame,pd.DataFrame,pd.DataFrame,dict]:
    """Word/window/sentence tracks and speaker stats; uncertainty invalidates aggregates."""
    source=pd.DataFrame(alignment['words']);uncertain=set(alignment.get('uncertain_words',[]))
    source['uncertain']=source.i.isin(uncertain);source['syllables']=source.norm.map(syllables)
    source['dur_s']=source.end-source.start
    eligible=np.zeros(len(frames),dtype=bool)
    for word in source.itertuples():
        if not word.uncertain:eligible|=(frames.t.to_numpy()>=word.start)&(frames.t.to_numpy()<word.end)
    voiced=eligible & frames.voiced.to_numpy()
    f0=frames.loc[voiced,'f0_hz'].to_numpy();intens=frames.loc[voiced,'intensity_db'].to_numpy()
    median=finite_reduce(f0,'median');imed=finite_reduce(intens,'median')
    tracks=frames.copy();tracks['f0_st']=semitones(tracks.f0_hz.to_numpy(),median)
    tracks['int_rel_db']=tracks.intensity_db-imed
    word_rows=[]
    for word in source.itertuples():
        row={k:getattr(word,k) for k in ('i','norm','sentence','start','end','dur_s','syllables','uncertain')}
        sub=tracks[(tracks.t>=word.start)&(tracks.t<word.end)]
        vox=sub[sub.voiced];pitch=vox.f0_st.to_numpy()
        row['log_dur_per_syl']=float(np.log(word.dur_s/word.syllables)) if word.dur_s>0 else float('nan')
        row['pause_before_s']=max(0.,word.start-source.end.iloc[word.i-1]) if word.i else 0.
        row['pause_after_s']=max(0.,source.start.iloc[word.i+1]-word.end) if word.i+1<len(source) else 0.
        if word.uncertain or (word.i and source.uncertain.iloc[word.i-1]):row['pause_before_s']=np.nan
        if word.uncertain or (word.i+1<len(source) and source.uncertain.iloc[word.i+1]):row['pause_after_s']=np.nan
        row.update(f0_st_median=finite_reduce(pitch,'median') if len(pitch)>=3 else np.nan,
                   f0_st_range=finite_reduce(pitch,'range') if len(pitch)>=3 else np.nan,
                   hnr_db_mean=finite_reduce(vox.hnr_db.to_numpy(),'mean'),
                   voiced_frac=float(sub.voiced.mean()) if len(sub) else np.nan)
        for col,kind,name in [('int_rel_db','mean','int_rel_db_mean'),('int_rel_db','max','int_rel_db_max'),
                               ('hiband_ratio_db','mean','hiband_ratio_db_mean'),('centroid_hz','mean','centroid_hz_mean')]:
            row[name]=finite_reduce(sub[col].to_numpy(),kind)
        row.update({f'mfcc_{k}_mean':finite_reduce(sub[f'mfcc_{k}'].to_numpy(),'mean') for k in range(1,14)})
        if word.uncertain:
            for key in list(row):
                if key not in ('i','norm','sentence','start','end','dur_s','syllables','uncertain','pause_before_s','pause_after_s'):row[key]=np.nan
        word_rows.append(row)
    words=pd.DataFrame(word_rows);windows=[];sentences=[]
    for word in source.itertuples():
        subset=source[(source.i>=word.i-1)&(source.i<=word.i+1)&(source.sentence==word.sentence)]
        sub=tracks[(tracks.t>=subset.start.iloc[0])&(tracks.t<subset.end.iloc[-1])]
        invalid=bool(subset.uncertain.any() or (subset.dur_s<=0).any())
        windows.append({'i':word.i,'uncertain':bool(subset.uncertain.any()),'invalid_evidence':invalid,'rate_syl_s':window_rate(subset,pause_threshold),
            'f0_st_std':finite_reduce(sub.loc[sub.voiced,'f0_st'].to_numpy(),'std') if not invalid else np.nan,
            'int_rel_db_mean':finite_reduce(sub.int_rel_db.to_numpy(),'mean') if not invalid else np.nan,
            'hiband_ratio_db_mean':finite_reduce(sub.hiband_ratio_db.to_numpy(),'mean') if not invalid else np.nan})
    for sentence in alignment['sentences']:
        subset=source[(source.i>=sentence['word_start'])&(source.i<=sentence['word_end'])]
        start,end=subset.start.iloc[0],subset.end.iloc[-1]
        sub=tracks[(tracks.t>=start)&(tracks.t<end)];vox=sub[sub.voiced]
        last=subset.tail(2);tail=tracks[(tracks.t>=last.start.iloc[0])&(tracks.t<end)&tracks.voiced]
        slope=float(np.polyfit(tail.t.to_numpy(),tail.f0_st.to_numpy(),1)[0]) if len(tail)>=3 else np.nan
        final=tracks[(tracks.t>=subset.start.iloc[-1])&(tracks.t<end)]
        has_number=bool(set('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion'.split()) & set(' '.join(subset.norm).split()))
        invalid=bool(subset.uncertain.any() or (subset.dur_s<=0).any())
        row={'i':sentence['i'],'start':start,'end':end,'uncertain':bool(subset.uncertain.any()),'invalid_evidence':invalid,
             'articulation_rate_syl_s':window_rate(subset,pause_threshold),
             'speech_rate_syl_s':float(subset.syllables.sum()/(end-start)) if end>start else np.nan,
             'f0_st_range':finite_reduce(vox.f0_st.to_numpy(),'range'),'final_pitch_slope_st_s':slope,
             'final_int_drop_db':finite_reduce(final.int_rel_db.to_numpy(),'mean')-finite_reduce(sub.int_rel_db.to_numpy(),'mean'),
             'pause_after_s':max(0.,source.start.iloc[subset.i.iloc[-1]+1]-end) if subset.i.iloc[-1]+1<len(source) else 0.,
             'n_words':len(subset),'n_syllables':int(subset.syllables.sum()),'has_number':has_number}
        if invalid:
            for key in ('articulation_rate_syl_s','speech_rate_syl_s','f0_st_range','final_pitch_slope_st_s','final_int_drop_db','n_syllables'):row[key]=np.nan
        last_i=int(subset.i.iloc[-1])
        if source.uncertain.iloc[last_i] or (last_i+1<len(source) and source.uncertain.iloc[last_i+1]):row['pause_after_s']=np.nan
        sentences.append(row)
    sentence_table=pd.DataFrame(sentences)
    valid_sentences=sentence_table[~sentence_table.invalid_evidence & np.isfinite(sentence_table.articulation_rate_syl_s) & (sentence_table.articulation_rate_syl_s>0)]
    count=float(valid_sentences.n_syllables.sum())
    speaking=float((valid_sentences.n_syllables/valid_sentences.articulation_rate_syl_s).sum())
    stats={'schema':'speaker_stats/v1','recording_id':alignment['recording_id'],
           'f0_median_hz':median,'f0_q1_hz':float(np.quantile(f0,.25)) if len(f0) else np.nan,
           'f0_q3_hz':float(np.quantile(f0,.75)) if len(f0) else np.nan,'intensity_median_db':imed,
           'articulation_rate_syl_s':count/speaking if speaking>0 else np.nan,
           'voiced_fraction':float(voiced.sum()/eligible.sum()) if eligible.any() else 0.,**ranges,
           'uncertain_words_excluded':len(uncertain)}
    stats={k:float(f'{v:.4g}') if isinstance(v,(float,np.floating)) and np.isfinite(v) else (None if isinstance(v,(float,np.floating)) else v) for k,v in stats.items()}
    return words,pd.DataFrame(windows),sentence_table,stats


def extract_features(root: Path, audio: Path, alignment: dict, settings: dict) -> dict[str,str]:
    """Extract a full feature bundle for any real alignment, including synthetic FLAC."""
    Alignment.model_validate(alignment)
    y,sr=sf.read(audio,dtype='float64')
    if sr!=44100 or y.ndim!=1:raise ValueError('Features require 44.1 kHz mono HQ audio')
    rid=alignment['recording_id'];base=root/'data/features'
    frames,ranges=frame_tracks(y,sr,settings['pitch_ceiling_q3_factor'])
    words,windows,sentences,stats=aggregate_features(frames,alignment,ranges,settings['pause_threshold_s'])
    paths=[base/folder/f'{rid}.parquet' for folder in ('frames','words','windows','sentences')]+[base/'speaker_stats'/f'{rid}.json']
    for path,table in zip(paths,(frames,words,windows,sentences)):write_parquet(path,table)
    _write_json(paths[-1],stats)
    return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def features_all(force: bool = False) -> None:
    """Generate all five feature outputs for promoted sources, with hash-bound caching."""
    root=Path.cwd();cfg=yaml.safe_load((root/'configs/default.yaml').read_text());settings=cfg['features']
    rows=list(csv.DictReader((root/'data/manifest/recordings.csv').open()))
    base=root/'data/features';manifest_path=base/'provenance.json'
    source_paths=[root/'src/speecheval/features.py',root/'src/speecheval/transcripts.py']
    inputs={'settings':settings,'versions':{p:importlib.metadata.version(p) for p in ('librosa','praat-parselmouth','numpy','pandas','pyarrow','cmudict')},
            'code':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_paths},'recordings':{}}
    old=json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    artifacts={}
    for row in rows:
        rid=row['recording_id'];audio=root/'data/audio/hq'/f'{rid}.wav';alignment_path=root/'data/alignment'/f'{rid}.json'
        identity={'audio':hashlib.sha256(audio.read_bytes()).hexdigest(),'alignment':hashlib.sha256(alignment_path.read_bytes()).hexdigest()}
        inputs['recordings'][rid]=identity
        paths=[base/folder/f'{rid}.parquet' for folder in ('frames','words','windows','sentences')]+[base/'speaker_stats'/f'{rid}.json']
        cached=not force and old.get('inputs',{}).get('recordings',{}).get(rid)==identity and all(old.get('inputs',{}).get(k)==inputs[k] for k in ('settings','versions','code'))
        cached=cached and all(p.exists() and old.get('artifacts',{}).get(str(p.relative_to(root)))==hashlib.sha256(p.read_bytes()).hexdigest() for p in paths)
        if not cached:
            LOGGER.info('Features: %s',rid)
            extract_features(root,audio,json.loads(alignment_path.read_text()),settings)
        artifacts.update({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    base.mkdir(parents=True,exist_ok=True)
    _write_json(manifest_path,{'schema':'features_provenance/v1','inputs':inputs,'artifacts':artifacts})
