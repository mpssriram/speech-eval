/** Missing text separators join words for selection, copy and assistive readers. */
export function transcriptTextTest(test,expect,route){
 test('transcript selection contains normal spaces between interactive words',async({page})=>{
  await page.goto(route);
  const transcript=page.locator('.transcript > div');
  await expect(transcript.locator('button').first()).toBeVisible();
  const expected=(await transcript.locator('button').allTextContents()).join(' ');
  expect(expected).toContain('Four score and seven years ago');
  expect(await transcript.textContent()).toBe(expected);
  const selected=await transcript.evaluate(element=>{
   const selection=window.getSelection(),range=document.createRange();
   range.selectNodeContents(element);selection.removeAllRanges();selection.addRange(range);
   const text=selection.toString();selection.removeAllRanges();return text;
  });
  expect(selected).toBe(expected);
  await transcript.locator('button').nth(10).click();
  expect(await transcript.textContent()).toBe(expected);
 });
}
