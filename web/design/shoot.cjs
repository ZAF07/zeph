const { chromium } = require('playwright');
const fs = require('fs');
(async()=>{
const man = JSON.parse(fs.readFileSync(__dirname+'/manifest.json','utf8'));
const b = await chromium.launch();
const out=[];
for (const [name,w] of man) {
  const ctx = await b.newContext({ viewport: { width: w, height: w===390?844:800 }, deviceScaleFactor: 1 });
  const p = await ctx.newPage();
  await p.goto('file://'+__dirname+'/reference/'+name+'.html');
  await p.evaluate(()=>document.fonts.ready);
  await p.waitForTimeout(150);
  const h = await p.evaluate(()=>document.documentElement.scrollHeight);
  const ov = await p.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+1);
  await p.screenshot({ path: __dirname+'/baseline/'+name+'.png', fullPage: true });
  if (await p.locator('[data-clerk-card]').count()) await p.screenshot({ path: __dirname+'/baseline/'+name+'.masked.png', fullPage: true, mask: [p.locator('[data-clerk-card]')], maskColor: '#071922' });
  out.push(name+' '+w+'x'+h+(ov?' HOVERFLOW':''));
  await ctx.close();
}
await b.close();
console.log(out.join('\n'));

})();
