import {test,expect} from 'playwright/test';
test('an active job remains visible and cancellable after navigation and refresh',async({page})=>{
 await page.goto('/#token=e2e-only-token');await page.getByRole('button',{name:'导入我的会话',exact:true}).click();
 const data={conversations:[{id:'recovery',title:'任务恢复',messages:[{id:'u',role:'user',content:'我喜欢先做小版本。E2E_DELAY'}]}]};
 await page.getByLabel('选择会话文件').setInputFiles({name:'recovery.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(data))});
 await page.getByRole('button',{name:'确认导入',exact:true}).click();
 await page.getByRole('button',{name:'模型设置',exact:true}).click();
 await page.getByLabel('接口地址').fill('http://127.0.0.1:8771/v1');await page.getByLabel('模型名称').fill('synthetic-test-only');await page.getByRole('button',{name:'保存并测试连接'}).click();
 await page.getByRole('button',{name:'个人档案',exact:true}).click();await page.getByText('选择分析范围',{exact:true}).click();await page.getByRole('button',{name:'预览本次分析'}).click();await page.getByRole('button',{name:'开始分析所选资料'}).click();
 await page.getByRole('button',{name:'模型设置',exact:true}).click();await page.reload();
 await expect(page.getByLabel('接口地址')).toBeVisible();
 await expect(page.getByRole('button',{name:'取消后台任务',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'取消后台任务',exact:true}).click();
 await expect(page.getByRole('button',{name:'取消后台任务',exact:true})).toHaveCount(0);
 await page.getByRole('button',{name:'个人档案',exact:true}).click();
 await expect(page.getByText('任务已取消',{exact:true})).toBeVisible();
});
