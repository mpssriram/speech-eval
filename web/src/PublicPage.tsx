import {useEffect,useRef,useState} from 'react';
import {ExampleResults} from './ExampleResults';
import examples from './catalog.js';
import gallery from './gallery';
import {navigate} from './routes';
const repo='https://github.com/mpssriram/speech-eval';
const command='git clone '+repo+'.git && cd speech-eval && make up';
function External({href,children}:{href:string;children:React.ReactNode}){return <a href={href} target="_blank" rel="noopener noreferrer">{children}</a>;}
export function SiteFooter(){return <footer className="site-footer"><nav aria-label="Project resources"><External href={repo}>GitHub</External><External href="https://drive.google.com/file/d/1rDbbPMKORv0nnQ-QnmbrQXIg1mqktvTm/view">Dataset (Drive)</External><External href={repo+'/blob/main/docs/report/report.pdf'}>Report</External><External href={repo+'/blob/main/LICENSE'}>Code: MIT</External><External href={repo+'/blob/main/LICENSE-DATA'}>Labels, docs and my recordings: CC BY 4.0</External><External href={repo+'/blob/main/docs/DATASET.md#sources-rights-and-attribution'}>Reader audio: public domain</External></nav><span>Sriram MPS, IIT Mandi</span></footer>;}
function Brand(){return <a className="brand" href="#/" aria-label="Speech Eval home"><svg viewBox="0 0 40 32" aria-hidden="true"><path d="M3 13v6m7-13v20m7-25v30m7-21v12m7-18v24m6-16v8"/></svg>Speech-Eval</a>;}
export function StaticUploadModal(){
 const dialog=useRef<HTMLDialogElement>(null),[copied,setCopied]=useState(false),[copyError,setCopyError]=useState('');
 useEffect(()=>{const element=dialog.current!;element.showModal();return ()=>element.close();},[]);
 function close(){navigate('/');}
 async function copy(){try{await navigator.clipboard.writeText(command);setCopied(true);setCopyError('');}catch{setCopyError('Select the command below and copy it.');}}
 return <dialog ref={dialog} className="upload-modal" aria-labelledby="local-analysis-title" onCancel={event=>{event.preventDefault();close();}} onClick={event=>{const box=dialog.current!.getBoundingClientRect();if(event.target===dialog.current&&(event.clientX<box.left||event.clientX>box.right||event.clientY<box.top||event.clientY>box.bottom))close();}}>
  <h2 id="local-analysis-title">Live analysis runs locally</h2>
  <p>This free online demo is static: it shows precomputed, frozen results (byte-identical to the reported numbers) and never uploads your voice. Analysis needs MFA, Praat and a 16.8 GB Docker image, which free hosting cannot run.</p>
  <div className="command"><pre><code>{command}</code></pre><button type="button" onClick={()=>void copy()}>{copied?'Copied':'Copy command'}</button></div>
  <p>Then open <a href="http://localhost:8080" target="_blank" rel="noopener noreferrer">http://localhost:8080</a>.</p>
  {copyError&&<p role="status">{copyError}</p>}
  <div className="modal-actions"><a className="primary-action" href="#/?examples">Explore an example</a><button onClick={close} autoFocus>Close</button></div>
 </dialog>;
}
export function Landing(){
 return <div className="landing"><section className="hero"><div><h1>Speech-Eval</h1><h2>Finds speech delivery flaws: what, where and why</h2><p>It marks the exact words and times and explains each flag with measured numbers, compared with expert readers or your own earlier take.</p><div className="hero-actions"><a className="primary-action" href="#/upload">Upload a recording</a><a className="secondary-action" href="#/?examples">Explore an example</a></div></div><div className="speech-preview" aria-label="An exact word boundary in the Gettysburg example"><div className="preview-wave" aria-hidden="true">{[9,16,26,40,29,55,34,49,20,12,5,4,4,4,4,6,25,42,56,30,22,38,17,8].map((height,i)=><i key={i} style={{height:height+'px'}}/>)}</div><p>“larger <span>|</span> sense”</p><span>An awkward pause, grounded in the words.</span><a href={'#/example/'+gallery[0].id}>Hear this example</a></div></section>
 <section className="how-it-works"><h2>How it works</h2><ol><li><strong>Align words (MFA)</strong><span>Locate each spoken word in time.</span></li><li><strong>Compare with a reference</strong><span>Expert readers, your earlier take, or speaker norms.</span></li><li><strong>Explain with numbers</strong><span>See what was flagged, where and why.</span></li></ol></section>
 <section className="mode-cards" aria-label="Comparison modes"><article><h3>Mode A</h3><p>Expert readers</p></article><article><h3>Mode B</h3><p>Your earlier take</p></article><article><h3>Mode C</h3><p>Speaker norms; heuristic tips are not scored.</p></article></section>
 <section id="examples" className="example-gallery"><div className="section-heading"><h2>Examples</h2><span>Frozen results. Every stored flag remains visible.</span></div><div>{gallery.map(e=><a className="example-card" title={e.tooltip||undefined} key={e.id} href={'#/example/'+e.id}><div><h3>{e.title.split(' · ')[0]}</h3><span className="gallery-mode">Mode {e.mode}</span></div><p>{e.description}</p><small>{e.flags} {e.flags===1?'flag':'flags'}</small></a>)}</div></section>
 </div>;
}
export function PublicPage({route,staticDemo=false}:{route:string;staticDemo?:boolean}){
 const [error,setError]=useState('');
 const path=route.split('?')[0],id=path.startsWith('/example/')?decodeURIComponent(path.split('/')[2]):'';
 const example=examples.find(e=>e.id===id);
 const home=!id;
 useEffect(()=>{setError('');if(route.includes('?examples'))requestAnimationFrame(()=>document.getElementById('examples')?.scrollIntoView({block:'start'}));else window.scrollTo(0,0);},[route]);
 return <div className={'shell '+(home?'landing-shell':'')}><header className="app-header public-header"><Brand/>{id?<><div className="header-picker"><label htmlFor="example">Recording / take</label><select id="example" value={id} onChange={e=>navigate('/example/'+e.target.value)}>{examples.map(e=><option key={e.id} value={e.id}>{e.title}</option>)}</select></div><div className="mode-control" role="group" aria-label="Analysis mode">{['A','B','C'].map(mode=><button key={mode} aria-pressed={example?.title.endsWith('Mode '+mode)} disabled={!examples.some(e=>e.alignment===example?.alignment&&e.title.endsWith('Mode '+mode))} onClick={()=>{const match=examples.find(e=>e.alignment===example?.alignment&&e.title.endsWith('Mode '+mode));if(match)navigate('/example/'+match.id);}}>Mode {mode}</button>)}</div><a className="secondary-action" href="#/upload">New analysis</a></>:<nav><a href="#/?examples">Examples</a><a href="#/upload">Upload</a></nav>}</header>
 <main>{id?<><a className="back-link" href="#/?examples">Back to examples</a>{staticDemo&&<p id="banner" className="banner">Precomputed demo. Live analysis of your own audio runs locally with Docker; see the GitHub README.</p>}{error?<p role="alert">{error}</p>:<ExampleResults id={id} onError={setError}/>}</>:<Landing/>}</main>
 <SiteFooter/>{staticDemo&&path==='/upload'&&<StaticUploadModal/>}</div>;
}
