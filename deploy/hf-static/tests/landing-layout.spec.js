import {test,expect} from '@playwright/test';
for(const width of [375,768,1280,1440,1920]){
 test('landing and static upload fit '+width+'px without horizontal scrolling',async({page})=>{
  await page.setViewportSize({width,height:1000});await page.goto('/#/');
  await expect(page.getByRole('heading',{name:'Speech-Eval',exact:true})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  if(width>=1280)expect(await page.evaluate(()=>document.documentElement.scrollHeight)).toBeLessThanOrEqual(1000);
  await page.getByRole('link',{name:'Upload a recording',exact:true}).click();
  const dialog=page.getByRole('dialog');await expect(dialog).toBeVisible();
  expect(await dialog.evaluate(e=>e.scrollWidth<=e.clientWidth)).toBe(true);
  await page.keyboard.press('Tab');expect(await dialog.evaluate(e=>e.contains(document.activeElement))).toBe(true);
  await page.mouse.click(2,2);await expect(dialog).toHaveCount(0);
 });
}
