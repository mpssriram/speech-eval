import {test,expect} from '@playwright/test';
test('live landing and hash examples navigate, then upload keeps the existing flow',async({page})=>{
 await page.goto('/#/');
 await expect(page.getByRole('heading',{name:'Speech-Eval',exact:true})).toBeVisible();
 await page.getByRole('link',{name:/Gettysburg take02.*Mode B/}).click();
 await expect(page).toHaveURL(/#\/example\//);
 await expect(page.getByTestId('overall-score')).toBeVisible();
 await page.goBack();await expect(page.getByRole('heading',{name:'Speech-Eval',exact:true})).toBeVisible();
 await page.getByRole('link',{name:'Upload a recording',exact:true}).click();
 await expect(page).toHaveURL(/#\/upload/);
 await expect(page.getByLabel('Audio file',{exact:true})).toBeVisible();
 await expect(page.getByRole('dialog')).toHaveCount(0);
 await page.getByRole('button',{name:'Speech Eval home'}).click();
 await expect(page.getByRole('heading',{name:'Speech-Eval',exact:true})).toBeVisible();
});
