import {test,expect} from '@playwright/test';

// A static Space runs inside an iframe. External pages must escape that frame.
test('GitHub, dataset and report open separately without replacing the embedded demo',async({page,context,baseURL})=>{
  await page.setContent(`<iframe title="Embedded static demo" src="${baseURL}/" sandbox="allow-scripts allow-same-origin allow-popups allow-popups-to-escape-sandbox" style="width:1400px;height:1000px"></iframe>`);
  const frame=page.frameLocator('iframe');
  await expect(frame.locator('#results')).toBeVisible();
  for(const name of ['GitHub','Dataset','Report']){
    const link=frame.getByRole('link',{name:new RegExp(name)});
    await expect(link).toHaveAttribute('target','_blank');
    await expect(link).toHaveAttribute('rel',/noopener/);
    await expect(link).toHaveAttribute('rel',/noreferrer/);
    const destination=await link.getAttribute('href');
    const opened=context.waitForEvent('page');await link.click();const popup=await opened;
    await popup.waitForURL(destination,{waitUntil:'domcontentloaded'});
    await expect(frame.locator('#title')).toHaveText('Gettysburg take02 · Mode B');
    expect(await popup.evaluate(()=>window.opener===null)).toBe(true);
    await popup.close();
  }
  // The stored JSON link remains a same-origin download.
  await expect(frame.locator('#json-link')).toHaveAttribute('download','8cbb735fbbb8.json');
});
