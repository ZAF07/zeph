import { chromium } from "playwright";

const [userId, profileDir] = process.argv.slice(2);
const response = await fetch("https://api.clerk.com/v1/sign_in_tokens", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${process.env.CLERK_SECRET_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ user_id: userId }),
});
const { token } = await response.json();

const context = await chromium.launchPersistentContext(profileDir);
const page = await context.newPage();
await page.goto(`http://localhost:3000/sign-in?__clerk_ticket=${token}`);
await page.waitForURL((url) => !url.pathname.startsWith("/sign-in"), {
  timeout: 30000,
});
for (let attempt = 0; attempt < 10; attempt++) {
  const me = page.waitForResponse((r) => r.url().endsWith("/api/me"), {
    timeout: 15000,
  });
  await page.goto("http://localhost:3000/");
  if ((await me).ok()) {
    break;
  }
  await page.waitForTimeout(2000);
}
await context.close();
