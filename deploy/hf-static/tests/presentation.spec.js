import {test,expect} from '@playwright/test';
import examples from '../src/catalog.js';
test('every rendered explanation uses readable fixed-point numbers and grammatical references',async({page})=>{
 await page.goto('/');
 await page.locator('#example').selectOption(examples.find(e=>e.default).id);
 for(const example of examples){
  await page.locator('#example').selectOption(example.id);
  await expect(page.getByRole('heading',{name:example.title,exact:true})).toBeVisible();
  for(const title of await page.locator('.flaw-title').allTextContents())expect(title).toMatch(/\d+\.\d{2}–\d+\.\d{2} s/);
  const texts=await page.locator('.flaw-card .explanation').allTextContents();
  for(const text of texts){
   expect(text).not.toMatch(/\d[eE][+-]\d/);
   expect(text).not.toMatch(/previous take (?:pause|average|vary)\b/);
   expect(text).toContain('What happened:');
   expect(text).toContain('Measured:');
   expect(text).toContain('How far off:');
   expect(text).toContain('Why it matters:');
   expect(text).not.toMatch(/your previous take|speaker norms|intelligibility/);
   for(const sd of text.matchAll(/(?<![\d.])(\d+(?:\.\d+)?) SD/g))expect(Number(sd[1])).toBeLessThanOrEqual(10);
  }
 }
});
