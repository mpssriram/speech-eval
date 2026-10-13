import {useCallback,useEffect,useRef,useState} from 'react';
import {Alert,Button,Loader,NativeSelect,Textarea} from '@mantine/core';
import {flaws,request,type Analysis,type Job,type Take,type TextOption,type Tracks} from './types';
import {Results} from './Results';
import {Recorder} from './Recorder';
import {takeLabels} from './takeLabels';

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
