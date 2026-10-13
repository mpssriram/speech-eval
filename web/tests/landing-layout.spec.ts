import {test,expect} from '@playwright/test';
import fs from 'node:fs';
import examples from '../src/catalog.js';
for(const width of [375,768,1280,1440,1920]){
 test('live landing and upload fit '+width+'px',async({page})=>{
  await page.setViewportSize({width,height:1000});await page.goto('/#/');
  await expect(page.getByRole('heading',{name:'Speech-Eval',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  if(width>=1280)expect(await page.evaluate(()=>document.documentElement.scrollHeight)).toBeLessThanOrEqual(1000);
  await page.getByRole('link',{name:'Upload a recording',exact:true}).click();await expect(page.getByLabel('Audio file',{exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 });
}
test('every live precomputed explanation renders without scientific notation',async({page})=>{
 for(const e of examples){
  await page.goto('/#/example/'+e.id);await expect(page.getByRole('heading',{name:e.title,exact:true})).toBeVisible();
  const expected=JSON.parse(fs.readFileSync('../deploy/hf-static/public/'+e.analysis,'utf8')).regions.length;
  await expect(page.locator('.explanation')).toHaveCount(expected);
  for(const text of await page.locator('.explanation').allTextContents())expect(text).not.toMatch(/\d[eE][+-]\d/);
 }
});
