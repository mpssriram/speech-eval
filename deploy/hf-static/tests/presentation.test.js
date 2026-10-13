import {test} from 'node:test';
import assert from 'node:assert/strict';
import {formatExplanation,fixed,formatText} from '../../../web/src/presentation.js';
test('zero pauses, extreme z, grammatical modes and exact times use presentation only',()=>{
 const r={type:'missing_pause',start:47.104,end:47.134,word_start:0,word_end:1,tags:[],evidence:{participant:6.9e-18,reference:.67,z:-3800},explanation:'raw 6.9e-18'};
 const before=JSON.stringify(r),words=[{i:0,text:'larger'},{i:1,text:'sense'}];
 for(const mode of ['A','B','C']){
  const text=formatExplanation(r,words,mode);
  assert.match(text,/47.10–47.13 s/);
  assert.match(text,/did not pause/);
  assert.match(text,/more than 10 SD/);
  assert.doesNotMatch(text,/\d[eE][+-]\d/);
  assert.doesNotMatch(text,/previous take pause /);
 }
 assert.equal(JSON.stringify(r),before);
 assert.equal(fixed(1e21),'1000000000000000000000.00');
 assert.equal(formatText('3.8e+03 SD'),'more than 10 SD');
});
