import {useEffect,useRef,useState} from 'react';
import WaveSurfer from 'wavesurfer.js';
import Regions from 'wavesurfer.js/dist/plugins/regions.esm.js';
import Plotly from 'plotly.js-basic-dist';
import {timeRange} from './presentation.js';
import type {Data,Layout} from 'plotly.js';
import {flaws,type Analysis,type Region,type Tracks,type Take,type ResultSource} from './types';

export function Waveform({analysis,onSelect,seek,selected,hidden=[],source}:{analysis:Analysis;onSelect:(index:number)=>void;seek:number|null;selected:number;hidden?:string[];source?:ResultSource}){
  const box=useRef<HTMLDivElement>(null);const audio=useRef<HTMLAudioElement>(null);const wave=useRef<WaveSurfer|null>(null);
  const regionPlugin=useRef<ReturnType<typeof Regions.create>|null>(null);
  const [error,setError]=useState('');
  const [ready,setReady]=useState(false);
  useEffect(()=>{
    if(!box.current||!audio.current)return;
    const regions=Regions.create();
    regionPlugin.current=regions;setError('');setReady(false);
    const instance=WaveSurfer.create({container:box.current,media:audio.current,url:source?.audio(analysis.recording_id)??`/api/audio/${analysis.recording_id}`,
      ...(source?.peaks?{peaks:[source.peaks],duration:analysis.duration_s}:{}),
      waveColor:'#63869f',progressColor:'#55d5e8',cursorColor:'#e5eff7',height:180,barWidth:2,barGap:2,normalize:false,plugins:[regions]});
    wave.current=instance;
    instance.on('ready',()=>setReady(true));
    instance.on('decode',()=>analysis.regions.forEach((r,i)=>{
      // Visual minimum only: original start/end seconds remain untouched.
      const region=regions.addRegion({id:String(i),start:r.start,end:r.end,
        color:flaws[r.type].color+'55',drag:false,resize:false});
      const element=region.element;if(!element)return;
      const label=`${flaws[r.type].label} · ${timeRange(r.start,r.end)}`;
      element.style.minWidth='4px';
      element.style.maxWidth='100%';
      element.style.borderTop='4px solid '+flaws[r.type].color;
      element.title=label;element.setAttribute('aria-label',label);
      element.setAttribute('role','button');element.tabIndex=0;
      element.addEventListener('keydown',event=>{
        if(event.key==='Enter'||event.key===' '){event.preventDefault();onSelect(i);instance.setTime(r.start);}
      });
    }));
    regions.on('region-clicked',(r,event)=>{event.stopPropagation();onSelect(Number(r.id));instance.setTime(r.start);});
    const error=(e:Error)=>{if(e.name!=='AbortError')setError(e.message);};
    instance.on('error',error);
    return ()=>{instance.destroy();wave.current=null;regionPlugin.current=null;};
  },[analysis,onSelect,source]);
  useEffect(()=>{
    const update=()=>regionPlugin.current?.getRegions().forEach(r=>{
      if(!r.element)return;
      r.element.dataset.selected=String(Number(r.id)===selected);
      r.element.style.visibility=hidden.includes(analysis.regions[Number(r.id)].type)?'hidden':'visible';
      r.element.style.outline=Number(r.id)===selected?'2px solid #e5eff7':'';
    });
    update();return wave.current?.on('ready',update);
  },[selected,analysis,hidden]);
  useEffect(()=>{if(seek!==null)wave.current?.setTime(seek);},[seek]);
  return <section className="timeline"><div className="section-heading"><h2>Your recording</h2><span>{analysis.duration_s.toFixed(2)} seconds · click a marked phrase</span></div>
    <p className="provenance">{analysis.recording_id} · analysis {analysis.analysis_id}</p><div className="region-lanes" aria-label="Flag labels above waveform">{Object.entries(flaws).filter(([type])=>!hidden.includes(type)&&analysis.regions.some(r=>r.type===type)).map(([type,f])=><div className="lane" key={type}><span style={{color:f.color}}>{f.label}</span><div>{analysis.regions.map((r,i)=>r.type===type?<button key={i} aria-pressed={selected===i} title={`${f.label} · ${timeRange(r.start,r.end)}`} style={{borderColor:f.color+'80',color:f.color}} onClick={()=>{onSelect(i);wave.current?.setTime(r.start);}}>{timeRange(r.start,r.end)}</button>:null)}</div></div>)}</div>
    {error&&<p role="alert">Could not load the waveform: {error}</p>}<div ref={box} data-testid="waveform" data-ready={ready}/><div className="time-axis">{Array.from({length:5},(_,i)=><span key={i}>{(analysis.duration_s*i/4).toFixed(0)} s</span>)}</div><audio ref={audio} controls preload="metadata" aria-label="Recording playback"><source src={source?.audio(analysis.recording_id)??`/api/audio/${analysis.recording_id}`}/></audio></section>;
}

