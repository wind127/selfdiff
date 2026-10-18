import {test,expect} from 'playwright/test';
test('real workspace completes import-model-evidence-revision-compare-export-delete flow',async({page})=>{
 await page.goto('/#token=e2e-only-token');await page.getByRole('button',{name:'导入我的会话',exact:true}).click();
 const data={conversations:[{id:'jan',title:'一月测试',messages:[{id:'u',role:'user',content:'我在一月习惯先做小版本。',timestamp:'2026-01-05T08:00:00Z'}]},{id:'sep',title:'九月测试',messages:[{id:'u',role:'user',content:'我在九月依然会先做小版本。',timestamp:'2026-09-05T08:00:00Z'}]}]};
 await page.getByLabel('选择会话文件').setInputFiles({name:'synthetic.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(data))});
 await page.getByRole('button',{name:'确认导入',exact:true}).click();
 await page.getByRole('button',{name:'模型设置',exact:true}).click();
 await page.getByLabel('接口地址').fill('http://127.0.0.1:8771/v1');await page.getByLabel('模型名称').fill('synthetic-test-only');
 await page.getByRole('button',{name:'保存并测试连接'}).click();await expect(page.getByText('连接成功。连接测试没有发送任何会话。')).toBeVisible();
 await page.getByRole('button',{name:'个人档案',exact:true}).click();await page.getByText('选择分析范围',{exact:true}).click();
 await page.getByRole('button',{name:'预览本次分析'}).click();await page.getByRole('button',{name:'开始分析所选资料'}).click();
 await expect(page.getByText('分析完成',{exact:true})).toBeVisible({timeout:15000});
 await page.getByRole('button',{name:'小规模验证让你开始行动',exact:true}).click();
 const dialog=page.getByRole('dialog');await expect(dialog.getByText('我在一月习惯先做小版本。',{exact:true})).toBeVisible();
 await dialog.getByLabel('你的表述').fill('先验证小场景对这两次项目有效。');await dialog.getByRole('button',{name:'保存我的修订'}).click();await expect(dialog.getByText('已保存你的修订')).toBeVisible();await dialog.getByRole('button',{name:'关闭详情'}).click();
 const filePromise=page.waitForEvent('download');await page.getByRole('button',{name:'导出 JSON',exact:true}).click();const download=await filePromise;const path=await download.path();const fs=await import('node:fs/promises');const exported=await fs.readFile(path!,'utf8');expect(exported).toContain('先验证小场景对这两次项目有效。');expect(exported).not.toContain('_e2e_not_a_real_key_');
 await page.getByRole('button',{name:'时间比较',exact:true}).click();await page.getByLabel('我同意将两个时期内的用户发言发送到已配置的模型进行分析').check();await page.getByRole('button',{name:'比较两个时期',exact:true}).click();await expect(page.getByText('分析完成',{exact:true})).toBeVisible({timeout:15000});await page.getByRole('button',{name:'保存这次比较'}).click();await expect(page.getByText('快照已保存')).toBeVisible();
 await page.getByRole('button',{name:'会话资料',exact:true}).click();await page.getByRole('button',{name:'删除 一月测试',exact:true}).click();await page.getByRole('button',{name:'删除会话与派生结论'}).click();await expect(page.getByRole('dialog')).toHaveCount(0);await page.getByRole('button',{name:'个人档案',exact:true}).click();await expect(page.getByText('还没有关于你的结论')).toBeVisible();
});
