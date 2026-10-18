import {test,expect} from 'playwright/test';

test('personal data stays separate and imports only after preview',async({page})=>{
  await page.goto('/#token=e2e-only-token');
  await page.getByRole('button',{name:'导入我的会话',exact:true}).click();
  await expect(page.getByRole('heading',{name:'把你的会话放在一起'})).toBeVisible();
  const data={conversations:[{id:'test-import',title:'合成测试会话',messages:[{id:'u',role:'user',content:'我喜欢先做小版本。'}]}]};
  await page.getByLabel('选择会话文件').setInputFiles({name:'synthetic.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(data))});
  await expect(page.getByText('预览完成，尚未导入')).toBeVisible();
  await page.getByRole('button',{name:'确认导入',exact:true}).click();
  await expect(page.getByText('合成测试会话', {exact:true})).toBeVisible();
  await page.getByLabel('搜索原话').fill('小版本');
  await expect(page.getByText('我喜欢先做小版本。',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'个人档案',exact:true}).click();
  await expect(page.getByText('还没有关于你的结论')).toBeVisible();
  await expect(page.getByText('你在意的，是有人真正用起来')).toHaveCount(0);
});
