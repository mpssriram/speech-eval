"""Deterministic synthetic speech effects, exact time maps and oracle alignments."""
from __future__ import annotations
import copy
import hashlib
import json
import logging
import subprocess
import tempfile
import html
import importlib.metadata
from functools import lru_cache
from typing import Literal
from pathlib import Path
import numpy as np
import parselmouth
from parselmouth.praat import call
import soundfile as sf
import yaml
from scipy.signal import butter, sosfiltfilt, resample_poly, welch
from pydantic import BaseModel, Field, model_validator
from speecheval.align.base import Alignment
from speecheval.verify import _write_json

LOGGER=logging.getLogger(__name__)


@lru_cache(maxsize=1)
def rubberband_version() -> str:
    """Record the actual installed system executable version without changing it."""
    result=subprocess.run(['rubberband','--version'],check=True,capture_output=True,text=True)
    return (result.stdout or result.stderr).strip()


class Flaw(BaseModel):
    type: Literal['rushing','dragging','monotone','too_quiet','awkward_pause','missing_pause','mumbling']
    start: float = Field(ge=0)
    end: float = Field(ge=0)
    severity: int = Field(ge=1,le=5)
    word_start: int = Field(ge=0)
    word_end: int = Field(ge=0)
    parameters: dict

    @model_validator(mode='after')
    def validate_interval(self) -> 'Flaw':
        if self.end<self.start or self.word_end<self.word_start:raise ValueError('Backwards flaw interval')
        return self


class Label(BaseModel):
    schema_id: Literal['labels/v1'] = Field(alias='schema')
    recording_id: str
    reference_id: str | None
    text_id: str
    source: Literal['synthetic','human']
    flaws: list[Flaw]


def stretch(y: np.ndarray, sr: int, factor: float, workdir: Path) -> np.ndarray:
    """Rubber Band fine-mode tempo change, fixed-duration target, unchanged pitch."""
    workdir.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='rubberband-',dir=workdir) as temp:
        source=Path(temp)/'input.wav';target=Path(temp)/'output.wav'
        sf.write(source,y,sr,subtype='FLOAT')
        subprocess.run(['rubberband','--fine','--tempo',str(factor),str(source),str(target)],check=True,capture_output=True)
        wet,actual=sf.read(target,dtype='float32')
        if actual!=sr:raise ValueError('Rubber Band changed sample rate')
    return wet


def edit_map(duration: float, start: float, end: float, new_duration: float) -> list[list[float]]:
    """Monotone piecewise-linear source seconds to flawed seconds, including steps."""
    if not 0<=start<=end<=duration or new_duration<0:raise ValueError('Invalid edit interval')
    return [[0.,0.],[start,start],[end,start+new_duration],[duration,duration+new_duration-(end-start)]]


def map_time(t: float, mapping: list[list[float]], side: str = 'right') -> float:
    """Map seconds; insertion-point word ends use the left side of a step."""
    points=np.asarray(mapping);exact=points[points[:,0]==t,1]
    if len(exact):return float(exact[0] if side=='left' else exact[-1])
    return float(np.interp(t,points[:,0],points[:,1]))


