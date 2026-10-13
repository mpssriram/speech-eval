import {useCallback,useEffect,useRef,useState} from 'react';
import {Button} from '@mantine/core';
import {flaws,request,type Analysis,type Tracks,type Take,type Segment,type ResultSource,type FlawType} from './types';
import {Waveform,FeatureChart,ProgressChart,featureOptions} from './Evidence';
import {takeLabels} from './takeLabels';
import {detectorRule} from './detectorRules';
import {formatExplanation,formatText,timeRange,fixed} from './presentation.js';

function Numbers({text}:{text:string}){return <>{text.split(/(>?[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)/g).map((part,i)=>/\d/.test(part)?<strong className="number" key={i}>{part}</strong>:part)}</>;}
function Legend({counts,active,onSelect}:{counts:Record<string,number>;active:FlawType|null;onSelect:(type:FlawType|null)=>void}){return <div className="legend" data-testid="legend" role="group" aria-label="Filter flagged phrases"><button aria-pressed={active===null} onClick={()=>onSelect(null)}>All ({Object.values(counts).reduce((sum,count)=>sum+count,0)})</button>{Object.entries(flaws).map(([type,f])=><button key={type} className={counts[type]?'':'zero-count'} aria-pressed={active===type} onClick={()=>onSelect(type as FlawType)}><i style={{background:f.color}}/>{f.label} ({counts[type]})</button>)}</div>;}


export function Results({analysis,tracks,aid,onError,source}:{analysis:Analysis;tracks:Tracks;aid:string;onError:(message:string)=>void;source?:ResultSource}){
  const [activeType,setActiveType]=useState<FlawType|null>(null);
  const [notice,setNotice]=useState<FlawType|null>(null),[noticeVersion,setNoticeVersion]=useState(0);
  const counts=Object.fromEntries(Object.keys(flaws).map(type=>[type,analysis.regions.filter(r=>r.type===type).length]));
  const hidden=activeType?Object.keys(flaws).filter(type=>type!==activeType):[];
  const list=useRef<HTMLDivElement>(null);
  useEffect(()=>{if(!notice)return;const timer=setTimeout(()=>setNotice(null),5000);return ()=>clearTimeout(timer);},[notice,noticeVersion]);
  function filter(type:FlawType|null){
    if(type&&counts[type]===0){setNotice(type);setNoticeVersion(v=>v+1);return;}
    setNotice(null);
    const next=type===activeType?null:type;setActiveType(next);
    if(next){const first=analysis.regions.map((r,i)=>({r,i})).filter(({r})=>r.type===next).sort((a,b)=>a.r.start-b.r.start)[0];setSelected(first.i);setSeek(first.r.start);}
  }
  const [selected,setSelected]=useState(source?.selectedRegion??0),[feature,setFeature]=useState('rate'),[seek,setSeek]=useState<number|null>(null);
  const player=useRef<HTMLAudioElement>(null),end=useRef<number>(Infinity);
  const playback=useRef(0);
  const [hasPlayback,setHasPlayback]=useState(false);
  const [segments,setSegments]=useState<Record<number,Segment|null>>({}),[takes,setTakes]=useState<Take[]>([]);
  useEffect(()=>{
    let cancelled=false;
    if(source){setSegments(source.segments);setTakes([]);return;}
    if(analysis.reference.baseline_recording_id)void Promise.all(analysis.regions.map(async(r,i)=>{
      const response=await fetch(`/api/analyses/${aid}/baseline-segment?word_start=${r.word_start}&word_end=${r.word_end}`);
      if(response.status===404)return [i,null] as const;
      if(!response.ok)throw new Error('Could not load baseline word matches.');
      return [i,await response.json() as Segment] as const;
    })).then(entries=>{if(!cancelled)setSegments(Object.fromEntries(entries));}).catch(e=>{if(!cancelled)onError(e.message);});
    request<Take[]>(`/api/history?text_id=${encodeURIComponent(analysis.text_id)}`).then(data=>{if(!cancelled)setTakes(data);}).catch(e=>{if(!cancelled)onError(e.message);});
    return ()=>{cancelled=true;playback.current++;};
  },[aid,analysis,onError,source]);
  const select=useCallback((index:number)=>{setSelected(index);setActiveType(old=>old&&analysis.regions[index]?.type!==old?null:old);},[analysis]);
  useEffect(()=>{const card=list.current?.querySelector(`[data-region-index="${selected}"]`) as HTMLElement|null;if(list.current&&card){list.current.scrollTop=card.offsetTop;if(activeType)card.scrollIntoView({block:'nearest'});}},[selected,activeType]);
  const region=analysis.regions[selected];
  async function play(index:number,baseline:boolean){
    const token=++playback.current;
    try{
      const r=analysis.regions[index];setSelected(index);setHasPlayback(true);
      const first=tracks.words.find(w=>w.i===r.word_start),last=tracks.words.find(w=>w.i===r.word_end);
      const segment=baseline?segments[index]:{recording_id:analysis.recording_id,start:first?.start??r.start,end:last?.end??r.end};
      if(!segment)throw new Error('No exact same-word segment is available in this baseline.');
      const media=player.current!;media.src=source?.audio(segment.recording_id)??`/api/audio/${segment.recording_id}`;end.current=segment.end;
      await new Promise<void>((resolve,reject)=>{media.onloadedmetadata=()=>resolve();media.onerror=()=>reject(new Error('Could not load playback audio'));media.load();});
      if(token!==playback.current)return;
      media.currentTime=Math.max(0,segment.start);await media.play();
    }catch(e){if(token===playback.current)onError((e as Error).message);}
  }
  const categories=['pace','pitch','pauses','volume','clarity'];
  const categoryTypes:Record<string,string[]>={pace:['rushing','dragging'],pitch:['monotone'],pauses:['awkward_pause','missing_pause'],volume:['too_quiet'],clarity:['mumbling']};
  return <>
    <div className="results-heading"><div><h1>{source?.title||"Delivery evidence"}</h1><p>{takeLabels[analysis.recording_id]||analysis.text_id.replaceAll('_',' ')} · Mode {analysis.mode} · {analysis.reference.kind.replaceAll('_',' ')}</p></div><span className="subtle">Scores describe detected delivery differences, not content quality.</span></div>
    <section className="score-card" aria-label="Rubric scores"><div className="overall"><span>Overall</span><strong data-testid="overall-score">{fixed(analysis.scores.overall,1)}<small>/10</small></strong></div><div className="categories">{categories.map(c=>{
      const count=analysis.regions.filter(r=>categoryTypes[c].includes(r.type)).length;
      return <div key={c}><span>{c[0].toUpperCase()+c.slice(1)}</span><meter min={0} max={10} value={analysis.scores[c]} aria-label={`${c} score`}/><strong>{fixed(analysis.scores[c],1)}<small>/10</small></strong><p>{count?`${count} flagged ${count===1?'region':'regions'}`:'No detected penalty'}</p></div>;})}</div></section>
    <div className="workspace"><div className="recording-column"><Waveform source={source} analysis={analysis} onSelect={select} seek={seek} selected={selected} hidden={hidden}/>
    <section className="transcript"><h2>Transcript</h2><p>Click a word to seek. Underlines mark detected regions.</p><div>{tracks.words.map(w=>{
      const idx=analysis.regions.findIndex(r=>r.word_start<=w.i&&w.i<=r.word_end);const f=idx>=0?analysis.regions[idx]:undefined;
      return <button className={idx===selected?'selected-word':''} key={w.i} title={`${w.start.toFixed(2)} s${f?' · '+flaws[f.type].label:''}`}
        style={f?{textDecorationColor:flaws[f.type].color,textDecorationLine:'underline'}:{}}
        onClick={()=>{setSeek(w.start);if(idx>=0)setSelected(idx);}}>{w.text}</button>;})}</div></section>
    {!source&&<section className="evidence"><div className="section-heading"><h2>Measured delivery</h2><span>{analysis.mode==='C'?'Per-word curves; no same-text reference band':'Shaded band: reference ±2σ in transformed space'}</span></div>
      <div role="tablist" aria-label="Delivery features" className="feature-tabs">{featureOptions.map(f=><button key={f.id} role="tab" aria-selected={feature===f.id} onClick={()=>setFeature(f.id)}>{f.label}</button>)}</div>
      <FeatureChart tracks={tracks} feature={feature} selected={region}/></section>}
    </div><section className="flag-panel"><div className="section-heading"><h2>Flagged phrases</h2><span>{analysis.regions.length} detected regions · sorted by time</span></div>
      <Legend counts={counts} active={activeType} onSelect={filter}/>
      {notice&&<div className="filter-notice" role="status" aria-live="polite" aria-atomic="true"><div><p>No {flaws[notice].label} regions were flagged in this recording.</p><p>{detectorRule(notice,analysis.mode)}</p></div><button aria-label="Dismiss notice" onClick={()=>setNotice(null)}>×</button></div>}
      {!analysis.regions.length?<div className="empty">{analysis.mode==='B'?'No delivery differences detected against your earlier take. A relative match is not an expert-quality rating.':analysis.mode==='C'?'No flaws detected against the four-feature norms. This is an automatic estimate, not a human rating.':'No flaws detected against the expert-reader reference. This is an automatic comparison, not a human rating.'}</div>:
        <div className="flaw-list" ref={list}>{analysis.regions.map((r,i)=>({r,i})).sort((a,b)=>a.r.start-b.r.start).map(({r,i})=><article hidden={hidden.includes(r.type)} key={`${r.type}-${r.start}-${i}`} data-testid="flaw-card" data-region-index={i} data-type={r.type} aria-current={selected===i?'true':undefined} className={`flaw-card ${selected===i?'active':''}`} style={{borderLeftColor:flaws[r.type].color}}>
          <button className="flaw-title" aria-expanded={selected===i} aria-controls={`phrase-details-${aid}-${i}`} onClick={()=>{setSelected(i);setSeek(r.start);}}><span className="type-chip" style={{color:flaws[r.type].color}}>{flaws[r.type].label}</span><span>{timeRange(r.start,r.end)}</span></button>
          <div className="flaw-details" id={`phrase-details-${aid}-${i}`} hidden={selected!==i}>
          <div className="severity" aria-label={`Severity ${r.severity} of 5`}>{'●'.repeat(r.severity)}{'○'.repeat(5-r.severity)}<span>Severity {r.severity}/5</span></div>
          <blockquote>{tracks.words.slice(r.word_start,r.word_end+1).map(w=>w.text).join(' ')}</blockquote><p className="explanation"><Numbers text={formatExplanation(r,tracks.words,analysis.mode)}/></p>
          <div className="playback"><Button variant="light" aria-label="Yours" onClick={()=>void play(i,false)}>Yours</Button><Button variant="subtle" aria-label="Baseline (same words)" disabled={!segments[i]} onClick={()=>void play(i,true)}>Baseline (same words)</Button></div>
          {!analysis.reference.baseline_recording_id?<small>Mode C has no same-text baseline.</small>:segments[i]===null?<small>Baseline words differ here; an exact phrase match is unavailable.</small>:!segments[i]?<small>Checking baseline word matches…</small>:null}
          </div>
        </article>)}</div>}
      <audio hidden={!hasPlayback} className="comparison-player" data-testid="phrase-player" ref={player} controls aria-label="Selected phrase playback" onTimeUpdate={()=>{if(player.current&&player.current.currentTime>=end.current)player.current.pause();}}/>
    </section></div>
    {!!analysis.key_moments.length&&<section className="tips"><h2>Heuristic tips (not scored) <small>Key moments</small></h2>{analysis.key_moments.map((k,i)=><p className="guideline" key={i}><strong>{k.passed?'Within guideline':'Check this moment'}</strong> · {formatText(k.message)}</p>)}</section>}
    {analysis.progress&&<section data-testid="rehearsal-progress"><h2>Changes since your earlier take</h2><p className="subtle">Both takes are checked against expert readers for these counts. The score above compares this take with your earlier delivery.</p>
      <div className="progress-table"><table><thead><tr><th>Delivery flag</th><th>Earlier count</th><th>Current count</th><th>Flagged seconds, earlier → current</th></tr></thead><tbody>{Object.entries(analysis.progress).map(([type,p])=><tr key={type}><th>{flaws[type as keyof typeof flaws]?.label||type}</th><td>{p.previous.count}</td><td>{p.current.count}</td><td>{p.previous.duration_s.toFixed(2)} → {p.current.duration_s.toFixed(2)}</td></tr>)}</tbody></table></div>
    </section>}
    {takes.length>1&&<section><h2>Rehearsal history</h2><p className="subtle">Compare scores within the same mode and reference. Mode B scores are relative to the selected earlier take.</p><ProgressChart takes={takes}/></section>}
    {!!analysis.warnings.length&&<details><summary>Analysis warnings ({analysis.warnings.length})</summary><pre>{formatText(JSON.stringify(analysis.warnings,null,2))}</pre></details>}
    <p className="limitations">Automatic, reproducible estimates. Human validation is pending; calibrated rules can produce false alarms. Mode C is a four-feature prototype, not a substitute for same-text comparison.</p>
  </>;
}
