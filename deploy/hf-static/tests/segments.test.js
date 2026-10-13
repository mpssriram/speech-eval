import test from 'node:test';
import assert from 'node:assert/strict';
import { phraseSegment } from '../src/segments.js';
test('same words produce baseline phrase times in seconds',()=>{
 const words=[{i:0,text:'larger',norm:'larger',start:2,end:2.5},{i:1,text:'sense,',norm:'sense',start:2.5,end:3}];
 assert.deepEqual(phraseSegment({word_start:0,word_end:1},words,words),{start:2,end:3});
});
test('missing baseline words disable paired playback',()=>{
 assert.equal(phraseSegment({word_start:0,word_end:1},[{i:0,norm:'new'},{i:1,norm:'words'}],[{i:0,norm:'different',start:1,end:2}]),null);
});
