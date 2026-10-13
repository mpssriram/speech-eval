import {test,expect} from '@playwright/test';
import examples from '../src/catalog.js';
import fs from 'node:fs';

test('gallery exposes seven labelled synthetic hits with phrase playback',async({page})=>{
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');
 for(const e of examples.filter(e=>e.injectedType)){
  await expect(page.locator(`.example-card[href="#/example/${e.id}"]`)).toContainText(`Synthetic edit (severity ${e.injectionSeverity}). The detector found the injected flaw.`);
 }
 for(const e of examples.filter(e=>e.injectedType)){
  await page.goto('/#/example/'+e.id);
  await expect(page.getByRole('heading',{name:e.title,exact:true})).toBeVisible();
  const card=page.locator(`[data-region-index="${e.selectedRegion}"]`);
  await expect(card).toHaveAttribute('data-type',e.injectedType);
  await expect(card).toHaveAttribute('aria-current','true');
  await card.getByRole('button',{name:'Yours',exact:true}).click();
  const player=page.getByTestId('phrase-player');
  await expect.poll(()=>player.evaluate(a=>a.readyState)).toBeGreaterThan(0);
  await expect.poll(()=>player.evaluate(a=>a.currentTime)).toBeGreaterThan(0);
  const expected=JSON.parse(fs.readFileSync('public/'+e.analysis,'utf8'));
  const response=await page.request.get('/'+e.analysis);
  expect(await response.json()).toEqual(expected);
  await player.evaluate(a=>a.pause());
 }
 expect(errors).toEqual([]);
});