def quiet(y: np.ndarray, sr: int, gain_db: float, shape: str) -> np.ndarray:
    """Flat or trailing gain in dB, with 30 ms ramps for the flat shape."""
    if shape not in ('flat','trail'):raise ValueError('Unknown gain shape')
    db=np.full(len(y),gain_db) if shape=='flat' else np.linspace(0,gain_db,len(y))
    if shape=='flat':
        n=min(round(sr*.03),len(y)//2)
        if n:db[:n]=np.linspace(0,gain_db,n);db[-n:]=np.linspace(gain_db,0,n)
    return (y*10**(db/20)).astype('float32')


def muffle(y: np.ndarray, sr: int, cutoff: float, gain_db: float) -> np.ndarray:
    """Fourth-order zero-phase Butterworth low-pass plus gain, with 30 ms wet ramps."""
    wet=sosfiltfilt(butter(4,cutoff,fs=sr,output='sos'),y)*10**(gain_db/20)
    mix=np.ones(len(y));n=min(round(sr*.03),len(y)//2)
    if n:mix[:n]=np.linspace(0,1,n);mix[-n:]=np.linspace(1,0,n)
    return (mix*wet+(1-mix)*y).astype('float32')


def flatten_pitch(y: np.ndarray, sr: int, kept: float, floor: float, ceiling: float) -> np.ndarray:
    """PSOLA pitch-tier compression in semitones, preserving the region's sample count."""
    sound=parselmouth.Sound(y,sampling_frequency=sr)
    manipulation=call(sound,'To Manipulation',.01,floor,ceiling)
    tier=call(manipulation,'Extract pitch tier')
    count=int(call(tier,'Get number of points'))
    if not count:raise ValueError('No voiced pitch-tier evidence for monotone injection')
    times=[call(tier,'Get time from index',i) for i in range(1,count+1)]
    frequencies=np.array([call(tier,'Get value at index',i) for i in range(1,count+1)])
    median=float(np.median(frequencies))
    call(tier,'Remove points between',0,len(y)/sr)
    for t,hz in zip(times,median*(frequencies/median)**kept):call(tier,'Add point',float(t),float(hz))
    call([tier,manipulation],'Replace pitch tier')
    wet=call(manipulation,'Get resynthesis (overlap-add)').values[0]
    if len(wet)!=len(y):raise ValueError('PSOLA changed sample count')
    return wet.astype('float32')


def choose_site(alignment: dict, config: dict, kind: str, severity: int, placement: int, shape: str = 'flat') -> tuple[int,int] | None:
    """Seeded eligible word region/boundary; never include uncertain word evidence."""
    words=alignment['words'];uncertain=set(alignment.get('uncertain_words',[]));sites=[]
    edge=config['keep_out_s'];duration=alignment['duration_s']
    for a,word in enumerate(words):
        if kind in ('awkward_pause','missing_pause'):
            if a+1>=len(words) or a in uncertain or a+1 in uncertain:continue
            following=words[a+1];gap=following['start']-word['end']
            if word['end']<edge or following['start']>duration-edge:continue
            if kind=='awkward_pause':
                if gap>=.15 or word['sentence']!=following['sentence']:continue
                if any(w['text'][-1:] in '.,;:!?' for w in (word,following)):continue
            elif gap<.35:continue
            sites.append((a,a+1))
        else:
            for n in range(config['region_words']['min'],config['region_words']['max']+1):
                b=a+n-1
                if b>=len(words):continue
                last=words[b]
                if word['start']<edge or last['end']>duration-edge or last['sentence']!=word['sentence']:continue
                if any(i in uncertain or words[i]['end']<=words[i]['start'] for i in range(a,b+1)):continue
                if kind=='too_quiet' and shape=='trail' and b+1<len(words) and words[b+1]['sentence']==last['sentence']:continue
                sites.append((a,b))
    if not sites:return None
    key=f"{config['seed']}|{alignment['recording_id']}|{kind}|{severity}|{placement}"
    seed=int.from_bytes(hashlib.sha256(key.encode()).digest()[:8],'big')
    return sites[int(np.random.default_rng(seed).integers(len(sites)))]


def zero_crossing(y: np.ndarray, sample: int, sr: int) -> int:
    """Nearest sign change within 5 ms; deterministic earliest tie-break."""
    left=max(1,sample-round(.005*sr));right=min(len(y)-1,sample+round(.005*sr))
    if right<left:return max(0,min(len(y),sample))
    candidates=np.flatnonzero(np.signbit(y[left-1:right])!=np.signbit(y[left:right+1]))+left
    return int(candidates[np.argmin(abs(candidates-sample))]) if len(candidates) else max(0,min(len(y),sample))


def splice(y: np.ndarray, start: int, end: int, wet: np.ndarray, fade: int) -> np.ndarray:
    """Duration-preserving equal-power edge blends, no hidden crossfade time loss."""
    wet=wet.copy();n=min(fade,len(wet)//2,(end-start)//2)
    if n:
        angle=np.linspace(0,np.pi/2,n)
        wet[:n]=y[start:start+n]*np.cos(angle)+wet[:n]*np.sin(angle)
        wet[-n:]=wet[-n:]*np.cos(angle)+y[end-n:end]*np.sin(angle)
    return np.concatenate((y[:start],wet,y[end:])).astype('float32')


def room_tone(y: np.ndarray, sr: int, alignment: dict, length: int) -> np.ndarray:
    """Loop the quietest available 300 ms between aligned words, with edge blending."""
    n=round(.3*sr);candidates=[]
    for left,right in zip(alignment['words'],alignment['words'][1:]):
        a=round(left['end']*sr);b=round(right['start']*sr)
        for start in range(a,b-n+1,max(1,n//4)):
            segment=y[start:start+n];candidates.append((float(np.mean(segment.astype(float)**2)),start))
    if not candidates:raise ValueError('No 300 ms inter-word room tone; refusing digital silence')
    _,start=min(candidates);chunk=y[start:start+n]
    result=chunk.copy();fade=min(round(.02*sr),n//2)
    angle=np.linspace(0,np.pi/2,fade)
    while len(result)<length:
        blend=result[-fade:]*np.cos(angle)+chunk[:fade]*np.sin(angle)
        result=np.concatenate((result[:-fade],blend,chunk[fade:])).astype('float32')
    return result[:length]


def inject_once(y: np.ndarray, sr: int, alignment: dict, stats: dict, config: dict, kind: str,
                severity: int, placement: int, workdir: Path, site: tuple[int,int] | None = None,
                shape: str = 'flat') -> tuple[np.ndarray,dict,list[list[float]],dict]:
    """Apply one flaw to mono audio; return audio, labels/v1, map seconds, alignment/v1."""
    if kind not in config['types'] or not 1<=severity<=5:raise ValueError('Unknown type/severity')
    site=site or choose_site(alignment,config,kind,severity,placement,shape)
    if site is None:raise ValueError(f'No eligible {kind} site')
    a,b=site;words=alignment['words'];spec=config['types'][kind]
    parameter=spec['severity'][severity-1];parameters={spec['param']:parameter}
    if any(i in alignment.get('uncertain_words',[]) for i in range(a,b+1)):raise ValueError('Uncertain injection site')
    duration=len(y)/sr;fade=round(config['crossfade_ms']*sr/1000)
    if kind=='awkward_pause':
        gap_start=words[a]['end'];gap_end=words[b]['start'];middle=(gap_start+gap_end)/2
        low=int(np.ceil(gap_start*sr-1e-8));high=int(np.floor(gap_end*sr+1e-8))
        candidate=zero_crossing(y,round(middle*sr),sr)
        point=max(low,min(high,candidate)) if low<=high else round(middle*sr)
        # A zero/sub-sample gap has no safe zero crossing. Preserve exact word
        # ownership at its boundary; the physical cut differs by at most half a sample.
        point_time=middle if gap_end-gap_start<1/sr else point/sr
        extra=round(parameter*sr);tone=room_tone(y,sr,alignment,extra)
        n=min(fade,extra//2,point,len(y)-point)
        if n:
            angle=np.linspace(0,np.pi/2,n)
            tone[:n]=y[point:point+n]*np.cos(angle)+tone[:n]*np.sin(angle)
            tone[-n:]=tone[-n:]*np.cos(angle)+y[point-n:point]*np.sin(angle)
        wet=np.concatenate((y[:point],tone,y[point:])).astype('float32')
        mapping=edit_map(duration,point_time,point_time,extra/sr);label_start=point_time;label_end=point_time+extra/sr
    elif kind=='missing_pause':
        start=round(words[a]['end']*sr);end=round(words[b]['start']*sr)
        original=end-start;kept=max(round(.03*sr),round(original*parameter))
        if kept>original:raise ValueError('Source pause is shorter than the 30 ms floor')
        remove=original-kept;cut_start=start+kept//2;cut_end=cut_start+remove
        # Preserve the exact intended sample count; snap by shifting both cut edges together.
        shift=zero_crossing(y,cut_start,sr)-cut_start
        shift=max(start-cut_start,min(end-cut_end,shift));cut_start+=shift;cut_end+=shift
        wet=np.concatenate((y[:cut_start],y[cut_end:])).astype('float32')
        n=min(fade,kept//2,cut_start,len(wet)-cut_start)
        if n:
            angle=np.linspace(0,np.pi/2,n)
            wet[cut_start-n:cut_start]=y[cut_start-n:cut_start]*np.cos(angle)+y[cut_end-n:cut_end]*np.sin(angle)
        mapping=edit_map(duration,cut_start/sr,cut_end/sr,0.)
        label_start=start/sr;label_end=(start+kept)/sr
        parameters.update(source_pause_s=original/sr,result_pause_s=kept/sr)
    else:
        start=zero_crossing(y,round(words[a]['start']*sr),sr);end=zero_crossing(y,round(words[b]['end']*sr),sr)
        region=y[start:end].copy()
        if kind in ('rushing','dragging'):changed=stretch(region,sr,parameter,workdir)
        elif kind=='monotone':changed=flatten_pitch(region,sr,parameter,stats['pitch_floor_hz'],stats['pitch_ceiling_hz'])
        elif kind=='too_quiet':changed=quiet(region,sr,parameter,shape);parameters['shape']=shape
        else:changed=muffle(region,sr,parameter,spec['extra_gain_db_per_severity']*severity)
        wet=splice(y,start,end,changed,fade) if kind in ('rushing','dragging','monotone') else np.concatenate((y[:start],changed,y[end:])).astype('float32')
        mapping=edit_map(duration,start/sr,end/sr,len(changed)/sr)
        label_start=map_time(words[a]['start'],mapping);label_end=map_time(words[b]['end'],mapping,side='left')
        parameters.update(edit_source_start_s=start/sr,edit_source_end_s=end/sr)
    peak=float(np.max(np.abs(wet)));limit=10**(-1/20)
    if peak>limit:
        adjustment=20*np.log10(limit/peak);wet*=10**(adjustment/20);parameters['peak_normalised_db']=adjustment
    rid=alignment['recording_id'].rsplit('__',1)[0]+f'__{kind}_s{severity}_{placement:02d}'
    label={'schema':'labels/v1','recording_id':rid,'reference_id':alignment['recording_id'],
        'text_id':rid.split('__')[0],'source':'synthetic','flaws':[{'type':kind,'severity':severity,
        'start':round(label_start,3),'end':round(label_end,3),'word_start':a,'word_end':b,'parameters':parameters}]}
    oracle=copy.deepcopy(alignment);oracle.update(recording_id=rid,audio=f'data/flawed/hq/{rid}.flac',
        duration_s=round(len(wet)/sr,3),aligner={'name':'oracle','version':'1'})
    for word in oracle['words']:
        word['start']=round(map_time(word['start'],mapping),3);word['end']=round(map_time(word['end'],mapping,side='left'),3)
    for sentence in oracle['sentences']:
        sentence['start']=oracle['words'][sentence['word_start']]['start'];sentence['end']=oracle['words'][sentence['word_end']]['end']
    Alignment.model_validate(oracle)
    Label.model_validate(label)
    return wet,label,mapping,oracle


def safe_output_pair(wet: np.ndarray, sr: int) -> tuple[np.ndarray,np.ndarray,float]:
    """Common attenuation protects HQ and resampled 16 kHz exports to -1 dBFS."""
    if sr!=44100:raise ValueError('HQ output must be 44.1 kHz')
    down=resample_poly(wet,160,441)
    peak=max(float(np.max(abs(wet))),float(np.max(abs(down))))
    limit=10**(-1/20)
    gain=min(1.,limit/peak) if peak else 1.
    return (wet*gain).astype('float32'),(down*gain).astype('float32'),float(20*np.log10(gain))


def generate_one(root: Path, audio: Path, alignment: dict, stats: dict, config: dict,
                 kind: str, severity: int, placement: int, force: bool = False, shape: str = 'flat') -> dict:
    """Write two PCM16 FLACs, exact label/map and oracle, with artifact-bound cache."""
    rid=alignment['recording_id'].rsplit('__',1)[0]+f'__{kind}_s{severity}_{placement:02d}'
    cache=root/'data/flawed/provenance'/f'{rid}.json'
    identity={'audio_sha256':hashlib.sha256(audio.read_bytes()).hexdigest(),
        'alignment_sha256':hashlib.sha256(json.dumps(alignment,sort_keys=True).encode()).hexdigest(),
        'stats_sha256':hashlib.sha256(json.dumps(stats,sort_keys=True).encode()).hexdigest(),'config':config,'shape':shape,
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'rubberband':rubberband_version(),
        'versions':{p:importlib.metadata.version(p) for p in ('numpy','scipy','praat-parselmouth','soundfile')}}
    if cache.exists() and not force:
        old=json.loads(cache.read_text())
        if old.get('inputs')==identity and all((root/p).exists() and hashlib.sha256((root/p).read_bytes()).hexdigest()==h for p,h in old['artifacts'].items()):return old
    y,sr=sf.read(audio,dtype='float32')
    if sr!=44100 or y.ndim!=1:raise ValueError('Injection requires original 44.1 kHz mono HQ audio')
    wet,label,mapping,oracle=inject_once(y,sr,alignment,stats,config,kind,severity,placement,root/'data/.cache/inject',shape=shape)
    wet,down,adjustment=safe_output_pair(wet,sr)
    if adjustment<0:
        parameters=label['flaws'][0]['parameters']
        parameters['peak_normalised_db']=parameters.get('peak_normalised_db',0.)+adjustment
    paths=[root/'data/flawed'/folder/f'{rid}.flac' for folder in ('hq','align16k')]
    for path in paths:path.parent.mkdir(parents=True,exist_ok=True)
    sf.write(paths[0],wet,sr,subtype='PCM_16')
    sf.write(paths[1],down,16000,subtype='PCM_16')
    paths.extend([root/'data/labels'/f'{rid}.json',root/'data/flawed/timemaps'/f'{rid}.json',root/'data/alignment/oracle'/f'{rid}.json'])
    label=copy.deepcopy(label)
    for flaw in label['flaws']:
        flaw['parameters']={k:(round(v,3) if k.endswith('_s') else float(f'{v:.4g}')) if isinstance(v,float) else v for k,v in flaw['parameters'].items()}
    _write_json(paths[2],label);_write_json(paths[3],{'schema':'timemap/v1','source_id':alignment['recording_id'],
        'recording_id':rid,'breakpoints':[[round(a,3),round(b,3)] for a,b in mapping]});_write_json(paths[4],oracle)
    record={'schema':'injection_provenance/v1','recording_id':rid,'inputs':identity,
        'artifacts':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    _write_json(cache,record)
    return record


def measure_effect(root: Path, audio: Path, label: dict) -> dict:
    """Independently measure the rendered PCM effect; 10% relative parameter tolerance."""
    source,sr=sf.read(audio,dtype='float64');rid=label['recording_id']
    wet,wet_sr=sf.read(root/'data/flawed/hq'/f'{rid}.flac',dtype='float64')
    if wet_sr!=sr:raise ValueError('Effect check sample-rate mismatch')
    flaw=label['flaws'][0];params=flaw['parameters'];kind=flaw['type'];measured=None;expected=None
    delta=(len(wet)-len(source))/sr
    adjustment=params.get('peak_normalised_db',0.)
    if kind=='awkward_pause':measured=delta;expected=params['inserted_pause_s']
    elif kind=='missing_pause':measured=params['source_pause_s']+delta;expected=params['result_pause_s']
    else:
        a=round(params['edit_source_start_s']*sr);b=round(params['edit_source_end_s']*sr)
        original=source[a:b];new_length=b-a+round(delta*sr)
        rendered=wet[a:a+new_length]
        if kind in ('rushing','dragging'):
            measured=(b-a)/new_length;expected=params['speed_factor']
        elif kind=='too_quiet':
            n=round(.06*sr);dry=original[n:-n];changed=rendered[n:-n]
            if params['shape']=='flat':measured=20*np.log10(np.linalg.norm(changed)/np.linalg.norm(dry))-adjustment
            else:
                valid=abs(dry)>.005
                db=20*np.log10(np.maximum(abs(changed[valid]),1e-12)/abs(dry[valid]))-adjustment
                position=np.arange(n,len(original)-n)[valid]/(len(original)-1)
                measured=float(np.polyfit(position,db,1)[0])
            expected=params['gain_db']
        elif kind=='monotone':
            stats=json.loads((root/'data/features/speaker_stats'/f"{label['reference_id']}.json").read_text())
            floor=stats['pitch_floor_hz'];ceiling=stats['pitch_ceiling_hz']
            def spread(signal):
                sound=parselmouth.Sound(signal,sampling_frequency=sr)
                pitch=sound.to_pitch_ac(time_step=.01,pitch_floor=floor,pitch_ceiling=ceiling)
                hz=pitch.selected_array['frequency'];times=pitch.xs()
                hz=hz[(hz>0)&(times>.1)&(times<len(signal)/sr-.1)]
                if len(hz)<10:return float('nan')
                semitones=12*np.log2(hz/np.median(hz))
                return float(np.quantile(semitones,.9)-np.quantile(semitones,.1))
            measured=spread(rendered)/spread(original);expected=params['pitch_range_kept']
        else:
            n=round(.1*sr);dry=original[n:-n];changed=rendered[n:-n]
            hz,power=welch(dry,sr,nperseg=2048);_,actual=welch(changed,sr,nperseg=2048)
            cutoff=params['lowpass_hz']
            # Analytic digital Butterworth power transfer for a forward/reverse 4th-order filter.
            with np.errstate(over='ignore',divide='ignore'):
                transfer=1/(1+(np.tan(np.pi*hz/sr)/np.tan(np.pi*cutoff/sr))**8)**2
            def ratio(p):return 10*np.log10(p[(hz>=2000)&(hz<=6000)].sum()/p[hz<2000].sum())
            measured=float(ratio(actual)-ratio(power));expected=float(ratio(power*transfer)-ratio(power))
    passed=bool(np.isfinite(measured) and abs(measured-expected)<=.1*max(abs(expected),1e-6))
    return {'recording_id':rid,'type':kind,'severity':flaw['severity'],'expected':float(expected),
            'measured':float(measured) if np.isfinite(measured) else None,'passed':passed,
            'metric':{'monotone':'acoustic semitone p90-p10 ratio','mumbling':'high-band ratio drop (dB), analytic filter prediction',
                      'too_quiet':'gain dB (flat RMS or trail slope)'}.get(kind,'duration-derived tempo ratio or pause seconds')}


def inject_preview(force: bool = False) -> None:
    """Generate 35 preview items and all 105 objective checks across three readers."""
    root=Path.cwd();config=yaml.safe_load((root/'configs/flaws.yaml').read_text())
    sources=sorted((root/'data/alignment').glob('gettysburg__*__orig.json'))[:3]
    if len(sources)!=3:raise ValueError('Three source readers are required')
    checks=[];items=[];skipped=[]
    for path in sources:
        alignment=json.loads(path.read_text());Alignment.model_validate(alignment)
        rid=alignment['recording_id'];audio=root/alignment['audio']
        stats=json.loads((root/'data/features/speaker_stats'/f'{rid}.json').read_text())
        for kind in config['types']:
            for severity in range(1,6):
                shape='trail' if kind=='too_quiet' and severity%2==0 else 'flat'
                if choose_site(alignment,config,kind,severity,1,shape) is None:
                    skipped.append({'source_id':rid,'type':kind,'severity':severity,'reason':'no eligible site'})
                    LOGGER.warning('No eligible site: %s %s s%d',rid,kind,severity);continue
                LOGGER.info('Inject %s %s s%d',rid,kind,severity)
                record=generate_one(root,audio,alignment,stats,config,kind,severity,1,force=force,shape=shape)
                label=json.loads((root/'data/labels'/f"{record['recording_id']}.json").read_text())
                checks.append(measure_effect(root,audio,label))
                if path==sources[0]:items.append(label)
    preview=root/'data/flawed/preview';preview.mkdir(parents=True,exist_ok=True)
    _write_json(preview/'manifest.json',{'schema':'preview/v1','items':items,'skipped':skipped})
    rows=[]
    for item in items:
        rid=item['recording_id'];ref=item['reference_id'];flaw=item['flaws'][0]
        source_url=f'../../audio/hq/{ref}.wav';flawed_url=f'../hq/{rid}.flac'
        mapping=json.loads((root/'data/flawed/timemaps'/f'{rid}.json').read_text())['breakpoints']
        original=json.loads((root/'data/alignment'/f'{ref}.json').read_text())['words']
        a=original[flaw['word_start']]['start'];b=original[flaw['word_end']]['end']
        words=' '.join(w['text'] for w in original[flaw['word_start']:flaw['word_end']+1])
        rows.append(f'<tr><td>{html.escape(flaw["type"])} s{flaw["severity"]}<br>{html.escape(words)}</td>'
            f'<td><audio controls preload="none" src="{source_url}"></audio></td>'
            f'<td><audio controls preload="none" src="{flawed_url}"></audio></td>'
            f'<td><button data-a="{a}" data-b="{b}" data-c="{flaw["start"]}" data-d="{flaw["end"]}" onclick="compare(this)">Compare region</button></td></tr>')
    page='''<!doctype html><meta charset="utf-8"><title>Speech flaw preview</title>
<h1>Synthetic flaw preview</h1><p>Automatic effect checks are not evidence of perceptual realism.</p>
<table><tr><th>Effect / words</th><th>Source</th><th>Flawed</th><th>Compare</th></tr>'''+''.join(rows)+'''</table>
<script>
let active=[];
function compare(button){
  active.forEach(a=>a.pause());
  const players=button.closest('tr').querySelectorAll('audio');active=[...players];
  function playPart(player,start,end,next){
    player.currentTime=Math.max(0,start-.3);
    function stop(){if(player.currentTime>=end+.3){player.pause();player.removeEventListener('timeupdate',stop);if(next)next();}}
    player.addEventListener('timeupdate',stop);player.play().catch(()=>player.removeEventListener('timeupdate',stop));
  }
  playPart(players[0],+button.dataset.a,+button.dataset.b,()=>playPart(players[1],+button.dataset.c,+button.dataset.d));
}
</script>'''
    (preview/'index.html').write_text(page,encoding='utf-8')
    failed=[c for c in checks if not c['passed']]
    _write_json(root/'data/flawed/effect_checks.json',{'schema':'effect_checks/v1','relative_tolerance':.1,
        'n_readers':len(sources),'checks':checks,'failed':failed,'skipped':skipped,
        'pitch_measurement':'Identical source speaker_stats floor/ceiling for source and rendered audio; semitone p90-p10 over voiced frames excluding 100 ms edges.',
        'limitations':['Objective parameter checks do not establish listening quality or realism.'],
        'passed':len(checks)==105 and not failed and not skipped})
    LOGGER.info('Preview %d files; effect checks %d/105 passed',len(items),len(checks)-len(failed))
    if failed or skipped or len(checks)!=105:raise ValueError(f'Effect checks incomplete: {len(failed)} failed, {len(skipped)} skipped')
