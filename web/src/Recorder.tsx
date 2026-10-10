import {useEffect,useRef,useState} from 'react';
import {Button} from '@mantine/core';

/** Keep microphone, meter and recording resources scoped to this form. */
export function Recorder({onFile,onError}:{onFile:(file:File)=>void;onError:(message:string)=>void}){
  const [recording,setRecording]=useState(false),[starting,setStarting]=useState(false);
  const [seconds,setSeconds]=useState(0),[level,setLevel]=useState(0);
  const recorder=useRef<MediaRecorder|null>(null),stream=useRef<MediaStream|null>(null);
  const context=useRef<AudioContext|null>(null),frame=useRef(0),mounted=useRef(true);
  const timer=useRef<ReturnType<typeof setInterval>|null>(null);
  function release(){
    if(timer.current)clearInterval(timer.current);timer.current=null;
    cancelAnimationFrame(frame.current);stream.current?.getTracks().forEach(t=>t.stop());stream.current=null;
    if(context.current)void context.current.close();context.current=null;
  }
  useEffect(()=>{mounted.current=true;return ()=>{
    mounted.current=false;
    if(recorder.current?.state==='recording')recorder.current.stop();
    release();
  };},[]);
  async function start(){
    setStarting(true);
    try{
      if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder)throw new Error('Browser recording is unavailable. Upload an audio file instead.');
      const input=await navigator.mediaDevices.getUserMedia({audio:true});
      if(!mounted.current){input.getTracks().forEach(t=>t.stop());return;}
      stream.current=input;
      const mime=['audio/webm;codecs=opus','audio/webm','audio/ogg;codecs=opus'].find(t=>MediaRecorder.isTypeSupported(t));
      const media=new MediaRecorder(input,mime?{mimeType:mime}:undefined),chunks:Blob[]=[];
      recorder.current=media;
      media.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};
      media.onstop=()=>{
        release();
        if(mounted.current){
          setRecording(false);setLevel(0);
          const type=media.mimeType,extension=type.includes('ogg')?'ogg':type.includes('mp4')?'m4a':'webm';
          if(chunks.length)onFile(new File(chunks,`browser_take.${extension}`,{type}));
        }
      };
      media.onerror=()=>{release();setRecording(false);onError('Recording failed. Please try again or upload a file.');};
      const ac=new AudioContext();context.current=ac;
      const analyser=ac.createAnalyser();ac.createMediaStreamSource(input).connect(analyser);
      const samples=new Uint8Array(analyser.fftSize);
      function meter(){analyser.getByteTimeDomainData(samples);setLevel(Math.min(1,Math.sqrt(samples.reduce((n,v)=>n+((v-128)/128)**2,0)/samples.length)*5));frame.current=requestAnimationFrame(meter);}
      media.start();meter();setSeconds(0);setRecording(true);
      timer.current=setInterval(()=>setSeconds(s=>{if(s>=599&&media.state==='recording')media.stop();return s+1;}),1000);
    }catch(e){release();onError((e as Error).message);}finally{if(mounted.current)setStarting(false);}
  }
  return <div className="recorder"><div className="playback">
    <Button type="button" variant="light" loading={starting} onClick={()=>recording?recorder.current?.stop():void start()}>
      {recording?'Stop recording':'Record in browser'}
    </Button><span role="status">{recording?`Recording · ${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`:'Record a take using your microphone'}</span>
  </div>{recording&&<meter aria-label="Microphone level" min={0} max={1} value={level}/>}</div>;
}
