import './style.css';
import examples from './catalog.js';
import { phraseSegment } from './segments.js';
const colours={rushing:'#d08226',dragging:'#8075cc',monotone:'#c05e99',too_quiet:'#4785c5',awkward_pause:'#d35c60',missing_pause:'#a5952b',mumbling:'#348a67'};
const name=t=>t.replaceAll('_',' ');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const app=document.querySelector('#app');
let analysis,words,baseline,example,selected=0,loadId=0,stopAt=null;
app.innerHTML=`<header><a class="brand" href="./">Speech-Eval<span>Speech delivery analytics</span></a><nav id="links"></nav></header>
<main><div id="banner" class="banner">Precomputed demo · Stored results only</div>
<div class="intro"><div><h1>Hear what changed.</h1><p>Explore delivery flags, their timing and the measured evidence.</p></div><div><button id="upload" disabled title="This demo contains stored analyses only.">Upload audio</button><p id="upload-help" class="small">Audio upload is unavailable in this precomputed demo.</p></div></div>
<section class="picker"><label for="example">Choose a recording and comparison</label><select id="example"></select><p id="context" class="small"></p></section>
<div id="error" role="alert"></div><div id="results" hidden>
<section class="recording"><div class="section-head"><h2 id="title"></h2><span id="mode" class="pill"></span></div><p id="provenance" class="small"></p><div id="scores" class="scores"></div>
<h3>Recording timeline</h3><p class="small">Select a coloured interval or a flag below. Intervals use the stored start and end times.</p><div id="timeline" class="timeline" aria-label="Flag timeline"></div><div class="scale"><span>0 s</span><span id="duration"></span></div><div id="legend" class="legend"></div>
<label class="audio-label" for="participant-audio">Participant recording</label><audio id="participant-audio" controls preload="metadata"></audio></section>
<div class="details"><section class="flags"><div class="section-head"><h2>Stored flags</h2><span id="flag-count"></span></div><div id="regions"></div></section>
<section class="evidence"><h2>Why this region?</h2><h3 id="region-title"></h3><p id="explanation" class="explanation"></p><div id="numbers"></div><div class="playback"><button id="play-participant">Play participant phrase</button><button id="play-baseline">Play same words in baseline</button></div><p id="pair-note" class="small"></p><label class="audio-label" for="baseline-audio">Baseline recording</label><audio id="baseline-audio" controls preload="metadata"></audio><details><summary>Transcript with selected words</summary><p id="transcript" class="transcript"></p></details></section></div>
<section class="additional"><h2>Comparison details</h2><div id="comparison"></div><div id="warnings"></div><p class="small">Experimental delivery benchmark. Flags may be wrong. Rubric scores are designed penalties, not an independently validated speaking-quality scale. Genuine-take labels were confirmed by the recorder; independent ratings and a human alignment spot-check are absent.</p><a id="json-link">View original analysis JSON</a></section></div>
<footer>Sriram MPS, IIT Mandi · Frozen v1 results · Playback files only; no analysis service runs here.</footer></main>`;
const $=id=>document.getElementById(id);
$('example').innerHTML=examples.map(e=>`<option value="${esc(e.id)}">${esc(e.title)}</option>`).join('');
const defaultId=examples.find(e=>e.default)?.id||examples[0]?.id;
$('example').value=defaultId||'';
$('example').addEventListener('change',()=>load($('example').value));
for(const id of ['participant-audio','baseline-audio']){
 $(id).addEventListener('timeupdate',()=>{if(stopAt?.id===id&&$(id).currentTime>=stopAt.end){$(id).pause();stopAt=null;}});
 $(id).addEventListener('play',()=>{const other=id==='participant-audio'?'baseline-audio':'participant-audio';$(other).pause();});
 $(id).addEventListener('seeking',()=>{if(stopAt?.id===id&&$(id).currentTime>stopAt.end)stopAt=null;});
}
async function file(path){const res=await fetch(new URL(path,document.baseURI));if(!res.ok)throw Error(`Could not load stored file: ${path}`);return res.json();}
async function load(id){
 const token=++loadId;$('error').textContent='';$('results').hidden=true;stopAt=null;
 for(const a of ['participant-audio','baseline-audio'])$(a).pause();
 example=examples.find(e=>e.id===id);if(!example)return;
 try{
  const [a,w,b]=await Promise.all([file(example.analysis),file(example.alignment),example.baselineAlignment?file(example.baselineAlignment):Promise.resolve({words:[]})]);
  if(token!==loadId)return;
  analysis=a;words=w.words;baseline=b.words;
  selected=example.selectedRegion??0;
  $('title').textContent=example.title;$('mode').textContent=`Mode ${a.mode}`;
  $('context').textContent=example.note;
  $('provenance').textContent=`${a.recording_id} · ${a.duration_s.toFixed(2)} s · analysis ${a.analysis_id}`;
  $('scores').innerHTML=Object.entries(a.scores).map(([k,v])=>`<div><span>${esc(name(k))}</span><strong>${esc(v)}<small> / 10</small></strong></div>`).join('');
  const peaks=example.peaks||[];
  $('timeline').innerHTML=`<svg viewBox="0 0 1000 100" preserveAspectRatio="none" aria-hidden="true">${peaks.map((v,i)=>`<line x1="${i*1000/peaks.length}" x2="${i*1000/peaks.length}" y1="${50-v*42}" y2="${50+v*42}" stroke="#b0bbc9" stroke-width="2"/>`).join('')}</svg>`+
  a.regions.map((v,i)=>`<button class="interval" data-region="${i}" aria-label="${esc(name(v.type))} ${v.start.toFixed(2)} to ${v.end.toFixed(2)} seconds" title="${esc(name(v.type))}: ${v.start.toFixed(2)}–${v.end.toFixed(2)} s" style="left:${v.start/a.duration_s*100}%;width:${Math.max(.08,(v.end-v.start)/a.duration_s*100)}%;background:${colours[v.type]}"></button>`).join('');
  $('duration').textContent=`${a.duration_s.toFixed(2)} s`;
  $('legend').innerHTML=Object.entries(colours).map(([k,v])=>`<span><i style="background:${v}"></i>${esc(name(k))}</span>`).join('');
  $('participant-audio').src=example.audio||'';$('baseline-audio').src=example.baselineAudio||'';
  $('flag-count').textContent=`${a.regions.length} flags`;
  $('regions').innerHTML=a.regions.length?a.regions.map((v,i)=>`<button class="region" data-region="${i}" style="border-left-color:${colours[v.type]}"><strong>${esc(name(v.type))}</strong><span>${v.start.toFixed(2)}–${v.end.toFixed(2)} s</span><small>Severity ${v.severity}</small></button>`).join(''):'<p>No stored delivery flags for this recording.</p>';
  document.querySelectorAll('[data-region]').forEach(el=>el.addEventListener('click',()=>select(Number(el.dataset.region))));
  $('json-link').href=example.analysis;$('json-link').download=`${a.analysis_id}.json`;
  $('comparison').innerHTML=`<p>Reference: ${esc(a.reference.kind)}${a.reference.baseline_recording_id?' — '+esc(a.reference.baseline_recording_id):''}</p>`+
   (a.progress?'<table><caption>Stored rehearsal counts and durations</caption><thead><tr><th>Flaw</th><th>Previous</th><th>Current</th></tr></thead><tbody>'+Object.entries(a.progress).map(([k,v])=>`<tr><th>${esc(name(k))}</th><td>${v.previous.count} flags / ${v.previous.duration_s} s</td><td>${v.current.count} flags / ${v.current.duration_s} s</td></tr>`).join('')+'</tbody></table>':'')+
   (a.key_moments?.length?'<h3>Heuristic key-moment checks</h3>'+a.key_moments.map(k=>`<p>${k.passed?'Passed':'Flagged'}: ${esc(k.message)}</p>`).join(''):'');
  $('warnings').innerHTML=a.warnings?.length?`<details><summary>${a.warnings.length} stored warnings</summary><pre>${esc(JSON.stringify(a.warnings,null,2))}</pre></details>`:'';
  $('results').hidden=false;select(selected);
 }catch(err){$('error').textContent=err.message;}
}
function select(i){
 selected=i;const v=analysis.regions[i];
 document.querySelectorAll('[data-region]').forEach(el=>el.setAttribute('aria-pressed',String(Number(el.dataset.region)===i)));
 $('region-title').textContent=v?`${name(v.type)} · ${v.start.toFixed(2)}–${v.end.toFixed(2)} s`:'No region selected';
 $('explanation').textContent=v?.explanation||'Select a recording with flags to inspect its measured evidence.';
 $('numbers').innerHTML=v?.evidence?`<dl>${Object.entries(v.evidence).map(([k,val])=>`<div><dt>${esc(name(k))}</dt><dd>${esc(val)}</dd></div>`).join('')}</dl>`:'';
 const pair=v?phraseSegment(v,words,baseline):null;
 $('play-participant').disabled=!v||!example.audio;
 $('play-baseline').disabled=!pair||!example.baselineAudio;
 $('baseline-audio').hidden=!example.baselineAudio;
 $('pair-note').textContent=analysis.mode==='C'?'Mode C uses norms and has no same-text baseline.':pair?'The same aligned words are selected in both recordings. Playback includes a small context margin.':'These words do not have an exact match in the stored baseline; paired phrase playback is unavailable.';
 $('transcript').innerHTML=words.map(w=>v&&w.i>=v.word_start&&w.i<=v.word_end?`<mark>${esc(w.text)}</mark>`:esc(w.text)).join(' ');
}
async function play(id,span){
 if(!span)return;
 const audio=$(id);stopAt={id,end:span.end+.25};audio.currentTime=Math.max(0,span.start-.25);
 try{await audio.play();}catch(e){$('error').textContent=`Playback could not start: ${e.message}`;}
}
$('play-participant').addEventListener('click',()=>{const v=analysis.regions[selected];if(v){const phrase=words.filter(w=>w.i>=v.word_start&&w.i<=v.word_end);play('participant-audio',{start:Math.min(v.start,phrase[0]?.start??v.start),end:Math.max(v.end,phrase.at(-1)?.end??v.end)});}});
$('play-baseline').addEventListener('click',()=>play('baseline-audio',phraseSegment(analysis.regions[selected],words,baseline)));
if(defaultId)load(defaultId);else $('error').textContent='No precomputed examples have been packaged yet.';
