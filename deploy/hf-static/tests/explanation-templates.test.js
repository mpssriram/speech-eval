import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {parse} from '../../../web/node_modules/yaml/dist/index.js';
import * as presentation from '../../../web/src/presentation.js';
const {formatExplanation,sdTooltip,flagThreshold}=presentation;
const rows=JSON.parse(fs.readFileSync(new URL('../../../tests/fixtures/explanation_snapshots.json',import.meta.url)));
const config=parse(fs.readFileSync(new URL('../../../configs/detector.yaml',import.meta.url),'utf8'));
const words=[{i:0,text:'larger'},{i:1,text:'sense'}];
for(const row of rows)test(row.mode+' '+row.region.type+' explanation snapshot preserves evidence',()=>{
 const before=JSON.stringify(row.region);
 const threshold=flagThreshold(config,row.region.type,row.mode);
 assert.equal(threshold,row.threshold);
 assert.equal(formatExplanation(row.region,words,row.mode,threshold),row.expected);
 assert.equal(JSON.stringify(row.region),before);
 assert.doesNotMatch(row.expected,/\d(?:\.\d*)?[eE][+-]?\d/);
});
test('tooltip and threshold read custom config for both rule families',()=>{
 assert.equal(flagThreshold({k:{rushing:4.25},mode_c:{k:{rate:1.75}}},'rushing','B'),4.25);
 assert.equal(flagThreshold({k:{rushing:4.25},mode_c:{k:{rate:1.75}}},'rushing','C'),1.75);
 assert.equal(sdTooltip(4.25),'How far from the reference average, in standard deviations. Bigger means more unusual. Flags start at 4.3 SD.');
});
test('pause and SD cutoffs and sentence location',()=>{
 const r=structuredClone(rows.find(r=>r.region.type==='missing_pause').region);
 r.tags=['first_sentence'];r.evidence={participant:.019,reference:.02,z:-10};
 const text=formatExplanation(r,words,'A',3.5);
 assert.match(text,/none \(you\) vs 0.02 s/);assert.match(text,/10.0 SD below/);assert.match(text,/Where: opening sentence$/);
 r.tags=[];r.evidence.z=-10.001;
 assert.match(formatExplanation(r,words,'A',3.5),/more than 10 SD below/);
 assert.doesNotMatch(formatExplanation(r,words,'A',3.5),/Where:/);
});

test('a short measured pause is never described as absent',()=>{
 const r=structuredClone(rows.find(r=>r.region.type==='missing_pause').region);
 r.evidence.participant=.07;
 const text=formatExplanation(r,words,'B',3.5);
 assert.match(text,/Your pause was too short where your earlier take pauses/);
 assert.match(text,/0.07 s \(you\)/);
 assert.doesNotMatch(text,/did not pause|none \(you\)|the your/);
});
