import fs from 'node:fs';
import examples from '../src/catalog.js';
const rows=JSON.parse(fs.readFileSync(new URL('../../tests/fixtures/explanation_snapshots.json',import.meta.url)));
const root=new URL('../../deploy/hf-static/public/',import.meta.url);
const example=examples.find(e=>e.default);
const base=JSON.parse(fs.readFileSync(new URL(example.analysis,root)));
const alignment=JSON.parse(fs.readFileSync(new URL(example.alignment,root)));
/** Each mode exercises all seven templates in the real shared card component. */
export function explanationCardTests(test,expect,prefix){
 for(const mode of ['A','B','C'])test(prefix+' '+mode+' card snapshots, bold labels and SD tooltip',async({page})=>{
  const cases=rows.filter(r=>r.mode===mode);
  await page.route('**/'+example.analysis,route=>route.fulfill({json:{...base,mode,regions:cases.map(r=>r.region)}}));
  await page.route('**/'+example.alignment,route=>route.fulfill({json:{...alignment,words:[{i:0,text:'larger',start:65.7,end:66.1},{i:1,text:'sense',start:66.2,end:67.13}]}}));
  await page.goto('/#/example/'+example.id);
  await expect(page.getByTestId('waveform')).toHaveAttribute('data-ready','true');
  const cards=page.getByTestId('flaw-card');await expect(cards).toHaveCount(7);
  for(let i=0;i<cases.length;i++){
   const card=cards.nth(i),lines=cases[i].expected.split('\n');
   await card.locator('.flaw-title').click();
   await expect(card.locator('.flaw-title')).toHaveText(lines[0]);
   const facts=card.locator('.explanation p');await expect(facts).toHaveCount(lines.length-1);
   for(let j=0;j<lines.length-1;j++){
    const paragraph=facts.nth(j);
    await expect(paragraph.locator('.fact-label')).toHaveText(lines[j+1].split(':')[0]+':');
    await expect(paragraph).toContainText(lines[j+1]);
    expect(await paragraph.locator('.fact-label').evaluate(e=>Number(getComputedStyle(e).fontWeight))).toBeGreaterThanOrEqual(700);
   }
   const help=card.getByRole('button',{name:'What is SD?',exact:true});
   await help.focus();await help.press('Enter');
   await expect(card.getByRole('tooltip')).toHaveText('How far from the reference average, in standard deviations. Bigger means more unusual. Flags start at '+cases[i].threshold.toFixed(1)+' SD.');
   await help.press('Enter');await expect(card.getByRole('tooltip')).toBeHidden();
   expect(await card.innerText()).not.toMatch(/\d(?:\.\d*)?[eE][+-]?\d/);
  }
 });
}
