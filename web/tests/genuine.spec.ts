import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {reportPath} from './fixtures';

/** Existing frozen jobs only: this test neither uploads nor recomputes detectors. */
test('genuine Gettysburg B hit and report screenshots use recorder take02 vs take01',async({page,request})=>{
  const id='6d8cbd6dec22ffc8f7827ebc';
  const response=await request.get(`/api/analyses/${id}`);
  expect(response.ok()).toBe(true);
  const job=await response.json();
  expect(job.status).toBe('done');
  expect(job.analysis.recording_id).toBe('gettysburg__user__input_91e74acbc922');
  expect(job.analysis.mode).toBe('B');
  expect(job.analysis.duration_s).toBe(83.03);
  const region=job.analysis.regions.findIndex((r:{type:string;start:number;end:number})=>r.type==='awkward_pause'&&r.start===29.9&&r.end===31.47);
  expect(region).toBeGreaterThanOrEqual(0);
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(`/results/${id}`);
  await expect(page.getByTestId('waveform')).toHaveAttribute('data-ready','true',{timeout:30000});
  await expect(page.getByTestId('feature-chart').locator('.main-svg').first()).toBeVisible();
  await expect(page.locator('.results-heading')).toContainText('Mode B');
  await expect(page.getByLabel('Recording playback')).toHaveAttribute('src','/api/audio/gettysburg__user__input_91e74acbc922');
  await page.getByTestId('flaw-card').nth(region).getByRole('button',{name:/Awkward pause.*29.90/}).click();
  const hit=page.getByTestId('flaw-card').nth(region);
  await expect(hit).toHaveAttribute('aria-current','true');
  await expect(hit.locator('p')).toHaveText(job.analysis.regions[region].display_explanation);
  await expect(hit).toContainText('larger sense,');
  await expect(hit.getByRole('button',{name:'Baseline (same words)',exact:true})).toBeEnabled();
  await page.getByRole('banner').scrollIntoViewIfNeeded();
  await page.screenshot({path:reportPath('img/ui_results.png'),fullPage:false});
  await hit.screenshot({path:reportPath('img/ui_region.png')});
  expect(errors).toEqual([]);
  const sha256=(p:string)=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
  fs.writeFileSync(reportPath('human_ui_verification.json'),JSON.stringify({
    schema:'human-ui-verification/v1',source:'genuine recorder take02 vs own take01',
    job_id:id,recording_id:job.analysis.recording_id,mode:'B',duration_s:83.03,
    detected_interval_s:[29.9,31.47],label_interval_s:[29.9,31.47],primary_iou:1,
    explanation:job.analysis.regions[region].display_explanation,
    api_raw_audio_sha256:'a889f28475f52532bfb1368f5310466d5c3ab925a6a0dc14664c124cfc42817f',
    screenshots:{'ui_results.png':sha256(reportPath('img/ui_results.png')),
                 'ui_region.png':sha256(reportPath('img/ui_region.png'))},page_errors:errors,
  },null,2)+'\n');
});
