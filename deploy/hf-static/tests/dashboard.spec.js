import { test, expect } from '@playwright/test';
import examples from '../src/catalog.js';
import fs from 'node:fs';
import {phraseSegment} from '../src/segments.js';
const evidence={pageErrors:[],failedResponses:[],apiCalls:[],examples:[],checks:[]};
function watch(page){
 page.on('pageerror',e=>evidence.pageErrors.push(e.message));
 page.on('response',r=>{if(r.status()>=400)evidence.failedResponses.push({url:r.url(),status:r.status()});});
 page.on('request',r=>{if(new URL(r.url()).pathname.startsWith('/api/'))evidence.apiCalls.push(r.url());});
}
async function play(page,id,button,expectedStart){
 const audio=page.locator('#'+id);
 await expect.poll(()=>audio.evaluate(a=>a.readyState)).toBeGreaterThan(0);
 const before=await audio.evaluate(a=>a.currentTime);
 if(button)await page.locator(button).click();else await audio.evaluate(a=>a.play());
 await expect.poll(()=>audio.evaluate(a=>a.paused)).toBe(false);
 if(expectedStart!==undefined)await expect.poll(()=>audio.evaluate(a=>a.currentTime),{timeout:10000}).toBeGreaterThanOrEqual(expectedStart);
 const start=await audio.evaluate(a=>a.currentTime);
 await expect.poll(()=>audio.evaluate(a=>a.currentTime),{timeout:10000}).toBeGreaterThan(start+.12);
 await audio.evaluate(a=>a.pause());
 return {duration:await audio.evaluate(a=>a.duration),played:true,before,start};
}
test('default genuine hit, region selection, and both phrase playbacks',async({page})=>{
 watch(page);await page.goto('/');await expect(page.locator('#results')).toBeVisible();
 await expect(page.locator('#title')).toHaveText('Gettysburg take02 · Mode B');
 await expect(page.locator('#region-title')).toContainText('29.90–31.47');
 await expect(page.locator('#explanation')).toContainText('larger');
 await expect(page.locator('#upload')).toBeDisabled();
 await expect(page.locator('#banner')).toHaveText('Precomputed demo. Live analysis of your own audio runs locally with Docker; see the GitHub README.');
 await page.locator('.region').first().click();
 const e=examples.find(e=>e.default);await page.locator(`.region[data-region="${e.selectedRegion}"]`).click();
 const participant=await play(page,'participant-audio','#play-participant',29);
 const baseline=await play(page,'baseline-audio','#play-baseline',27);
 evidence.checks.push({default:'larger | sense',participant,baseline});
 await page.screenshot({path:'../../reports/img/static_results.png',fullPage:true});
 await page.locator('.evidence').screenshot({path:'../../reports/img/static_region.png'});
});
test('every example loads and playback works; C has no invented baseline',async({page})=>{
 watch(page);await page.goto('/');await expect(page.locator('#results')).toBeVisible();
 for(const e of examples){
  await page.locator('#example').selectOption(e.id);await expect(page.locator('#title')).toHaveText(e.title);
  await expect(page.locator('#results')).toBeVisible();
  const row={id:e.id,title:e.title,participant:await play(page,'participant-audio')};
  if(e.baselineAudio){
   row.baseline=await play(page,'baseline-audio');
   if(await page.locator('.region').count()){
    await expect(page.locator('#play-baseline')).toBeEnabled();
    const a=JSON.parse(fs.readFileSync('public/'+e.analysis,'utf8'));
    const w=JSON.parse(fs.readFileSync('public/'+e.alignment,'utf8')).words;
    const b=JSON.parse(fs.readFileSync('public/'+e.baselineAlignment,'utf8')).words;
    const pair=phraseSegment(a.regions[e.selectedRegion??0],w,b);
    row.phrase=await play(page,'baseline-audio','#play-baseline',Math.max(0,pair.start-.25));
   }else{await expect(page.locator('#play-baseline')).toBeDisabled();row.phrase='No flagged region; whole baseline played above';}
  }else{await expect(page.locator('#play-baseline')).toBeDisabled();await expect(page.locator('#pair-note')).toContainText('no same-text baseline');}
  evidence.examples.push(row);
 }
});
test('mobile layout fits and uses keyboard-accessible regions',async({page})=>{
 watch(page);await page.setViewportSize({width:390,height:844});await page.goto('/');
 await expect(page.locator('#results')).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.locator('.region').first().focus();await page.keyboard.press('Enter');
 await expect(page.locator('.region').first()).toHaveAttribute('aria-pressed','true');
 await page.screenshot({path:'../../reports/img/static_mobile.png',fullPage:true});
});
test.afterAll(()=>{
 fs.writeFileSync('../../reports/deploy_browser_checks.json',JSON.stringify(evidence,null,2)+'\n');
 expect(evidence.pageErrors).toEqual([]);expect(evidence.failedResponses).toEqual([]);expect(evidence.apiCalls).toEqual([]);
});
