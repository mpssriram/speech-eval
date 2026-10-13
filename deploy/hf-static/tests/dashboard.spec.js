import {test,expect} from '@playwright/test';
import examples from '../src/catalog.js';
import fs from 'node:fs';
import {phraseSegment} from '../src/segments.js';
const evidence={base_url:process.env.DEMO_BASE_URL||'http://127.0.0.1:18765',pageErrors:[],failedResponses:[],apiCalls:[],examples:[],checks:[]};
function watch(page){page.on('pageerror',e=>evidence.pageErrors.push(e.message));page.on('response',r=>{if(r.status()>=400)evidence.failedResponses.push({url:r.url(),status:r.status()});});page.on('request',r=>{if(new URL(r.url()).pathname.startsWith('/api/'))evidence.apiCalls.push(r.url());});}
const defaultExample=examples.find(e=>e.default);
async function play(audio,expectedStart){
 await expect.poll(()=>audio.evaluate(a=>a.readyState)).toBeGreaterThan(0);
 await audio.evaluate(a=>a.play());await expect.poll(()=>audio.evaluate(a=>a.paused)).toBe(false);
 if(expectedStart!==undefined)expect(await audio.evaluate(a=>a.currentTime)).toBeGreaterThanOrEqual(expectedStart);
 const start=await audio.evaluate(a=>a.currentTime);
 await expect.poll(()=>audio.evaluate(a=>a.currentTime)).toBeGreaterThan(start+.12);
 await audio.evaluate(a=>a.pause());return {duration:await audio.evaluate(a=>a.duration),played:true,start};
}
test('genuine hit selection and paired phrase playback use the same frozen words',async({page})=>{
 watch(page);await page.goto('/#/example/'+defaultExample.id);
 await expect(page.getByRole('heading',{name:defaultExample.title,exact:true})).toBeVisible();
 const hit=page.locator('[data-region-index="'+defaultExample.selectedRegion+'"]');
 await expect(hit).toHaveAttribute('aria-current','true');await expect(hit).toContainText('larger');
 await expect(page.locator('#banner')).toContainText('Precomputed demo.');
 await page.locator('.flaw-title').first().click();await hit.locator('.flaw-title').click();
 await hit.getByRole('button',{name:'Yours',exact:true}).click();
 const participant=await play(page.getByTestId('phrase-player'),29);
 await hit.getByRole('button',{name:'Baseline (same words)',exact:true}).click();
 const baseline=await play(page.getByTestId('phrase-player'),27);
 evidence.checks.push({default:'larger | sense',participant,baseline});
 await page.getByRole('banner').scrollIntoViewIfNeeded();await page.screenshot({path:'../../reports/img/static_results.png',fullPage:true});await hit.screenshot({path:'../../reports/img/static_region.png'});
});
test('every example plays audio; Mode C has no invented baseline',async({page})=>{
 watch(page);await page.goto('/#/example/'+defaultExample.id);
 for(const e of examples){
  await page.locator('#example').selectOption(e.id);await expect(page.getByRole('heading',{name:e.title,exact:true})).toBeVisible();
  await expect(page.getByTestId('waveform')).toHaveAttribute('data-ready','true');
  const row={id:e.id,title:e.title,participant:await play(page.getByLabel('Recording playback',{exact:true}))};
  const a=JSON.parse(fs.readFileSync('public/'+e.analysis,'utf8'));
  if(a.regions.length){
   const selected=page.locator('[data-region-index="'+(e.selectedRegion??0)+'"]');
   if(e.baselineAudio){
    await expect(selected.getByRole('button',{name:'Baseline (same words)',exact:true})).toBeEnabled();
    const w=JSON.parse(fs.readFileSync('public/'+e.alignment,'utf8')).words,b=JSON.parse(fs.readFileSync('public/'+e.baselineAlignment,'utf8')).words,pair=phraseSegment(a.regions[e.selectedRegion??0],w,b);
    await selected.getByRole('button',{name:'Baseline (same words)',exact:true}).click();
    row.baseline=await play(page.getByTestId('phrase-player'),pair.start);
   }else{await expect(selected.getByRole('button',{name:'Baseline (same words)',exact:true})).toBeDisabled();await expect(selected).toContainText('no same-text baseline');}
  }else await expect(page.locator('.flag-panel .empty')).toContainText('No flaws detected');
  evidence.examples.push(row);
 }
});
test('mobile results fit and keyboard markers select a card',async({page})=>{
 watch(page);await page.setViewportSize({width:375,height:844});await page.goto('/#/example/'+defaultExample.id);
 await expect(page.getByTestId('waveform')).toHaveAttribute('data-ready','true');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 const marker=page.getByTestId('waveform').locator('[part~="region"]').first();await marker.focus();await page.keyboard.press('Enter');
 await expect(page.locator('[data-region-index="0"]')).toHaveAttribute('aria-current','true');
 await page.screenshot({path:'../../reports/img/static_mobile.png',fullPage:true});
});
test.afterAll(()=>{
 fs.writeFileSync(process.env.DEMO_BASE_URL?.startsWith('https:')?'../../reports/deploy_browser_checks_public.json':'../../reports/deploy_browser_checks.json',JSON.stringify(evidence,null,2)+'\n');
 expect(evidence.pageErrors).toEqual([]);expect(evidence.failedResponses).toEqual([]);expect(evidence.apiCalls).toEqual([]);
});
