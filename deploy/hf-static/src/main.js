import './style.css';
import examples from './catalog.js';
import { phraseSegment } from './segments.js';
const colours={rushing:'#d08226',dragging:'#8075cc',monotone:'#c05e99',too_quiet:'#4785c5',awkward_pause:'#d35c60',missing_pause:'#a5952b',mumbling:'#348a67'};
const name=t=>t.replaceAll('_',' ');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const app=document.querySelector('#app');
let analysis,words,baseline,example,selected=0,loadId=0,stopAt=null,hiddenTypes=new Set();
app.innerHTML=`<header><div class="header-inner"><a class="brand" href="./"><svg viewBox="0 0 40 32" aria-hidden="true"><path d="M3 13v6m7-13v20m7-25v30m7-21v12m7-18v24m6-16v8"/></svg>Speech-Eval</a><div class="header-picker"><label for="example">Recording / take</label><select id="example"></select></div><div id="mode-control" class="mode-control" role="group" aria-label="Analysis mode">${['A','B','C'].map(m=>`<button data-mode="${m}" aria-pressed="false">Mode ${m}</button>`).join('')}</div><button id="upload" disabled aria-describedby="banner" title="Precomputed demo. Live analysis of your own audio runs locally with Docker; see the GitHub README.">New analysis</button></div></header>
<main><div id="banner" class="banner">Precomputed demo. Live analysis of your own audio runs locally with Docker; see the GitHub README.</div><nav id="links"><a href="https://github.com/mpssriram/speech-eval">GitHub ↗</a><a href="https://github.com/mpssriram/speech-eval/blob/main/docs/DATASET.md">Dataset ↗</a><a href="https://github.com/mpssriram/speech-eval/blob/main/docs/report/report.pdf">Report ↗</a></nav>
<div id="error" role="alert"></div><div id="loading" role="status">Loading the stored recording and its evidence…</div><div id="results" hidden>
<div class="results-heading"><div><h1 id="title"></h1><p id="context" class="small"></p></div><span id="mode" class="pill"></span></div><section id="scores" class="score-card" aria-label="Rubric scores"></section>
<div class="workspace"><div class="recording-column"><section class="recording"><div class="section-head"><h2>Your recording</h2><span id="duration"></span></div><p id="provenance" class="small"></p><div id="lanes" class="region-lanes" aria-label="Flag labels above waveform"></div><div id="timeline" class="timeline" aria-label="Flag timeline"></div><div id="axis" class="time-axis"></div><label class="audio-label" for="participant-audio">Participant recording</label><audio id="participant-audio" aria-label="Recording playback" controls preload="metadata"></audio></section>
<section class="transcript-card"><h2>Transcript</h2><p class="small">Highlighted words belong to the selected phrase.</p><details><summary>Transcript with selected words</summary><p id="transcript" class="transcript"></p></details></section></div>
<section class="flags"><div class="section-head"><h2>Flagged phrases</h2><span id="flag-count"></span></div><div id="legend" class="legend" aria-label="Filter flagged phrases"></div><p id="filter-empty" hidden>All flaw types are hidden. Select a filter to show its phrases.</p><div id="regions" class="flaw-list"></div><label class="audio-label" for="baseline-audio">Baseline recording</label><audio id="baseline-audio" aria-label="Baseline recording playback" controls preload="metadata"></audio></section></div>
<section id="tips" class="tips" hidden><h2>Heuristic tips (not scored)</h2><div id="key-moments"></div></section><section class="additional"><h2>Comparison details</h2><div id="comparison"></div><div id="warnings"></div><p class="small">Experimental delivery benchmark. Flags may be wrong. Rubric scores are designed penalties, not an independently validated speaking-quality scale. Genuine-take labels were confirmed by the recorder; independent ratings and a human alignment spot-check are absent.</p><a id="json-link">View original analysis JSON</a></section></div>
<footer>Sriram MPS, IIT Mandi · Frozen v1 results · Playback files only; no analysis service runs here.</footer></main>`;
const $=id=>document.getElementById(id);
$('example').innerHTML=examples.map(e=>`<option value="${esc(e.id)}">${esc(e.title)}</option>`).join('');
const defaultId=examples.find(e=>e.default)?.id||examples[0]?.id;
$('example').value=defaultId||'';
$('example').addEventListener('change',()=>load($('example').value));
for(const id of ['participant-audio','baseline-audio']){
 $(id).addEventListener('timeupdate',()=>{if(id==='participant-audio'&&analysis)$('playhead').style.left=`${Math.min(100,$(id).currentTime/analysis.duration_s*100)}%`;if(stopAt?.id===id&&$(id).currentTime>=stopAt.end){$(id).pause();stopAt=null;}});
 $(id).addEventListener('play',()=>{const other=id==='participant-audio'?'baseline-audio':'participant-audio';$(other).pause();});
 $(id).addEventListener('seeking',()=>{if(stopAt?.id===id&&$(id).currentTime>stopAt.end)stopAt=null;});
}
async function file(path){const res=await fetch(new URL(path,document.baseURI));if(!res.ok)throw Error(`Could not load stored file: ${path}`);return res.json();}
async function load(id){
 const token=++loadId;$('error').textContent='';$('results').hidden=true;$('loading').hidden=false;hiddenTypes.clear();stopAt=null;
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
  const groups={pace:['rushing','dragging'],pitch:['monotone'],pauses:['awkward_pause','missing_pause'],volume:['too_quiet'],clarity:['mumbling']};
  $('scores').innerHTML=`<div class="overall"><span>Overall score</span><strong>${esc(a.scores.overall)}<small>/10</small></strong><p class="small">Delivery comparison</p></div><div class="categories">${Object.entries(groups).map(([k,types])=>{const count=a.regions.filter(r=>types.includes(r.type)).length;return `<div><span>${k[0].toUpperCase()+k.slice(1)}</span><meter min="0" max="10" value="${a.scores[k]}" aria-label="${k} score"></meter><strong>${esc(a.scores[k])}<small>/10</small></strong><p>${count?count+' flagged '+(count===1?'region':'regions'):'No penalty'}</p></div>`}).join('')}</div>`;
  document.querySelectorAll('[data-mode]').forEach(el=>{el.setAttribute('aria-pressed',String(el.dataset.mode===a.mode));el.disabled=!examples.some(e=>e.alignment===example.alignment&&e.title.endsWith(`Mode ${el.dataset.mode}`));});
  const peaks=example.peaks||[];
  $('timeline').innerHTML=`<svg viewBox="0 0 1000 180" preserveAspectRatio="none" aria-hidden="true">${peaks.map((v,i)=>`<line x1="${i*1000/peaks.length}" x2="${i*1000/peaks.length}" y1="${90-v*78}" y2="${90+v*78}" stroke="#789bb8" stroke-width="2"/>`).join('')}</svg>`+
  a.regions.map((v,i)=>`<button class="interval" data-region="${i}" data-type="${v.type}" aria-label="${esc(name(v.type))} ${v.start.toFixed(2)} to ${v.end.toFixed(2)} seconds" title="${esc(name(v.type))}: ${v.start.toFixed(2)}–${v.end.toFixed(2)} s" style="left:${v.start/a.duration_s*100}%;width:${(v.end-v.start)/a.duration_s*100}%;background:${colours[v.type]}"></button>`).join('')+'<span id="playhead" class="playhead" aria-hidden="true"></span>';
  $('lanes').innerHTML=Object.entries(colours).filter(([type])=>a.regions.some(r=>r.type===type)).map(([type,color])=>`<div class="lane" data-type="${type}"><span><i style="background:${color}"></i>${esc(name(type))}</span><div>${a.regions.map((r,i)=>r.type===type?`<button data-region="${i}" title="${esc(name(type))} · ${r.start.toFixed(2)}–${r.end.toFixed(2)} s" style="border-color:${color}">${r.start.toFixed(2)}–${r.end.toFixed(2)} s</button>`:'').join('')}</div></div>`).join('');
  $('axis').innerHTML=Array.from({length:5},(_,i)=>`<span>${(a.duration_s*i/4).toFixed(0)} s</span>`).join('');
  $('duration').textContent=`${a.duration_s.toFixed(2)} s`;
  $('legend').innerHTML=Object.entries(colours).map(([k,v])=>`<button data-filter="${k}" aria-pressed="true"><i style="background:${v}"></i>${esc(name(k))}</button>`).join('');
  $('participant-audio').src=example.audio||'';$('baseline-audio').src=example.baselineAudio||'';
  $('flag-count').textContent=`${a.regions.length} detected regions · sorted by time`;
  const decorate=text=>String(text??'').split(/(>?[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)/g).map(part=>/\d/.test(part)?`<strong class="number">${esc(part)}</strong>`:esc(part)).join('');
  $('regions').innerHTML=a.regions.length?a.regions.map((v,i)=>({v,i})).sort((x,y)=>x.v.start-y.v.start).map(({v,i})=>{
    const pair=phraseSegment(v,words,baseline),phrase=words.filter(w=>w.i>=v.word_start&&w.i<=v.word_end).map(w=>w.text).join(' ');
    return `<article class="flaw-card" data-card="${i}" data-type="${v.type}" style="border-left-color:${colours[v.type]}"><button class="region" data-region="${i}"><strong class="type-chip"><i style="background:${colours[v.type]}"></i>${esc(name(v.type))}</strong><span>${v.start.toFixed(2)}–${v.end.toFixed(2)} s</span></button><div class="severity" aria-label="Severity ${v.severity} of 5">${'●'.repeat(v.severity)}${'○'.repeat(5-v.severity)}<span>Severity ${v.severity}/5</span></div><blockquote>${esc(phrase)}</blockquote><p class="explanation">${decorate(v.explanation)}</p><div class="playback"><button class="play-yours" data-play="${i}" aria-label="Yours" ${!example.audio?'disabled':''}>Yours</button><button class="play-baseline" data-play="${i}" aria-label="Baseline (same words)" ${!pair||!example.baselineAudio?'disabled':''}>Baseline (same words)</button></div><p class="pair-note small">${a.mode==='C'?'Mode C uses norms and has no same-text baseline.':pair?'The same aligned words are selected in both recordings. Playback includes a small context margin.':'These words do not have an exact match in the stored baseline; paired phrase playback is unavailable.'}</p><details class="numbers"><summary>Measured values</summary><dl>${Object.entries(v.evidence||{}).map(([k,val])=>`<div><dt>${esc(name(k))}</dt><dd>${esc(val)}</dd></div>`).join('')}</dl></details></article>`;
  }).join(''):`<div class="empty"><h3 id="region-title">No region selected</h3><p id="explanation">No stored delivery flags for this recording.</p><button id="play-participant" disabled>Yours</button><button id="play-baseline" disabled>Baseline (same words)</button><p id="pair-note" class="small">${a.mode==='C'?'Mode C uses norms and has no same-text baseline.':'Select a recording with flags to inspect its measured evidence.'}</p></div>`;
  document.querySelectorAll('[data-region]').forEach(el=>el.addEventListener('click',()=>select(Number(el.dataset.region))));
  document.querySelectorAll('[data-filter]').forEach(el=>el.addEventListener('click',()=>{const type=el.dataset.filter;hiddenTypes.has(type)?hiddenTypes.delete(type):hiddenTypes.add(type);el.setAttribute('aria-pressed',String(!hiddenTypes.has(type)));document.querySelectorAll('[data-type]').forEach(node=>node.hidden=hiddenTypes.has(node.dataset.type));$('filter-empty').hidden=!a.regions.length||a.regions.some(r=>!hiddenTypes.has(r.type));}));
  document.querySelectorAll('[data-play]').forEach(el=>el.addEventListener('click',()=>{select(Number(el.dataset.play));el.classList.contains('play-yours')?playYours():play('baseline-audio',phraseSegment(analysis.regions[selected],words,baseline));}));
  $('json-link').href=example.analysis;$('json-link').download=`${a.analysis_id}.json`;
  $('comparison').innerHTML=`<p>Reference: ${esc(a.reference.kind)}${a.reference.baseline_recording_id?' — '+esc(a.reference.baseline_recording_id):''}</p>`+
   (a.progress?'<table><caption>Stored rehearsal counts and durations</caption><thead><tr><th>Flaw</th><th>Previous</th><th>Current</th></tr></thead><tbody>'+Object.entries(a.progress).map(([k,v])=>`<tr><th>${esc(name(k))}</th><td>${v.previous.count} flags / ${v.previous.duration_s} s</td><td>${v.current.count} flags / ${v.current.duration_s} s</td></tr>`).join('')+'</tbody></table>':'')+
   '';
  $('tips').hidden=!a.key_moments?.length;$('key-moments').innerHTML=(a.key_moments||[]).map(k=>`<p>${k.passed?'Passed':'Flagged'}: ${esc(k.message)}</p>`).join('');
  $('warnings').innerHTML=a.warnings?.length?`<details><summary>${a.warnings.length} stored warnings</summary><pre>${esc(JSON.stringify(a.warnings,null,2))}</pre></details>`:'';
  $('results').hidden=false;$('loading').hidden=true;select(selected);
 }catch(err){$('loading').hidden=true;$('error').textContent=err.message;}
}
function select(i){
 selected=i;const v=analysis.regions[i];
 document.querySelectorAll('[data-region]').forEach(el=>el.setAttribute('aria-pressed',String(Number(el.dataset.region)===i)));
 if(v){
  document.querySelectorAll('.flaw-card').forEach(card=>{const active=Number(card.dataset.card)===i;card.classList.toggle('evidence',active);card.setAttribute('aria-current',String(active));for(const [selector,id] of [['.region','region-title'],['.explanation','explanation'],['.numbers','numbers'],['.play-yours','play-participant'],['.play-baseline','play-baseline'],['.pair-note','pair-note']]){const el=card.querySelector(selector);if(active)el.id=id;else el.removeAttribute('id');}});
  const card=document.querySelector(`[data-card="${i}"]`);if(card)$('regions').scrollTop=card.offsetTop;
 }
 $('baseline-audio').hidden=!example.baselineAudio;
 $('transcript').innerHTML=words.map(w=>v&&w.i>=v.word_start&&w.i<=v.word_end?`<mark>${esc(w.text)}</mark>`:esc(w.text)).join(' ');
}
async function play(id,span){
 if(!span)return;
 const audio=$(id);stopAt={id,end:span.end+.25};audio.currentTime=Math.max(0,span.start-.25);
 try{await audio.play();}catch(e){$('error').textContent=`Playback could not start: ${e.message}`;}
}
function playYours(){const v=analysis.regions[selected];if(v){const phrase=words.filter(w=>w.i>=v.word_start&&w.i<=v.word_end);play('participant-audio',{start:Math.min(v.start,phrase[0]?.start??v.start),end:Math.max(v.end,phrase.at(-1)?.end??v.end)});}}
document.querySelectorAll('[data-mode]').forEach(el=>el.addEventListener('click',()=>{const m=el.dataset.mode;if(m===analysis?.mode)return;const match=examples.find(e=>e.alignment===example?.alignment&&e.title.endsWith(`Mode ${m}`));if(match){$('example').value=match.id;load(match.id);}}));
if(defaultId)load(defaultId);else $('error').textContent='No precomputed examples have been packaged yet.';
