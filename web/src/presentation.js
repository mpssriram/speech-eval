/** Presentation only. Never mutate stored analysis, evidence, scores or times. */
export function fixed(value, digits=2) {
 return Number(value).toLocaleString('en-US',{useGrouping:false,minimumFractionDigits:digits,maximumFractionDigits:digits});
}
export function timeRange(start,end){return fixed(start)+'–'+fixed(end)+' s';}
/** Fixed point fallback for tips, warnings and future stored templates. */
export function formatText(text) {
 return String(text??'').replace(/[-+]?\d+(?:\.\d+)?[eE][-+]?\d+/g,v=>fixed(Number(v)))
  .replace(/(?<![\d.])(-?\d+(?:\.\d+)?) SD/g,(v,n)=>Math.abs(Number(n))>10?'more than 10 SD':fixed(Math.abs(Number(n)))+' SD')
  .replace(/your previous take pause\b/g,'your previous take paused')
  .replace(/your previous take average\b/g,'your previous take averaged')
  .replace(/your previous take vary\b/g,'your previous take varied');
}
export function formatExplanation(region,words,mode='A') {
 const a=region.word_start,b=region.word_end;
 const word=i=>words.find(w=>w.i===i)?.text??'';
 const quote=words.filter(w=>w.i>=a&&w.i<=b).map(w=>w.text).join(' ');
 const prefix=timeRange(region.start,region.end)+', "'+quote+'": ';
 const e=region.evidence;
 if(!e||![e.participant,e.reference,e.z].every(v=>typeof v==='number')){
  return prefix+formatText(region.explanation).replace(/^\d+(?:\.\d+)?[–-]\d+(?:\.\d+)? s,\s*"[^"]*":\s*/,'');
 }
 const p=e.participant,r=e.reference,z=Math.abs(e.z),n=fixed;
 const sd=z>10?'more than 10 SD':n(z)+' SD';
 const ref=mode==='B'?'your previous take':mode==='C'?'speaker norms':'good readers';
 const avg=mode==='B'?'averaged':'average',vary=mode==='B'?'varied':'vary',pause=mode==='B'?'paused':'pause';
 const expected=r<.02?(mode==='B'?'your previous take had no pause':ref+' do not pause'):ref+' '+pause+' '+n(r)+' s';
 const participant=p<.02?'you did not pause':'you paused '+n(p)+' s';
 const tags=region.tags??[];
 let text;
 switch(region.type){
 case 'rushing':text='you spoke at '+n(p,1)+' syllables/s; '+ref+' '+avg+' '+n(r,1)+' ('+n(p/r)+'× faster, '+sd+' above). Rushing this phrase reduces its weight.';break;
 case 'dragging':text='you spoke at '+n(p,1)+' vs '+n(r,1)+' syllables/s for '+ref+' ('+n(r/p)+'× slower, '+sd+' below). The phrase loses momentum.';break;
 case 'monotone':text='your pitch varied by '+n(p)+' semitones; '+ref+' '+vary+' by '+n(r)+' ('+n(r?100*(1-p/r):0)+'% less variation, '+sd+' below). The phrase sounds flat.';break;
 case 'too_quiet':text=n(r-p)+' dB quieter than '+ref+' relative to your own average level ('+sd+' below).'+(tags.includes('sentence_final')?' Your voice trails off at the end of the sentence.':'');break;
 case 'mumbling':text='high-frequency energy (consonant clarity) is '+n(r-p)+' dB lower than '+ref+' ('+sd+' below). Words may sound muffled.';break;
 case 'awkward_pause':text=participant+' between "'+word(a)+'" and "'+word(b)+'", where '+expected+' ('+n(p-r)+' s longer, '+sd+' above). It breaks the sentence.';break;
 case 'missing_pause':text=participant+' after "'+word(a)+'" where '+expected+' ('+n(r-p)+' s shorter, '+sd+' below). The listener gets no breathing space.';break;
 default:return prefix+formatText(region.explanation).replace(/^.*?:\s*/,'');
 }
 const suffix={final_sentence:" This is the speech's final sentence.",first_sentence:' This is the opening sentence.',contains_number:' This phrase contains a number.',sentence_final:' This region reaches a sentence ending.'};
 return prefix+text+tags.map(t=>suffix[t]??'').join('');
}
