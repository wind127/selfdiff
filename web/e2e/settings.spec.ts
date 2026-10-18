import {test,expect} from 'playwright/test';
test('slow settings load cannot overwrite values entered by the user',async({page})=>{
 await page.goto('/#token=e2e-only-token');await page.getByRole('button',{name:'体验示例',exact:true}).click();
 await page.route('**/api/settings?*',async route=>{
  await new Promise(resolve=>setTimeout(resolve,1000));
  await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({base_url:'',model:'',configured:false,key_configured:true})});
 });
 await page.getByRole('button',{name:'模型设置',exact:true}).click();
 await page.getByLabel('接口地址').fill('http://127.0.0.1:8771/v1');
 await page.getByLabel('模型名称').fill('my-chosen-model');
 await expect(page.getByText('当前进程：已设置密钥',{exact:true})).toBeVisible();
 await expect(page.getByLabel('接口地址')).toHaveValue('http://127.0.0.1:8771/v1');
 await expect(page.getByLabel('模型名称')).toHaveValue('my-chosen-model');
});
