import { chromium } from "playwright";

const [profileDir, statePath, role] = process.argv.slice(2);
const context = await chromium.launchPersistentContext(profileDir);
if (role === "admin") {
  await context.addCookies([
    { name: "zeph-design-as", value: "admin", domain: "localhost", path: "/" },
  ]);
}
await context.storageState({ path: statePath });
await context.close();
