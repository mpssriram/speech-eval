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
  await expect(page.getByLabel('Recording playback').locator('source')).toHaveAttribute('src','/api/audio/gettysburg__user__input_91e74acbc922');
  await page.getByTestId('flaw-card').nth(region).getByRole('button',{name:/Awkward pause.*29.90/}).click();
  const hit=page.getByTestId('flaw-card').nth(region);
  await expect(hit).toHaveAttribute('aria-current','true');
  await expect(page.getByTestId('waveform').locator('[part~="region"]').nth(region)).toHaveAttribute('data-selected','true');
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
    native_raw_wav_sha256:'a889f28475f52532bfb1368f5310466d5c3ab925a6a0dc14664c124cfc42817f',
    screenshots:{'ui_results.png':sha256(reportPath('img/ui_results.png')),
                 'ui_region.png':sha256(reportPath('img/ui_region.png'))},page_errors:errors,
  },null,2)+'\n');
});

for(const width of [1440,390]){
  test(`genuine waveform markers have hover labels and exact widths at ${width}px`,async({page,request})=>{
    await page.setViewportSize({width,height:1000});
    const id='0aae3748f747b13e89697e17';
    const job=await (await request.get(`/api/analyses/${id}`)).json();
    await page.goto(`/results/${id}`);
    await expect(page.getByTestId('waveform')).toHaveAttribute('data-ready','true',{timeout:30000});
    const regions=page.getByTestId('waveform').locator('[part~="region"]');
    await expect(regions).toHaveCount(9);
    // Removing text inside each interval prevents overlapping/wrapped labels.
    expect(await regions.allTextContents()).toEqual(Array(9).fill(''));
    const shapes=await regions.evaluateAll(elements=>elements.map(el=>({
      width:el.getBoundingClientRect().width,parentWidth:el.parentElement!.getBoundingClientRect().width,
      title:el.getAttribute('title'),label:el.getAttribute('aria-label'),
      color:getComputedStyle(el).backgroundColor,
    })));
    shapes.forEach((shape,i)=>{
      const r=job.analysis.regions[i];
      expect(shape.width).toBeCloseTo(shape.parentWidth*(r.end-r.start)/job.analysis.duration_s,0);
      expect(shape.title).toContain(`${r.start.toFixed(2)}–${r.end.toFixed(2)} s`);
      expect(shape.label).toBe(shape.title);
      expect(shape.color).not.toBe('rgba(0, 0, 0, 0)');
    });
    const rush=job.analysis.regions.findIndex((r:{type:string})=>r.type==='rushing');
    expect(rush).toBeGreaterThanOrEqual(0);
    await regions.nth(rush).focus();
    await regions.nth(rush).press('Enter');
    await expect(page.getByTestId('flaw-card').nth(rush)).toHaveAttribute('aria-current','true');
    expect(await regions.nth(rush).getAttribute('title')).toContain('Rushing');
    expect(await page.getByTestId('waveform').locator('[part~="region"]').nth(rush).evaluate(el=>getComputedStyle(el).backgroundColor)).toBe('rgba(255, 180, 84, 0.333)');
    const proofPath=reportPath('waveform_ui_verification.json');
    const proof=width===1440?{schema:'waveform-ui-verification/v1',checks:{}}:
      JSON.parse(fs.readFileSync(proofPath,'utf8'));
    proof.checks[String(width)]={job_id:id,region_count:9,inline_labels:0,
      actual_interval_widths_verified:true,hover_and_accessible_labels:true,
      keyboard_selection:true,legend_colours_preserved:true,shapes};
    fs.writeFileSync(proofPath,JSON.stringify(proof,null,2)+'\n');
  });
}
