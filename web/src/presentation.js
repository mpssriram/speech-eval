/** Presentation only. Never mutate stored analysis, evidence, scores or times. */
export function fixed(value, digits=2) {
 return Number(value).toLocaleString('en-US',{useGrouping:false,minimumFractionDigits:digits,maximumFractionDigits:digits});
}
export function timeRange(start,end){return fixed(start)+'–'+fixed(end)+' s';}
/** Fixed point fallback for tips, warnings and future stored templates. */
export function formatText(text) {
 return String(text??'').replace(/[-+]?\d+(?:\.\d+)?[eE][-+]?\d+/g,v=>fixed(Number(v)))
  .replace(/(?<![\d.])(-?\d+(?:\.\d+)?) SD/g,(v,n)=>Math.abs(Number(n))>10?'more than 10 SD':fixed(Math.abs(Number(n)),1)+' SD')
  .replace(/your previous take pause\b/g,'your previous take paused')
  .replace(/your previous take average\b/g,'your previous take averaged')
  .replace(/your previous take vary\b/g,'your previous take varied');
}
/** Thresholds are supplied from detector.yaml by the build's config loader. */
export function flagThreshold(config,type,mode='A') {
 const features={rushing:'rate',dragging:'rate',monotone:'pitchrange',too_quiet:'final_drop',missing_pause:'end_pause'};
 return mode==='C'&&features[type]?config.mode_c.k[features[type]]:config.k[type];
}
export function sdTooltip(threshold) {
 return 'How far from the reference average, in standard deviations. Bigger means more unusual. Flags start at '+fixed(threshold,1)+' SD.';
}
export function formatExplanation(region,words,mode='A',threshold) {
 const a=region.word_start,b=region.word_end;
 const word=i=>words.find(w=>w.i===i)?.text??'';
 const quote=words.filter(w=>w.i>=a&&w.i<=b).map(w=>w.text).join(' ');
 const title=region.type.replaceAll('_',' ').replace(/^./,c=>c.toUpperCase());
 const header=title+' · '+timeRange(region.start,region.end)+' · "'+quote+'"';
 const e=region.evidence;
 if(!e||![e.participant,e.reference,e.z].every(v=>typeof v==='number'))return header+'\n'+formatText(region.display_explanation??region.explanation);
 const p=e.participant,r=e.reference,z=Math.abs(e.z);
 const n=v=>fixed(v,1).replace(/^-0\.0$/,'0.0').replace('-','−');
 const sd=z>10?'more than 10 SD':n(z)+' SD';
 const ref=mode==='B'?'your earlier take':mode==='C'?'typical speakers':'good readers';
 const average=mode==='B'?"your earlier take's average":ref+"' average";
 const pause=v=>v<.02?'none':fixed(v)+' s';
 let what,measured,off,why;
 switch(region.type){
 case 'rushing':what='You spoke much faster here.';measured=n(p)+' syllables per second (you) vs '+n(r)+' syllables per second ('+ref+')';off=n(p/r)+' times faster';why='Listeners may miss words.';break;
 case 'dragging':what='You spoke much more slowly here.';measured=n(p)+' syllables per second (you) vs '+n(r)+' syllables per second ('+ref+')';off=n(r/p)+' times slower';why='The phrase loses momentum.';break;
 case 'monotone':what='Your pitch stayed flat here.';measured=n(p)+' semitones (you) vs '+n(r)+' semitones ('+ref+')';off=n(r?100*p/r:0)+'% of the reference range';why='Flat pitch hides which words matter.';break;
 case 'too_quiet':what='You were much quieter here.';measured=n(p)+' dB (you) vs '+n(r)+' dB ('+ref+'), relative to your own average';off=n(r-p)+' dB quieter';why='Listeners may lose these words.';break;
 case 'mumbling':what='Your words were less crisp here.';measured='clarity measure (high-frequency energy): '+n(p)+' dB (you) vs '+n(r)+' dB ('+ref+')';off=n(r-p)+' dB lower';why='Consonants are harder to hear.';break;
 case 'awkward_pause':what='You paused in the middle of a phrase.';measured="pause after '"+word(a)+"': "+pause(p)+' (you) vs '+(r<.02?'no pause':pause(r))+' ('+ref+')';off=fixed(p-r)+' s longer';why='It breaks the sentence.';break;
 case 'missing_pause':what=(p<.02?'You did not pause where ':'Your pause was too short where ')+ref+(mode==='B'?' pauses.':' pause.');measured="pause after '"+word(a)+"': "+pause(p)+' (you) vs '+(r<.02?'no pause':pause(r))+' ('+ref+')';off=fixed(r-p)+' s shorter';why='Listeners get no breathing space.';break;
 default:return header+'\n'+formatText(region.explanation);
 }
 const direction=e.z<0?'below':'above';
 const flags=typeof threshold==='number'?' Flags start at '+fixed(threshold,1)+' SD.':'';
 const lines=[header,'What happened: '+what,'Measured: '+measured,'How far off: '+off+', which is '+sd+' '+direction+' '+(mode==='B'?'':'the ')+average+'.'+flags,'Why it matters: '+why];
 const tags=region.tags??[],where=[];
 if(tags.includes('first_sentence'))where.push('opening sentence');
 if(tags.includes('final_sentence'))where.push('final sentence');
 if(where.length)lines.push('Where: '+where.join(' / '));
 return lines.join('\n');
}
