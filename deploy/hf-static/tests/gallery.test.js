import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import examples from '../src/catalog.js';

test('all seven synthetic types have stored v1 hits and exact injection severity labels',()=>{
 const expected=['rushing','dragging','monotone','too_quiet','mumbling','awkward_pause','missing_pause'];
 const synthetic=examples.filter(e=>e.injectedType);
 assert.deepEqual(synthetic.map(e=>e.injectedType).sort(),expected.sort());
 const manifest=Object.fromEntries(fs.readFileSync(new URL('../MANIFEST.sha256',import.meta.url),'utf8').trim().split('\n').map(line=>{const [hash,path]=line.split('  ');return [path,hash];}));
 for(const e of synthetic){
  assert.match(e.title,new RegExp(`synthetic edit, severity ${e.injectionSeverity}`));
  const load=path=>{const bytes=fs.readFileSync(new URL('../public/'+path,import.meta.url));assert.equal(createHash('sha256').update(bytes).digest('hex'),manifest[path]);return JSON.parse(bytes);};
  const a=load(e.analysis),labels=load(e.label).flaws;
  assert.equal(a.schema,'analysis/v1');
  assert.equal(a.detector.config_hash,'f0759b1d459d2f1fd06452a1fa617e49444558f03c2ee8f8d1dfc05e1bc87e09');
  const p=a.regions[e.selectedRegion];assert.equal(p.type,e.injectedType);
  const hit=labels.find(g=>g.type===p.type&&g.severity===e.injectionSeverity&&Math.max(0,Math.min(g.end,p.end)-Math.max(g.start,p.start))/(Math.max(g.end,p.end)-Math.min(g.start,p.start))>=.3);
  assert.ok(hit,`Missing genuine stored hit for ${e.injectedType}`);
  assert.ok(fs.existsSync(new URL('../public/'+e.audio,import.meta.url)));
 }
});