export const featureOptions=[{id:'rate',label:'Speed',unit:'syllables/s'},{id:'pitchvar',label:'Pitch variation',unit:'semitones'},
  {id:'loud',label:'Loudness',unit:'relative dB'},{id:'clarity',label:'Clarity',unit:'high-band dB'},{id:'pause',label:'Pauses',unit:'seconds'}];

export function FeatureChart({tracks,feature,selected}:{tracks:Tracks;feature:string;selected:Region|undefined}){
  const element=useRef<HTMLDivElement>(null);
  useEffect(()=>{
    const box=element.current;if(!box)return;
    const x=tracks.words.map(w=>w.i),text=tracks.words.map(w=>w.text);
    const data:Data[]=[
      {x,y:tracks.words.map(w=>w.reference[feature]?.low??null),type:'scatter',mode:'lines',line:{width:0},name:'Reference lower',showlegend:false,hoverinfo:'skip'},
      {x,y:tracks.words.map(w=>w.reference[feature]?.high??null),type:'scatter',mode:'lines',fill:'tonexty',fillcolor:'rgba(96,153,200,.20)',line:{width:0},name:'Reference ±2σ',hoverinfo:'skip'},
      {x,y:tracks.words.map(w=>w.reference[feature]?.mu??null),text,type:'scatter',mode:'lines',line:{color:'#93aec2',width:1,dash:'dot'},name:'Reference median',hovertemplate:`%{text}<br>%{y:${feature==='rate'?'.1f':'.2f'}}<extra>Reference median</extra>`},
      {x,y:tracks.words.map(w=>w.features[feature]??null),text,type:'scatter',mode:'lines+markers',line:{color:'#55d5e8',width:2},marker:{size:4},name:'Yours',hovertemplate:`%{text}<br>%{y:${feature==='rate'?'.1f':'.2f'}}<extra>Yours</extra>`},
    ];
    const layout:Partial<Layout>={height:320,autosize:true,paper_bgcolor:'transparent',plot_bgcolor:'transparent',font:{color:'#b9ccdc',family:'system-ui'},
      margin:{l:64,r:20,t:26,b:58},legend:{orientation:'h',y:1.18},xaxis:{title:{text:'Word in your transcript'},gridcolor:'#20384d',zeroline:false},
      yaxis:{title:{text:featureOptions.find(f=>f.id===feature)?.unit},gridcolor:'#20384d',zeroline:false,tickformat:feature==='rate'?'.1f':'.2f',exponentformat:'none',showexponent:'none'},
      shapes:selected?[{type:'rect',xref:'x',yref:'paper',x0:selected.word_start-.5,x1:selected.word_end+.5,y0:0,y1:1,
        fillcolor:flaws[selected.type].color+'22',line:{width:0},layer:'below'}]:[]};
    const available=tracks.words.some(w=>w.reference[feature]);
    void Plotly.newPlot(box,available?data:data.slice(3),layout,{responsive:true,displayModeBar:false});
    const observer=new ResizeObserver(()=>{void Plotly.Plots.resize(box);});observer.observe(box);
    return ()=>{observer.disconnect();Plotly.purge(box);};
  },[tracks,feature,selected]);
  return <div ref={element} data-testid="feature-chart" className="feature-chart"/>;
}

export function ProgressChart({takes}:{takes:Take[]}){
  const element=useRef<HTMLDivElement>(null);
  useEffect(()=>{
    const box=element.current;if(!box)return;
    const colors=['#55d5e8','#ffb454','#ed89c4','#f87979','#73b8ff','#74d6a4'];
    const data:Data[]=['overall','pace','pitch','pauses','volume','clarity'].map((key,i)=>({
      x:takes.map((_,n)=>n+1),y:takes.map(t=>t.scores[key]),text:takes.map(t=>`Mode ${t.mode} · ${t.recording_id}`),
      name:key,type:'scatter',mode:'lines+markers',line:{color:colors[i]},hovertemplate:'Take %{x}<br>%{text}<br>%{y:.1f}/10<extra>%{fullData.name}</extra>',
    }));
    void Plotly.newPlot(box,data,{height:320,paper_bgcolor:'transparent',plot_bgcolor:'transparent',font:{color:'#b9ccdc'},
      margin:{l:50,r:20,t:30,b:55},xaxis:{title:{text:'Take in upload order'},dtick:1},yaxis:{title:{text:'Score /10'},range:[0,10]},legend:{orientation:'h'}},{responsive:true,displayModeBar:false});
    const observer=new ResizeObserver(()=>{void Plotly.Plots.resize(box);});observer.observe(box);
    return ()=>{observer.disconnect();Plotly.purge(box);};
  },[takes]);
  return <div ref={element} data-testid="progress-chart" className="feature-chart"/>;
}
