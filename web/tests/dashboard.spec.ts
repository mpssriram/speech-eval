import {test,expect,type Page} from '@playwright/test';
import fs from 'node:fs';
import {speechFixture,reportPath} from './fixtures';

async function submit(page:Page){
  await page.getByLabel('Audio file',{exact:true}).setInputFiles(speechFixture().audio);
  await page.getByRole('button',{name:'Analyse recording',exact:true}).click();
  await expect(page.getByTestId('overall-score')).toContainText(/\d\.\d/,{timeout:150000});
}

test('new analysis exposes upload, recording and all three modes',async({page})=>{
  await page.goto('/#/upload');
  await expect(page.getByLabel('Audio file',{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Record in browser'})).toBeVisible();
  await expect(page.getByLabel('Comparison').locator('option')).toHaveText([
    'Compare with expert readers','Compare with my previous take','Compare with good-speaker norms',
  ]);
  await page.getByLabel('Audio file',{exact:true}).setInputFiles(speechFixture().audio);
  await expect(page.getByRole('button',{name:'Analyse recording',exact:true})).toBeEnabled();
  await page.getByLabel('Speech text').selectOption('own_speech');
  await expect(page.getByLabel('Comparison')).toHaveCount(0);
  await expect(page.getByLabel('Your transcript')).toHaveAttribute('required','');
  await expect(page.getByRole('button',{name:'Analyse recording',exact:true})).toBeDisabled();
  await page.getByLabel('Your transcript').fill('Four score and seven years ago.');
  await expect(page.getByRole('button',{name:'Analyse recording',exact:true})).toBeEnabled();
});

test('browser recording yields an uploadable take and releases the meter',async({page,context})=>{
  await context.grantPermissions(['microphone']);
  await page.goto('/#/upload');
  await page.getByRole('button',{name:'Record in browser',exact:true}).click();
  await expect(page.getByLabel('Microphone level')).toBeVisible();
  await expect(page.getByRole('status')).toContainText('Recording · 0:01');
  await page.getByRole('button',{name:'Stop recording',exact:true}).click();
  await expect(page.locator('.upload')).toContainText('browser_take.webm');
  await expect(page.getByLabel('Microphone level')).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Analyse recording',exact:true})).toBeEnabled();
});

test('real API upload, evidence, exact phrase playback and Modes A B C',async({page,browser,request})=>{
  const started=Date.now(),completed:string[]=[];
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/#/upload');
  await page.getByLabel('Audio file',{exact:true}).setInputFiles(speechFixture().audio);
  await page.screenshot({path:reportPath('img/ui_upload.png'),fullPage:true});
  await submit(page);
  completed.push(page.url().split('/').pop()!);
  await expect(page.getByTestId('waveform').locator('[part~="region"]').first()).toBeVisible();
  await expect(page.locator('.results-heading')).toContainText('Mode A');
  await expect(page.getByTestId('feature-chart').locator('.main-svg').first()).toBeVisible();
  await page.screenshot({path:reportPath('img/smoke_results.png'),fullPage:true});
  const cards=page.getByTestId('flaw-card');
  await cards.first().locator('.flaw-title').click();
  await expect(cards.first().locator('.explanation')).toContainText(/\d.*s/);
  // Real API presentation must not leak scientific notation or uncapped SD.
  const explanations=await cards.locator('.explanation').allTextContents();
  expect(explanations.length).toBeGreaterThan(0);
  for(const text of explanations){
    expect(text).not.toMatch(/\d[eE][+-]\d/);
    for(const sd of text.matchAll(/(?<![\d.])(\d+(?:\.\d+)?) SD/g))expect(Number(sd[1])).toBeLessThanOrEqual(10);
    expect(text).toContain('What happened:');
    expect(text).toContain('Measured:');
  }
  await page.getByTestId('waveform').locator('[part~="region"]').nth(1).click();
  await expect(cards.nth(1)).toHaveAttribute('aria-current','true');
  await expect(page.getByTestId('waveform').locator('[part~="region"]').nth(1)).toHaveAttribute('data-selected','true');
  await cards.nth(1).getByRole('button',{name:'Yours',exact:true}).click();
  const player=page.getByTestId('phrase-player');
  const yoursStart=await player.evaluate((a:HTMLAudioElement)=>a.currentTime);
  await expect.poll(()=>player.evaluate((a:HTMLAudioElement)=>a.currentTime)).toBeGreaterThan(yoursStart+.1);
  await expect(cards.nth(1).getByRole('button',{name:'Baseline (same words)',exact:true})).toBeEnabled();
  await cards.nth(1).getByRole('button',{name:'Baseline (same words)',exact:true}).click();
  await expect.poll(()=>player.evaluate((a:HTMLAudioElement)=>a.currentSrc)).toContain('gettysburg__lv_dj__orig');
  const baselineStart=await player.evaluate((a:HTMLAudioElement)=>a.currentTime);
  await expect.poll(()=>player.evaluate((a:HTMLAudioElement)=>a.currentTime)).toBeGreaterThan(baselineStart+.1);
  await cards.first().locator('.flaw-title').click();
  await expect(cards.first().getByRole('button',{name:'Baseline (same words)',exact:true})).toBeDisabled();
  await expect(cards.first()).toContainText('Baseline words differ');
  await expect(page.getByRole('alert')).toHaveCount(0);
  await page.getByRole('tab',{name:'Pauses',exact:true}).click();
  await page.getByRole('banner').scrollIntoViewIfNeeded();
  await page.screenshot({path:reportPath('img/smoke_region.png'),fullPage:true});
  await page.getByRole('button',{name:'New analysis',exact:true}).click();
  await page.getByLabel('Comparison').selectOption('B');
  await expect(page.getByLabel('Previous take').locator('option')).not.toHaveCount(1);
  // Existing history may include other recordings; compare this fixture to its own A take.
  await page.getByLabel('Previous take').selectOption(completed[0]);
  await submit(page);
  completed.push(page.url().split('/').pop()!);
  await expect(page.getByTestId('rehearsal-progress')).toBeVisible();
  await expect(page.locator('.empty')).toContainText('against your earlier take');
  await expect(page.getByTestId('progress-chart').locator('.main-svg').first()).toBeVisible();
  await expect(page.getByTestId('waveform')).toHaveAttribute('data-ready','true');
  await page.screenshot({path:reportPath('img/ui_modeB.png'),fullPage:true});
  await page.getByRole('button',{name:'New analysis',exact:true}).click();
  await page.getByLabel('Comparison').selectOption('C');
  await submit(page);
  completed.push(page.url().split('/').pop()!);
  await expect(page.locator('.results-heading')).toContainText('Mode C');
  await expect(page.getByRole('heading',{name:/Heuristic tips \(not scored\)/})).toBeVisible();
  await expect(page.getByTestId('waveform')).toHaveAttribute('data-ready','true');
  expect(await page.getByRole('button',{name:'Baseline (same words)',exact:true}).evaluateAll(elements=>elements.every(e=>(e as HTMLButtonElement).disabled))).toBe(true);
  await page.screenshot({path:reportPath('img/ui_modeC_upload.png'),fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await expect(page.getByTestId('overall-score')).toBeVisible();
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  expect(errors).toEqual([]);
  const results=await Promise.all(completed.map(async id=>(await request.get(`/api/analyses/${id}`)).json()));
  fs.writeFileSync(reportPath('ui_verification.json'),JSON.stringify({
    schema:'ui-verification/v1',browser:browser.version(),fixture:{recording_id:'gettysburg__lv_mk__orig',sha256:speechFixture().sha256},
    modes:results.map(j=>({mode:j.analysis.mode,analysis_id:j.analysis_id,score:j.analysis.scores.overall,regions:j.analysis.regions.length,status:j.status})),
    screenshots:['ui_upload.png','smoke_results.png','smoke_region.png','ui_modeB.png','ui_modeC.png'],page_errors:errors,
    elapsed_seconds:Number(((Date.now()-started)/1000).toFixed(2)),viewport:{width:1440,height:1000},mobile:{width:390,height:844},
  },null,2)+'\n');
});
