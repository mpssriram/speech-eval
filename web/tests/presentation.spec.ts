import {test,expect} from '@playwright/test';
test('live frozen job uses fixed point explanations without changing evidence',async({page})=>{
 await page.goto('/results/6d8cbd6dec22ffc8f7827ebc');
 await expect(page.getByTestId('overall-score')).toBeVisible();
 for(const text of await page.locator('.explanation').allTextContents()){
  expect(text).not.toMatch(/\d[eE][+-]\d/);
  expect(text).not.toMatch(/previous take (?:pause|average|vary)\b/);
  expect(text).toContain('What happened:');
   expect(text).toContain('Measured:');
   expect(text).toContain('How far off:');
   expect(text).toContain('Why it matters:');
  expect(text).not.toMatch(/your previous take|speaker norms|intelligibility/);
   for(const sd of text.matchAll(/(?<![\d.])(\d+(?:\.\d+)?) SD/g))expect(Number(sd[1])).toBeLessThanOrEqual(10);
 }
});
for(const width of [375,768,1280,1440,1920]){
 test('live results fit '+width+'px with wrapping chips and visible short markers',async({page})=>{
  await page.setViewportSize({width,height:1080});
  await page.goto('/results/0aae3748f747b13e89697e17');
  await expect(page.getByTestId('waveform')).toHaveAttribute('data-ready','true');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  const markerWidths=await page.getByTestId('waveform').locator('[part~="region"]').evaluateAll(es=>es.map(e=>e.getBoundingClientRect().width));
  expect(Math.min(...markerWidths)).toBeGreaterThanOrEqual(4);
  const chips=await page.locator('.lane>div').evaluateAll(es=>es.map(e=>({client:e.clientWidth,scroll:e.scrollWidth})));
  for(const chip of chips)expect(chip.scroll).toBeLessThanOrEqual(chip.client);
  const columns=await page.locator('.workspace').evaluate(e=>getComputedStyle(e).display);
  expect(columns).toBe(width>=1280?'grid':'flex');
 });
}
