import {useEffect,useRef,useState} from 'react';
import WaveSurfer from 'wavesurfer.js';
import Regions from 'wavesurfer.js/dist/plugins/regions.esm.js';
import Plotly from 'plotly.js-basic-dist';
import type {Data,Layout} from 'plotly.js';
import {flaws,type Analysis,type Region,type Tracks,type Take} from './types';

export function Waveform({analysis,onSelect,seek,selected}:{analysis:Analysis;onSelect:(index:number)=>void;seek:number|null;selected:number}){
  const box=useRef<HTMLDivElement>(null);const audio=useRef<HTMLAudioElement>(null);const wave=useRef<WaveSurfer|null>(null);
  const regionPlugin=useRef<ReturnType<typeof Regions.create>|null>(null);
  const [error,setError]=useState('');
  const [ready,setReady]=useState(false);
  useEffect(()=>{
    if(!box.current||!audio.current)return;
    const regions=Regions.create();
    regionPlugin.current=regions;setError('');setReady(false);
    const instance=WaveSurfer.create({container:box.current,media:audio.current,url:`/api/audio/${analysis.recording_id}`,
      waveColor:'#63869f',progressColor:'#55d5e8',cursorColor:'#e5eff7',height:116,barWidth:2,barGap:2,normalize:false,plugins:[regions]});
    wave.current=instance;
    instance.on('ready',()=>setReady(true));
    instance.on('decode',()=>analysis.regions.forEach((r,i)=>regions.addRegion({id:String(i),start:r.start,end:r.end,
      color:flaws[r.type].color+'55',content:flaws[r.type].label,drag:false,resize:false})));
    regions.on('region-clicked',(r,event)=>{event.stopPropagation();onSelect(Number(r.id));instance.setTime(r.start);});
    const error=(e:Error)=>{if(e.name!=='AbortError')setError(e.message);};
    instance.on('error',error);
    return ()=>{instance.destroy();wave.current=null;regionPlugin.current=null;};
  },[analysis,onSelect]);
  useEffect(()=>{
    const update=()=>regionPlugin.current?.getRegions().forEach(r=>{
      if(!r.element)return;
      r.element.dataset.selected=String(Number(r.id)===selected);
      r.element.style.outline=Number(r.id)===selected?'2px solid #e5eff7':'';
      r.element.style.minWidth='3px';
    });
    update();return wave.current?.on('ready',update);
  },[selected,analysis]);
  useEffect(()=>{if(seek!==null)wave.current?.setTime(seek);},[seek]);
  return <section className="timeline"><div className="section-heading"><h2>Your recording</h2><span>{analysis.duration_s.toFixed(1)} seconds · click a marked phrase</span></div>
    {error&&<p role="alert">Could not load the waveform: {error}</p>}<div ref={box} data-testid="waveform" data-ready={ready}/><audio ref={audio} controls preload="metadata" aria-label="Recording playback"/></section>;
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
      {x,y:tracks.words.map(w=>w.reference[feature]?.mu??null),text,type:'scatter',mode:'lines',line:{color:'#93aec2',width:1,dash:'dot'},name:'Reference median'},
      {x,y:tracks.words.map(w=>w.features[feature]??null),text,type:'scatter',mode:'lines+markers',line:{color:'#55d5e8',width:2},marker:{size:4},name:'Yours',hovertemplate:'%{text}<br>%{y:.2f}<extra>Yours</extra>'},
    ];
    const layout:Partial<Layout>={height:320,autosize:true,paper_bgcolor:'transparent',plot_bgcolor:'transparent',font:{color:'#b9ccdc',family:'system-ui'},
      margin:{l:64,r:20,t:26,b:58},legend:{orientation:'h',y:1.18},xaxis:{title:{text:'Word in your transcript'},gridcolor:'#20384d',zeroline:false},
      yaxis:{title:{text:featureOptions.find(f=>f.id===feature)?.unit},gridcolor:'#20384d',zeroline:false},
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
