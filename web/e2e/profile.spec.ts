import {test,expect} from 'playwright/test';

test('demo insights have evidence, user revisions and period snapshots',async({page})=>{
  await page.goto('/#token=e2e-only-token');
  await page.getByRole('button',{name:'体验示例',exact:true}).click();
  await expect(page.getByRole('heading',{name:'你正在形成怎样的自己'})).toBeVisible();
  await page.getByRole('button',{name:'有时，比较方案占用了动手的时间',exact:true}).click();
  const dialog=page.getByRole('dialog');
  await expect(dialog.getByText('我总想把方案比较完再动手，结果这一周还没有开始。',{exact:true})).toBeVisible();
  await dialog.getByLabel('你的表述').fill('只在需求不清楚时发生。');
  await dialog.getByRole('button',{name:'部分符合',exact:true}).click();
  await dialog.getByRole('button',{name:'保存我的修订',exact:true}).click();
  await expect(dialog.getByText('已保存你的修订')).toBeVisible();
  await dialog.getByRole('button',{name:'关闭详情'}).click();
  await expect(page.getByText('只在需求不清楚时发生。',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'时间比较',exact:true}).click();
  await page.getByRole('button',{name:'比较两个时期',exact:true}).click();
  await expect(page.getByText('分析完成',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'保存这次比较',exact:true}).click();
  await expect(page.getByText('快照已保存')).toBeVisible();
});

test('share card includes only manually selected public text',async({page})=>{
 await page.goto('/#token=e2e-only-token');await page.getByRole('button',{name:'体验示例',exact:true}).click();
 await page.getByRole('button',{name:'制作分享卡',exact:true}).click();
 const dialog=page.getByRole('dialog');
 await dialog.getByLabel('有时，比较方案占用了动手的时间',{exact:true}).check();
 await dialog.getByLabel('准备公开的文字').fill('我正在学习先验证一个小场景。<script>bad()</script>');
 await dialog.getByLabel('我已检查这些文字，愿意导出分享').check();
 const downloadPromise=page.waitForEvent('download');
 await dialog.getByRole('button',{name:'下载分享卡',exact:true}).click();
 const download=await downloadPromise;const path=await download.path();
 const fs=await import('node:fs/promises');const content=await fs.readFile(path!,'utf8');
 expect(content).not.toContain('<script>');expect(content).not.toContain('我总想把方案比较完再动手');
 expect(content).toContain('合成示例');
});
