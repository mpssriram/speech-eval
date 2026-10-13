import {useEffect,useState} from 'react';
import {Results} from './Results';
import examples from './catalog.js';
import {phraseSegment} from './segments.js';
import type {Analysis,Tracks,ResultSource} from './types';
export function ExampleResults({id,onError}:{id:string;onError:(message:string)=>void}){
 const [data,setData]=useState<{analysis:Analysis;tracks:Tracks;source:ResultSource}|null>(null);
 const example=examples.find(e=>e.id===id);
 useEffect(()=>{
  let cancelled=false;setData(null);
  if(!example){onError('Example not found. Choose a recording from the gallery.');return;}
  const read=async(path:string)=>{const response=await fetch(new URL(path,document.baseURI));if(!response.ok)throw Error('Could not load stored example: '+path);return response.json();};
  void Promise.all([read(example.analysis),read(example.alignment),example.baselineAlignment?read(example.baselineAlignment):Promise.resolve({words:[]})]).then(([analysis,alignment,baseline])=>{
   if(cancelled)return;
   const source:ResultSource={title:example.title,selectedRegion:example.selectedRegion,peaks:example.peaks,
    audio:(rid:string)=>rid===analysis.recording_id?example.audio:example.baselineAudio||'',
    segments:Object.fromEntries(analysis.regions.map((r:Analysis['regions'][number],i:number)=>{const span=phraseSegment(r,alignment.words,baseline.words);return [i,span?{...span,recording_id:analysis.reference.baseline_recording_id}:null];}))};
   setData({analysis,tracks:{words:alignment.words.map((w:Tracks['words'][number])=>({...w,features:{},reference:{}})),frames:{}},source});
  }).catch(e=>{if(!cancelled)onError(e.message);});
  return ()=>{cancelled=true;};
 },[id,example,onError]);
 if(!data)return <p role="status">Loading the stored recording and its evidence…</p>;
 return <div id="results"><Results key={id} {...data} aid={id} onError={onError}/><a id="json-link" href={example?.analysis} download={data.analysis.analysis_id+'.json'}>View original analysis JSON</a></div>;
}
