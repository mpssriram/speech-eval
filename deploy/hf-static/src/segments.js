/** Find an exact same-words baseline span; returned times are seconds. */
export function phraseSegment(region, participant, baseline) {
 const selected=participant.filter(w=>w.i>=region.word_start && w.i<=region.word_end);
 if(!selected.length || !baseline.length) return null;
 const norm=w=>w.norm || w.text.toLowerCase().replace(/[^a-z0-9]/g,'');
 const matches=[];
 for(let i=0;i<=baseline.length-selected.length;i++)
  if(selected.every((w,j)=>norm(w)===norm(baseline[i+j]))) matches.push(i);
 if(!matches.length) return null;
 // Repeated phrases: use relative transcript position to choose the closest occurrence.
 const target=region.word_start/Math.max(1,participant.length);
 const i=matches.reduce((a,b)=>Math.abs(a/baseline.length-target)<=Math.abs(b/baseline.length-target)?a:b);
 return {start:baseline[i].start,end:baseline[i+selected.length-1].end};
}
