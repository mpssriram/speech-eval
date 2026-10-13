import {test,expect} from '@playwright/test';
for(const width of [375,768,1280,1440,1920]){
 test('static results fit '+width+'px with wrapping chips and visible short markers',async({page})=>{
  await page.setViewportSize({width,height:1080});await page.goto('/');
  await expect(page.getByTestId('waveform')).toHaveAttribute('data-ready','true');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  for(const size of await page.locator('.lane>div').evaluateAll(es=>es.map(e=>({client:e.clientWidth,scroll:e.scrollWidth}))))expect(size.scroll).toBeLessThanOrEqual(size.client);
  expect(Math.min(...await page.getByTestId('waveform').locator('[part~="region"]').evaluateAll(es=>es.map(e=>e.getBoundingClientRect().width)))).toBeGreaterThanOrEqual(4);
 });
}
