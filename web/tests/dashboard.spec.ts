import {test,expect,type Page} from '@playwright/test';
import path from 'node:path';

const audio=process.env.UI_FIXTURE_AUDIO||path.resolve('../data/audio/hq/gettysburg__lv_mk__orig.wav');
async function submit(page:Page){
  await page.getByLabel('Audio file',{exact:true}).setInputFiles(audio);
  await page.getByRole('button',{name:'Analyse recording',exact:true}).click();
  await expect(page.getByTestId('overall-score')).toContainText(/\d\.\d/,{timeout:150000});
}

test('new analysis exposes upload, recording and all three modes',async({page})=>{
  await page.goto('/');
  await expect(page.getByLabel('Audio file',{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'Record in browser'})).toBeVisible();
  await expect(page.getByLabel('Comparison').locator('option')).toHaveText([
    'Compare with expert readers','Compare with my previous take','Compare with good-speaker norms',
  ]);
});

test('browser recording yields an uploadable take and releases the meter',async({page,context})=>{
  await context.grantPermissions(['microphone']);
  await page.goto('/');
  await page.getByRole('button',{name:'Record in browser',exact:true}).click();
  await expect(page.getByLabel('Microphone level')).toBeVisible();
  await expect(page.getByRole('status')).toContainText('Recording · 0:01');
  await page.getByRole('button',{name:'Stop recording',exact:true}).click();
  await expect(page.locator('.upload')).toContainText('browser_take.webm');
  await expect(page.getByLabel('Microphone level')).toHaveCount(0);
  await expect(page.getByRole('button',{name:'Analyse recording',exact:true})).toBeEnabled();
});

test('real API upload, evidence, exact phrase playback and Modes A B C',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  await submit(page);
  await expect(page.getByTestId('waveform').locator('[part~="region"]').first()).toBeVisible();
  await expect(page.locator('.results-heading')).toContainText('Mode A');
  await expect(page.getByTestId('feature-chart').locator('.main-svg').first()).toBeVisible();
  const cards=page.getByTestId('flaw-card');
  await expect(cards.first().locator('p')).toContainText(/\d.*s/);
  await page.getByTestId('waveform').locator('[part~="region"]').nth(1).click();
  await expect(cards.nth(1)).toHaveAttribute('aria-current','true');
  await expect(page.getByTestId('waveform').locator('[part~="region"]').nth(1)).toHaveAttribute('data-selected','true');
  await cards.nth(1).getByRole('button',{name:'Yours',exact:true}).click();
  const player=page.getByTestId('phrase-player');
  await expect.poll(()=>player.evaluate((a:HTMLAudioElement)=>a.currentTime)).toBeGreaterThan(83.5);
  await expect(cards.nth(1).getByRole('button',{name:'Baseline (same words)',exact:true})).toBeEnabled();
  await cards.nth(1).getByRole('button',{name:'Baseline (same words)',exact:true}).click();
  await expect.poll(()=>player.evaluate((a:HTMLAudioElement)=>a.currentSrc)).toContain('gettysburg__lv_dj__orig');
  await expect.poll(()=>player.evaluate((a:HTMLAudioElement)=>a.currentTime)).toBeGreaterThan(60);
  await expect(cards.first().getByRole('button',{name:'Baseline (same words)',exact:true})).toBeDisabled();
  await expect(cards.first()).toContainText('Baseline words differ');
  await page.getByRole('button',{name:'New analysis',exact:true}).click();
  await page.getByLabel('Comparison').selectOption('B');
  await expect(page.getByLabel('Previous take').locator('option')).not.toHaveCount(1);
  const previous=await page.getByLabel('Previous take').locator('option').nth(1).getAttribute('value');
  await page.getByLabel('Previous take').selectOption(previous!);
  await submit(page);
  await expect(page.getByTestId('rehearsal-progress')).toBeVisible();
  await expect(page.getByTestId('progress-chart').locator('.main-svg').first()).toBeVisible();
  await page.getByRole('button',{name:'New analysis',exact:true}).click();
  await page.getByLabel('Comparison').selectOption('C');
  await submit(page);
  await expect(page.locator('.results-heading')).toContainText('Mode C');
  await expect(page.getByRole('heading',{name:/Key moments/})).toBeVisible();
  expect(await page.getByRole('button',{name:'Baseline (same words)',exact:true}).evaluateAll(elements=>elements.every(e=>(e as HTMLButtonElement).disabled))).toBe(true);
  expect(errors).toEqual([]);
});
