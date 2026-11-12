import { chromium } from "playwright";

const [path, screenshot, width = "1280", profileDir] = process.argv.slice(2);
const context = await chromium.launchPersistentContext(profileDir, {
  viewport: { width: Number(width), height: 900 },
});
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(String(error)));
page.on("dialog", (dialog) => dialog.accept());

await page.goto(`http://localhost:3000${path}`);
await page.waitForLoadState("networkidle");
await page.screenshot({ path: screenshot });
console.log(`opened ${page.url()}, screenshot ${screenshot}`);
console.log("page errors:", errors.length ? errors : "none");
await context.close();
