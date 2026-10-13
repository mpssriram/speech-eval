export function flaggedPhraseTests(test,expect,url,prefix,config){
 test.beforeEach(async({page})=>{await page.goto(url);await expect(page.getByTestId('waveform')).toHaveAttribute('data-ready','true');});
 const chips=page=>page.getByTestId('legend');
 const cards=page=>page.locator('.flaw-card:visible');
 const choose=async page=>{
  const labels=await page.locator('.flaw-card .type-chip').allTextContents();
  const label=labels.find(l=>labels.some(other=>other!==l));
  expect(label).toBeTruthy();
  return {label,count:labels.filter(l=>l===label).length,total:labels.length};
 };
 test(prefix+' filters one type, selects its first chronological card and dims other markers',async({page})=>{
  const {label,count,total}=await choose(page);
  await expect(chips(page).getByRole('button',{name:`All (${total})`,exact:true})).toHaveAttribute('aria-pressed','true');
  await page.screenshot({path:new URL(`../../reports/img/chips_${prefix}_all.png`,import.meta.url).pathname,fullPage:true});
  const chip=chips(page).getByRole('button',{name:`${label} (${count})`,exact:true});await chip.click();
  await expect(chip).toHaveAttribute('aria-pressed','true');await expect(cards(page)).toHaveCount(count);
  for(const text of await cards(page).locator('.type-chip').allTextContents())expect(text).toBe(label);
  const first=cards(page).first();await expect(first).toHaveAttribute('aria-current','true');
  await expect(first.locator('.flaw-title')).toHaveAttribute('aria-expanded','true');
  await expect(first.locator('.explanation')).toBeVisible();
  const inList=await first.evaluate(e=>{const a=e.getBoundingClientRect(),b=e.parentElement.getBoundingClientRect();return a.top>=b.top-2&&a.top<b.bottom;});expect(inList).toBe(true);
  const markers=await page.getByTestId('waveform').locator('[part~=region]').evaluateAll(es=>es.map(e=>({label:e.getAttribute('aria-label'),opacity:Number(getComputedStyle(e).opacity),visible:getComputedStyle(e).visibility})));
  for(const m of markers){expect(m.visible).toBe('visible');expect(m.opacity).toBe(m.label.startsWith(label+' ·')?1:0.18);}
  await page.screenshot({path:new URL(`../../reports/img/chips_${prefix}_filtered.png`,import.meta.url).pathname,fullPage:true});
 });
 test(prefix+' zero-count notice preserves filtering, reads config, closes and expires',async({page})=>{
  const {label,count}=await choose(page);await chips(page).getByRole('button',{name:`${label} (${count})`,exact:true}).click();
  const zero=chips(page).getByRole('button',{name:'Monotone (0)',exact:true});await expect(zero).toBeEnabled();
  await zero.focus();await zero.press('Space');
  const notice=page.getByRole('status');await expect(notice).toContainText('No Monotone regions were flagged in this recording.');
  await expect(notice).toContainText(`at least ${config.k.monotone} SD below the reference`);
  await expect(chips(page).getByRole('button',{name:`${label} (${count})`,exact:true})).toHaveAttribute('aria-pressed','true');await expect(cards(page)).toHaveCount(count);
  expect(await zero.evaluate(e=>getComputedStyle(e).borderStyle)).toBe('solid');
  await page.screenshot({path:new URL(`../../reports/img/chips_${prefix}_notice.png`,import.meta.url).pathname,fullPage:true});
  await notice.getByRole('button',{name:'Dismiss notice'}).click();await expect(notice).toHaveCount(0);
  await zero.focus();await zero.press('Enter');await expect(page.getByRole('status')).toBeVisible();
  await expect(page.getByRole('status')).toHaveCount(0,{timeout:7000});
  await page.setViewportSize({width:390,height:844});await zero.click();
  await expect(page.getByRole('status')).toContainText('No Monotone');
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:new URL(`../../reports/img/chips_${prefix}_mobile_notice.png`,import.meta.url).pathname,fullPage:true});
 });
 test(prefix+' All and repeated selection reset the list and waveform',async({page})=>{
  const {label,count,total}=await choose(page);const chip=chips(page).getByRole('button',{name:`${label} (${count})`,exact:true});
  await chip.focus();
  expect(await chip.evaluate(e=>getComputedStyle(e).outlineStyle)).toBe('solid');
  await chip.press('Enter');await expect(cards(page)).toHaveCount(count);
  await chip.press('Space');await expect(cards(page)).toHaveCount(total);
  const all=chips(page).getByRole('button',{name:`All (${total})`,exact:true});await expect(all).toHaveAttribute('aria-pressed','true');
  await chip.click();await all.click();await expect(cards(page)).toHaveCount(total);
  expect(await page.getByTestId('waveform').locator('[part~=region]').evaluateAll(es=>es.every(e=>getComputedStyle(e).opacity==='1'))).toBe(true);
 });
}
