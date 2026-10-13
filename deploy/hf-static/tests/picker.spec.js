import {test,expect} from '@playwright/test';
function luminance(rgb){return rgb.slice(0,3).map(v=>{const n=v/255;return n<=.04045?n/12.92:((n+.055)/1.055)**2.4;}).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);}
for(const scheme of ['light','dark']){
 test(`recording options stay readable with ${scheme} browser settings`,async({page})=>{
  await page.emulateMedia({colorScheme:scheme});await page.goto('/');await expect(page.locator('#results')).toBeVisible();
  const styles=await page.locator('#example option').evaluateAll(options=>options.map(option=>{const s=getComputedStyle(option);return {color:s.color,background:s.backgroundColor};}));
  expect(styles).toHaveLength(19);
  for(const style of styles){
   const rgb=value=>value.match(/[\d.]+/g).map(Number),fg=rgb(style.color),bg=rgb(style.background);
   // Native popups must have an explicit opaque backing for their text colour.
   expect(bg.length===3||bg[3]===1).toBe(true);
   const a=luminance(fg),b=luminance(bg);expect((Math.max(a,b)+.05)/(Math.min(a,b)+.05)).toBeGreaterThanOrEqual(4.5);
  }
  // The visual fix must retain native keyboard selection and the same stored take.
  const picker=page.locator('#example');await picker.focus();await picker.press('Home');await picker.press('ArrowDown');await picker.press('Enter');
  await expect(page.locator('#title')).toHaveText('Gettysburg take02 · Mode A');
 });
}
