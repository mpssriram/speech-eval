export const flaws = {
  rushing:{label:'Rushing',color:'#ffb454'}, dragging:{label:'Dragging',color:'#a5a2ff'},
  monotone:{label:'Monotone',color:'#ed89c4'}, too_quiet:{label:'Too quiet',color:'#73b8ff'},
  awkward_pause:{label:'Awkward pause',color:'#f87979'}, missing_pause:{label:'Missing pause',color:'#e2d46b'},
  mumbling:{label:'Mumbling',color:'#74d6a4'},
};
export type FlawType=keyof typeof flaws;
export type Region={type:FlawType;start:number;end:number;word_start:number;word_end:number;severity:number;explanation:string;evidence?:Record<string,number|string>;tags?:string[];display_explanation?:string};
export type Analysis={analysis_id:string;recording_id:string;text_id:string;mode:string;duration_s:number;regions:Region[];
  reference:{baseline_recording_id?:string;kind:string};scores:Record<string,number>;warnings:unknown[];
  key_moments:{kind:string;passed:boolean;message:string}[];
  progress:Record<string,{previous:{count:number;duration_s:number};current:{count:number;duration_s:number}}>|null};
export type Word={i:number;text:string;start:number;end:number;features:Record<string,number|null>;
  reference:Record<string,{mu:number|null;low:number|null;high:number|null;sigma_transformed:number}>};
export type Tracks={words:Word[];frames:Record<string,(number|null)[]>};
export type Job={analysis_id:string;status:'queued'|'running'|'done'|'error';analysis?:Analysis;error?:string};
export type TextOption={text_id:string;title:string;canonical_transcript:string};
export type Take={analysis_id:string;recording_id:string;scores:Record<string,number>;mode:string};
export type Segment={recording_id:string;start:number;end:number};
export async function request<T>(url:string,options?:RequestInit):Promise<T>{
  const response=await fetch(url,options);
  const data=await response.json();
  if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Request failed. Please retry.');
  return data as T;
}

export type ResultSource={title:string;selectedRegion?:number;segments:Record<number,Segment|null>;audio:(id:string)=>string;peaks?:number[]};
