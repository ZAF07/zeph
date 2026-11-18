/*
 * Visual acceptance test. Screenshots the running app and compares each page
 * with design/baseline/<ref>.png, pixel by pixel.
 *
 *   node design/compare.cjs                 every page in routes.json
 *   node design/compare.cjs Dashboard M-    only refs that start with these
 *
 * Env: BASE_URL (default http://localhost:3000), LIMIT (max % of differing
 * pixels, default 0.5), STATE_USER / STATE_ADMIN (Playwright storageState
 * files for a signed-in user and admin running on design fixtures).
 * Needs devDependencies: playwright, pixelmatch, pngjs.
 * Sign-in and sign-up mask the Clerk card on both sides and allow 8%, since
 * the Clerk widget cannot be matched pixel for pixel.
 * Writes design/.diff/<ref>.png (red = different) and exits 1 on any failure.
 */
const { chromium } = require('playwright');
const { PNG } = require('pngjs');
const fs = require('fs');
const path = require('path');
const here = __dirname;
const routes = JSON.parse(fs.readFileSync(path.join(here, 'routes.json'), 'utf8'));
const BASE = process.env.BASE_URL || 'http://localhost:3000';
const LIMIT = Number(process.env.LIMIT || 0.5);
const only = process.argv.slice(2);
const states = { user: process.env.STATE_USER, admin: process.env.STATE_ADMIN };

(async () => {
  const pixelmatch = (await import('pixelmatch')).default;
  const browser = await chromium.launch();
  fs.mkdirSync(path.join(here, '.diff'), { recursive: true });
  let failed = 0;
  for (const r of routes) {
    if (only.length && !only.some((p) => r.ref.startsWith(p))) continue;
    const ctx = await browser.newContext({
      viewport: { width: r.w, height: r.w === 390 ? 844 : 800 },
      deviceScaleFactor: 1,
      reducedMotion: 'reduce',
      storageState: states[r.auth] || undefined,
    });
    const page = await ctx.newPage();
    await page.goto(BASE + r.path, { waitUntil: 'networkidle' });
    await page.evaluate(() => document.fonts.ready);
    await page.addStyleTag({ content: '*{animation:none!important;transition:none!important;caret-color:transparent!important}' });
    const mask = (r.mask || []).map((s) => page.locator(s));
    const shot = PNG.sync.read(await page.screenshot({ fullPage: true, mask, maskColor: '#071922' }));
    await ctx.close();
    const base = PNG.sync.read(fs.readFileSync(path.join(here, 'baseline', r.ref + (r.mask ? '.masked.png' : '.png'))));
    const w = Math.min(shot.width, base.width);
    const h = Math.min(shot.height, base.height);
    const crop = (img) => { const o = new PNG({ width: w, height: h }); PNG.bitblt(img, o, 0, 0, w, h, 0, 0); return o; };
    const a = crop(base), b = crop(shot), d = new PNG({ width: w, height: h });
    const n = pixelmatch(a.data, b.data, d.data, w, h, { threshold: 0.1 });
    const pct = (100 * n) / (w * h);
    const dh = Math.abs(shot.height - base.height);
    const maskNote = r.mask ? ' (Clerk card masked)' : '';
    const ok = pct <= (r.mask ? Math.max(LIMIT, 8) : LIMIT) && (r.mask || dh <= 8);
    if (!ok) { failed++; fs.writeFileSync(path.join(here, '.diff', r.ref + '.png'), PNG.sync.write(d)); }
    console.log(`${ok ? 'PASS' : 'FAIL'}  ${r.ref.padEnd(34)} ${pct.toFixed(2)}% differs, height ${shot.height} vs ${base.height}${maskNote}`);
  }
  await browser.close();
  if (failed) { console.log(`\n${failed} page(s) drifted. Open design/.diff/<ref>.png to see where.`); process.exit(1); }
  console.log('\nAll pages match the design.');
})();
