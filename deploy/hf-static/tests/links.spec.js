import {test,expect} from '@playwright/test';
import examples from '../src/catalog.js';
test('external resources escape the embedded demo without replacing it',async({page,context,baseURL})=>{
 await page.setContent('<iframe title="Embedded static demo" src="'+baseURL+'/#/" sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox" style="width:1400px;height:1000px"></iframe>');
 const frame=page.frameLocator('iframe');await expect(frame.getByRole('heading',{name:'Speech-Eval',exact:true})).toBeVisible();
 for(const name of ['GitHub','Dataset','Report']){
  const link=frame.getByRole('link',{name:new RegExp(name)});await expect(link).toHaveAttribute('target','_blank');await expect(link).toHaveAttribute('rel',/noopener/);await expect(link).toHaveAttribute('rel',/noreferrer/);
  const destination=await link.getAttribute('href'),opened=context.waitForEvent('page');await link.click();const popup=await opened;
  await popup.waitForURL(destination,{waitUntil:'domcontentloaded'});
  await expect(frame.getByRole('heading',{name:'Speech-Eval',exact:true})).toBeVisible();expect(await popup.evaluate(()=>window.opener===null)).toBe(true);await popup.close();
 }
 await frame.getByRole('link',{name:/Gettysburg take02.*Mode B/}).click();
 await expect(frame.locator('#json-link')).toHaveAttribute('download',examples.find(e=>e.default).id+'.json');
});
