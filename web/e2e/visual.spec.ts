import {test,expect} from 'playwright/test';
import path from 'node:path';
test('demo remains readable at desktop and phone sizes with keyboard dialogs',async({page})=>{
 await page.setViewportSize({width:1440,height:1000});
 await page.goto('/#token=e2e-only-token');await page.getByRole('button',{name:'体验示例',exact:true}).click();
 await expect(page.getByRole('heading',{name:'你正在形成怎样的自己'})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 await page.screenshot({path:path.resolve('../docs/images/demo.png'),fullPage:true});
 await page.setViewportSize({width:375,height:812});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 await page.screenshot({path:path.resolve('../docs/images/demo-mobile.png'),fullPage:true});
 await page.getByRole('button',{name:'有时，比较方案占用了动手的时间',exact:true}).click();
 await expect(page.getByRole('dialog')).toBeVisible();
 await page.keyboard.press('Escape');await expect(page.getByRole('dialog')).toHaveCount(0);
});
