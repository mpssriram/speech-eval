import {useCallback,useEffect,useRef,useState} from 'react';
import {Alert,Button,Loader,NativeSelect,Textarea} from '@mantine/core';
import {flaws,request,type Analysis,type Job,type Take,type TextOption,type Tracks} from './types';
import {Waveform,FeatureChart,ProgressChart,featureOptions} from './Evidence';
import {Recorder} from './Recorder';
import type {Segment} from './types';
import {takeLabels} from './takeLabels';

function Numbers({text}:{text:string}){return <>{text.split(/(>?[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)/g).map((part,i)=>/\d/.test(part)?<strong className="number" key={i}>{part}</strong>:part)}</>;}
function Legend({hidden,onToggle}:{hidden:string[];onToggle:(type:string)=>void}){return <div className="legend" data-testid="legend" aria-label="Filter flagged phrases">{Object.entries(flaws).map(([type,f])=><button key={type} aria-pressed={!hidden.includes(type)} onClick={()=>onToggle(type)}><i style={{background:f.color}}/>{f.label}</button>)}</div>;}

function Results({analysis,tracks,aid,onError}:{analysis:Analysis;tracks:Tracks;aid:string;onError:(message:string)=>void}){
  const [hidden,setHidden]=useState<string[]>([]);
  const [selected,setSelected]=useState(0),[feature,setFeature]=useState('rate'),[seek,setSeek]=useState<number|null>(null);
  const player=useRef<HTMLAudioElement>(null),end=useRef<number>(Infinity);
  const playback=useRef(0);
  const [hasPlayback,setHasPlayback]=useState(false);
  const [segments,setSegments]=useState<Record<number,Segment|null>>({}),[takes,setTakes]=useState<Take[]>([]);
  useEffect(()=>{
    let cancelled=false;
    if(analysis.reference.baseline_recording_id)void Promise.all(analysis.regions.map(async(r,i)=>{
      const response=await fetch(`/api/analyses/${aid}/baseline-segment?word_start=${r.word_start}&word_end=${r.word_end}`);
      if(response.status===404)return [i,null] as const;
      if(!response.ok)throw new Error('Could not load baseline word matches.');
      return [i,await response.json() as Segment] as const;
    })).then(entries=>{if(!cancelled)setSegments(Object.fromEntries(entries));}).catch(e=>{if(!cancelled)onError(e.message);});
    request<Take[]>(`/api/history?text_id=${encodeURIComponent(analysis.text_id)}`).then(data=>{if(!cancelled)setTakes(data);}).catch(e=>{if(!cancelled)onError(e.message);});
    return ()=>{cancelled=true;playback.current++;};
  },[aid,analysis,onError]);
  const select=useCallback((index:number)=>{setSelected(index);},[]);
  useEffect(()=>{const list=document.querySelector('.flaw-list'),card=list?.querySelector(`[data-region-index="${selected}"]`) as HTMLElement|null;if(list&&card)list.scrollTop=card.offsetTop;},[selected]);
  const region=analysis.regions[selected];
  async function play(index:number,baseline:boolean){
    const token=++playback.current;
    try{
      const r=analysis.regions[index];setSelected(index);setHasPlayback(true);
      const first=tracks.words.find(w=>w.i===r.word_start),last=tracks.words.find(w=>w.i===r.word_end);
      const segment=baseline?segments[index]:{recording_id:analysis.recording_id,start:first?.start??r.start,end:last?.end??r.end};
      if(!segment)throw new Error('No exact same-word segment is available in this baseline.');
      const media=player.current!;media.src=`/api/audio/${segment.recording_id}`;end.current=segment.end;
      await new Promise<void>((resolve,reject)=>{media.onloadedmetadata=()=>resolve();media.onerror=()=>reject(new Error('Could not load playback audio'));media.load();});
      if(token!==playback.current)return;
      media.currentTime=Math.max(0,segment.start);await media.play();
    }catch(e){if(token===playback.current)onError((e as Error).message);}
  }
  const categories=['pace','pitch','pauses','volume','clarity'];
  const categoryTypes:Record<string,string[]>={pace:['rushing','dragging'],pitch:['monotone'],pauses:['awkward_pause','missing_pause'],volume:['too_quiet'],clarity:['mumbling']};
  return <>
    <div className="results-heading"><div><h1>Delivery evidence</h1><p>{takeLabels[analysis.recording_id]||analysis.text_id.replaceAll('_',' ')} · Mode {analysis.mode} · {analysis.reference.kind.replaceAll('_',' ')}</p></div><span className="subtle">Scores describe detected delivery differences, not content quality.</span></div>
    <section className="score-card" aria-label="Rubric scores"><div className="overall"><span>Overall</span><strong data-testid="overall-score">{analysis.scores.overall.toFixed(1)}<small>/10</small></strong></div><div className="categories">{categories.map(c=>{
      const count=analysis.regions.filter(r=>categoryTypes[c].includes(r.type)).length;
      return <div key={c}><span>{c[0].toUpperCase()+c.slice(1)}</span><meter min={0} max={10} value={analysis.scores[c]} aria-label={`${c} score`}/><strong>{analysis.scores[c].toFixed(1)}<small>/10</small></strong><p>{count?`${count} flagged ${count===1?'region':'regions'}`:'No detected penalty'}</p></div>;})}</div></section>
    <div className="workspace"><div className="recording-column"><Waveform analysis={analysis} onSelect={select} seek={seek} selected={selected} hidden={hidden}/>
    <section className="transcript"><h2>Transcript</h2><p>Click a word to seek. Underlines mark detected regions.</p><div>{tracks.words.map(w=>{
      const idx=analysis.regions.findIndex(r=>r.word_start<=w.i&&w.i<=r.word_end);const f=idx>=0?analysis.regions[idx]:undefined;
      return <button className={idx===selected?'selected-word':''} key={w.i} title={`${w.start.toFixed(2)} s${f?' · '+flaws[f.type].label:''}`}
        style={f?{textDecorationColor:flaws[f.type].color,textDecorationLine:'underline'}:{}}
        onClick={()=>{setSeek(w.start);if(idx>=0)setSelected(idx);}}>{w.text}</button>;})}</div></section>
    <section className="evidence"><div className="section-heading"><h2>Measured delivery</h2><span>{analysis.mode==='C'?'Per-word curves; no same-text reference band':'Shaded band: reference ±2σ in transformed space'}</span></div>
      <div role="tablist" aria-label="Delivery features" className="feature-tabs">{featureOptions.map(f=><button key={f.id} role="tab" aria-selected={feature===f.id} onClick={()=>setFeature(f.id)}>{f.label}</button>)}</div>
      <FeatureChart tracks={tracks} feature={feature} selected={region}/></section>
    </div><section className="flag-panel"><div className="section-heading"><h2>Flagged phrases</h2><span>{analysis.regions.length} detected regions · sorted by time</span></div>
      <Legend hidden={hidden} onToggle={type=>setHidden(old=>old.includes(type)?old.filter(t=>t!==type):[...old,type])}/>{analysis.regions.length>0&&analysis.regions.every(r=>hidden.includes(r.type))&&<p className="empty">All flaw types are hidden. Select a filter to show its phrases.</p>}
      {!analysis.regions.length?<div className="empty">{analysis.mode==='B'?'No delivery differences detected against your earlier take. A relative match is not an expert-quality rating.':analysis.mode==='C'?'No flaws detected against the four-feature norms. This is an automatic estimate, not a human rating.':'No flaws detected against the expert-reader reference. This is an automatic comparison, not a human rating.'}</div>:
        <div className="flaw-list">{analysis.regions.map((r,i)=>({r,i})).sort((a,b)=>a.r.start-b.r.start).map(({r,i})=><article hidden={hidden.includes(r.type)} key={`${r.type}-${r.start}-${i}`} data-testid="flaw-card" data-region-index={i} aria-current={selected===i?'true':undefined} className={`flaw-card ${selected===i?'active':''}`} style={{borderLeftColor:flaws[r.type].color}}>
          <button className="flaw-title" onClick={()=>{setSelected(i);setSeek(r.start);}}><span className="type-chip" style={{color:flaws[r.type].color}}>{flaws[r.type].label}</span><span>{r.start.toFixed(2)}–{r.end.toFixed(2)} s</span></button>
          <div className="severity" aria-label={`Severity ${r.severity} of 5`}>{'●'.repeat(r.severity)}{'○'.repeat(5-r.severity)}<span>Severity {r.severity}/5</span></div>
          <blockquote>{tracks.words.slice(r.word_start,r.word_end+1).map(w=>w.text).join(' ')}</blockquote><p><Numbers text={r.display_explanation??r.explanation}/></p>
          <div className="playback"><Button variant="light" aria-label="Yours" onClick={()=>void play(i,false)}>Yours</Button><Button variant="subtle" aria-label="Baseline (same words)" disabled={!segments[i]} onClick={()=>void play(i,true)}>Baseline (same words)</Button></div>
          {!analysis.reference.baseline_recording_id?<small>Mode C has no same-text baseline.</small>:segments[i]===null?<small>Baseline words differ here; an exact phrase match is unavailable.</small>:!segments[i]?<small>Checking baseline word matches…</small>:null}
        </article>)}</div>}
      <audio hidden={!hasPlayback} className="comparison-player" data-testid="phrase-player" ref={player} controls aria-label="Selected phrase playback" onTimeUpdate={()=>{if(player.current&&player.current.currentTime>=end.current)player.current.pause();}}/>
    </section></div>
    {!!analysis.key_moments.length&&<section className="tips"><h2>Heuristic tips (not scored) <small>Key moments</small></h2>{analysis.key_moments.map((k,i)=><p className="guideline" key={i}><strong>{k.passed?'Within guideline':'Check this moment'}</strong> · {k.message}</p>)}</section>}
    {analysis.progress&&<section data-testid="rehearsal-progress"><h2>Changes since your earlier take</h2><p className="subtle">Both takes are checked against expert readers for these counts. The score above compares this take with your earlier delivery.</p>
      <div className="progress-table"><table><thead><tr><th>Delivery flag</th><th>Earlier count</th><th>Current count</th><th>Flagged seconds, earlier → current</th></tr></thead><tbody>{Object.entries(analysis.progress).map(([type,p])=><tr key={type}><th>{flaws[type as keyof typeof flaws]?.label||type}</th><td>{p.previous.count}</td><td>{p.current.count}</td><td>{p.previous.duration_s.toFixed(2)} → {p.current.duration_s.toFixed(2)}</td></tr>)}</tbody></table></div>
    </section>}
    {takes.length>1&&<section><h2>Rehearsal history</h2><p className="subtle">Compare scores within the same mode and reference. Mode B scores are relative to the selected earlier take.</p><ProgressChart takes={takes}/></section>}
    {!!analysis.warnings.length&&<details><summary>Analysis warnings ({analysis.warnings.length})</summary><pre>{JSON.stringify(analysis.warnings,null,2)}</pre></details>}
    <p className="limitations">Automatic, reproducible estimates. Human validation is pending; calibrated rules can produce false alarms. Mode C is a four-feature prototype, not a substitute for same-text comparison.</p>
  </>;
}

export default function App(){
  const [texts,setTexts]=useState<TextOption[]>([]),[text,setText]=useState('gettysburg'),[mode,setMode]=useState('A'),[transcript,setTranscript]=useState('');
  const [file,setFile]=useState<File|null>(null),[history,setHistory]=useState<Take[]>([]),[previous,setPrevious]=useState('');
  const [aid,setAid]=useState(location.pathname.startsWith('/results/')?location.pathname.split('/')[2]:''),[job,setJob]=useState<Job|null>(null),[tracks,setTracks]=useState<Tracks|null>(null);
  const [error,setError]=useState(''),[sending,setSending]=useState(false),[textsLoading,setTextsLoading]=useState(true);
  useEffect(()=>{request<TextOption[]>('/api/texts').then(setTexts).catch(e=>setError(e.message)).finally(()=>setTextsLoading(false));},[]);
  useEffect(()=>{let cancelled=false;setPrevious('');request<Take[]>(`/api/history?text_id=${encodeURIComponent(job?.analysis?.text_id||text)}`).then(data=>{if(!cancelled)setHistory(data);}).catch(e=>{if(!cancelled)setError(e.message);});return ()=>{cancelled=true;};},[text,aid,job?.analysis?.text_id]);
  useEffect(()=>{const navigate=()=>{setAid(location.pathname.startsWith('/results/')?location.pathname.split('/')[2]:'');setError('');};window.addEventListener('popstate',navigate);return ()=>window.removeEventListener('popstate',navigate);},[]);
  useEffect(()=>{
    if(!aid)return;let cancelled=false;let timer:ReturnType<typeof setTimeout>;
    setTracks(null);setJob(null);
    async function poll(){try{const value=await request<Job>(`/api/analyses/${aid}`);if(cancelled)return;setJob(value);
      if(value.status==='done'){const data=await request<Tracks>(`/api/analyses/${aid}/tracks`);if(!cancelled)setTracks(data);}
      else if(value.status==='error')setError(value.error||'Analysis failed. Try a matching transcript.');
      else timer=setTimeout(()=>void poll(),1000);
    }catch(e){if(!cancelled)setError((e as Error).message);}}
    void poll();return ()=>{cancelled=true;clearTimeout(timer);};
  },[aid]);
  async function submit(event:React.FormEvent){
    event.preventDefault();if(!file){setError('Choose an audio file first.');return;}setError('');setSending(true);
    try{const form=new FormData();form.append('audio',file);form.append('mode',text==='own_speech'?'C':mode);form.append('text_id',text);
      if(transcript.trim())form.append('transcript',transcript.trim());if(mode==='B'&&text!=='own_speech')form.append('previous_analysis_id',previous);
      const result=await request<Job>('/api/analyses',{method:'POST',body:form});setAid(result.analysis_id);window.history.pushState({},'',`/results/${result.analysis_id}`);
    }catch(e){setError((e as Error).message);}finally{setSending(false);}
  }
  function reset(){setAid('');setJob(null);setTracks(null);setError('');window.history.pushState({},'','/');}
  function openTake(id:string){if(!id)return;setAid(id);setError('');window.history.pushState({},'',`/results/${id}`);}
  const shownMode=job?.analysis?.mode||mode;
  const busy=!!aid&&(!job||['queued','running'].includes(job.status)||job.status==='done'&&!tracks);
  return <div className="shell"><header className="app-header"><button className="brand" onClick={reset} aria-label="Speech Eval home"><svg viewBox="0 0 40 32" aria-hidden="true"><path d="M3 13v6m7-13v20m7-25v30m7-21v12m7-18v24m6-16v8"/></svg><span>Speech-Eval</span></button>
      <div className="header-picker"><label htmlFor="header-take">{aid?'Recording / take':'Text / take'}</label><select id="header-take" value={aid||text} onChange={e=>aid?openTake(e.target.value):(setText(e.target.value),setMode(e.target.value==='own_speech'?'C':'A'),setTranscript(''))}>
      {aid?<>{!history.some(t=>t.analysis_id===aid)&&<option value={aid}>{job?.analysis?.text_id||'Loading recording'} · current take</option>}{history.map((t,i)=><option key={t.analysis_id} value={t.analysis_id}>{takeLabels[t.recording_id]||`${(job?.analysis?.text_id||text).replaceAll('_',' ')} · Analysis ${i+1}`} · Mode {t.mode}</option>)}</>:<>{texts.map(t=><option key={t.text_id} value={t.text_id}>{t.title}</option>)}<option value="own_speech">My own speech (Mode C-lite)</option></>}</select></div>
      <div className="mode-control" role="group" aria-label="Analysis mode">{['A','B','C'].map(m=><button key={m} aria-pressed={shownMode===m} title={{A:'Compare with expert readers',B:'Compare with my previous take',C:'Compare with good-speaker norms'}[m]} disabled={aid?!history.some(t=>t.mode===m&&t.recording_id===job?.analysis?.recording_id):text==='own_speech'&&m!=='C'} onClick={()=>{if(aid){if(shownMode!==m)openTake(history.find(t=>t.mode===m&&t.recording_id===job?.analysis?.recording_id)?.analysis_id||'');}else setMode(m);}}>Mode {m}</button>)}</div>
      <Button variant="light" onClick={reset}>New analysis</Button></header>
    <main>{error&&<Alert color="red" title="Could not complete that action" role="alert" withCloseButton onClose={()=>setError('')}>{error}</Alert>}
      {!aid?<><div className="intro"><h1>Hear the delivery.<br/>See the evidence.</h1><p>Compare a recording with skilled readers or your earlier take. Explore each detected difference in the audio and the measurements.</p></div>
        <form onSubmit={submit} className="new-analysis"><div className="form-main"><h2>New analysis</h2>
          {textsLoading?<Loader aria-label="Loading reference texts"/>:<NativeSelect label="Speech text" value={text} onChange={e=>{setText(e.target.value);setMode(e.target.value==='own_speech'?'C':'A');setTranscript('');}} data={[...texts.map(t=>({value:t.text_id,label:t.title})),{value:'own_speech',label:'My own speech (Mode C-lite)'}]}/>}
          {text!=='own_speech'&&<NativeSelect label="Comparison" value={mode} onChange={e=>setMode(e.target.value)} data={[{value:'A',label:'Compare with expert readers'},{value:'B',label:'Compare with my previous take'},{value:'C',label:'Compare with good-speaker norms'}]}/>}
          {mode==='B'&&text!=='own_speech'&&<NativeSelect label="Previous take" value={previous} onChange={e=>setPrevious(e.target.value)} data={[{value:'',label:history.length?'Choose an earlier analysis':'No previous takes yet'},...history.map((t,i)=>({value:t.analysis_id,label:`Take ${i+1} · ${t.scores.overall.toFixed(1)}/10 · ${t.recording_id}`}))]}/>}
          <Textarea label={text==='own_speech'?'Your transcript':'As-read transcript (optional)'} description={text==='own_speech'?'Paste the words you actually spoke. No content grading.':'If omitted, new audio is aligned to the canonical text on CPU.'} value={transcript} onChange={e=>setTranscript(e.target.value)} minRows={text==='own_speech'?5:3} autosize required={text==='own_speech'}/>
          <label className="upload">Audio file<input aria-label="Audio file" type="file" accept=".wav,.mp3,.m4a,.webm,.ogg" onChange={e=>setFile(e.target.files?.[0]||null)}/><span>{file?file.name:'Choose a recording'} · max 25 MB / 10 minutes</span></label>
          <Recorder onFile={setFile} onError={setError}/>
          <Button type="submit" size="md" loading={sending} disabled={!file||(mode==='B'&&!previous)||(text==='own_speech'&&!transcript.trim())}>Analyse recording</Button>
        </div><aside className="form-aside"><h3>What you’ll see</h3><p>Time-marked differences in pace, pitch, pauses, volume and clarity.</p><p>Each flag links its measured evidence to the same words in a baseline recording.</p><div className="notice">No loudness normalization. Your original recording stays unchanged.</div><p className="subtle">Automatic scores are experimental. They don’t judge arguments, wording or speaking ability.</p></aside></form>
      </>:busy?<section className="loading" aria-live="polite"><Loader/><h1>{job?.status==='queued'?'Recording queued':'Analysing your delivery'}</h1><p>Alignment and features run sequentially. This page updates every second.</p><div className="skeleton"/><div className="skeleton short"/></section>:
        job?.status==='done'&&job.analysis&&tracks?<Results key={aid} analysis={job.analysis} tracks={tracks} aid={aid} onError={setError}/>:<section className="empty"><h1>Analysis unavailable</h1><p>{job?.error||'Check the error above, then start a new analysis.'}</p><Button onClick={reset}>New analysis</Button></section>}
    </main><footer>Speech delivery, grounded in audio. <span>Rule-based · deterministic · human validation pending</span></footer></div>;
}
