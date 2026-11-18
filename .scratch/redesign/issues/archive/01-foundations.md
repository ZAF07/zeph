# 01 — Redesign: foundations (images, tokens, font, fixture mode, pixel test, sessions)

Status: completed

Lane: solo. Runs before any other redesign issue. README slice: 0.

## Parent

`.scratch/redesign/PRD.md`

## What to build

Set up everything the other issues build on. Do it in this order:

1. **Full-resolution images.** Zaf has put PNGs in `web/design/img-full/`, named to match the seven JPGs in `web/design/reference/img/`. Convert each one to a JPG of the same name at quality 90, keeping the size and framing (macOS: `sips -s format jpeg -s formatOptions 90 <in>.png --out <out>.jpg`). Replace the files in `reference/img/`, then delete `img-full/`. If any file is missing, misnamed or not 16:9, stop and ask.
2. **Rebuild the baselines once** with `shoot.cjs`, from the new images. This is the only baseline change allowed in the whole redesign.
3. **Theme and font.** Replace the `@theme` block with `web/design/tokens.css`. Load Outfit with `next/font/google` (weights 300, 400, 500, 600) as `--font-outfit`. Copy the images to the app's public `design/` folder.
4. **Design-fixture mode** (ADR 0018). It's on only when `NEXT_PUBLIC_DESIGN_FIXTURES=1`, read through the typed `env` module, and never reachable in a production build. The API client factory returns a fixture client with the same interface. Pages don't know about it. `/api/me` returns Alex (`alex@example.com`) as a User, or Zaf as an Admin when the browser has the `zeph-design-as=admin` cookie. The clock is fixed so the greeting reads "Good evening". `?design=` flags are read only in fixture mode. Set up **one fixture file per page area** (home, memories, check-ins, account, telegram, onboarding, admin-users, admin-tables, admin-forms, admin-cards, plan, overview), so later issues running in parallel each fill their own. This issue fills only what `/api/me` and the shell need.
5. **Pixel test wiring.** Add `playwright`, `pixelmatch` and `pngjs` as dev dependencies. Add `design/.diff/` to `.gitignore`. Leave `design/` out of ESLint and Prettier (its `.cjs` scripts stay plain JavaScript).
6. **Sign-in sessions for the test.** Add a script that makes `STATE_USER` and `STATE_ADMIN` Playwright storageState files by reusing the run-dashboard skill's `start-session.sh` (User, and Admin with the `zeph-design-as=admin` cookie added). It writes them outside the repo and prints the paths. Add a matching clean-up that deletes the Clerk test users. No credentials go in the repo.
7. **One source of truth.** Delete `docs/design/`. Change the "UI design" section of `CLAUDE.md` to point to `web/design/README.md` (and ADR 0018).

Existing pages will look broken after this. That's expected, and so is merging it to main.

Refs: none pass yet. This issue proves the test runs.

## Acceptance criteria

- [x] Seven JPGs in `reference/img/` come from the full-resolution PNGs at quality 90, `img-full/` is gone, and the baselines are rebuilt once with `shoot.cjs` (diff stat pasted).
- [x] The theme is exactly `tokens.css`, and no Tailwind default colour classes resolve.
- [x] Outfit loads through `next/font/google`.
- [x] With the flag on, `/api/me` returns Alex, or Zaf with the admin cookie. With the flag off, the real client is used. Covered by a test.
- [x] A production build doesn't contain the fixture client (checked and shown).
- [x] The session script makes both files outside the repo, and the clean-up removes the test users.
- [x] `node design/compare.cjs Dashboard` runs end to end and writes a diff image. FAIL is expected here.
- [x] `docs/design/` is deleted and `CLAUDE.md` points at `web/design/README.md`.
- [x] Before coding, the agent replied to the once-at-start prompt in `web/design/PROMPTS.md` and Zaf answered its questions.

## Blocked by

None. It can start immediately, once Zaf has put the PNGs in `web/design/img-full/`.

## Rules for every redesign issue

- Read `web/design/README.md` in full, then every reference file named here at both widths, before coding. The README wins on look, copy and behaviour. Where it and this issue differ, stop and ask. Its "When to stop and ask" list applies.
- Build so the computed styles equal the reference's inline styles. Take copy, sizes, colours, gaps and image CSS from the reference, never from memory. Use only the tokens (arbitrary values like `gap-[22px]` where no token exists).
- Never change anything in `web/design/` (`LIMIT`, masks, baselines, references), except the one image swap and baseline rebuild in issue 01.
- Own worktree (`make worktree-setup`), own branch, own PR. Run the pixel test with `BASE_URL=http://localhost:$WEB_PORT`, `NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev`, and the two session files from issue 01's script.
- **Parallel work.** Two agents work at once. Put this issue's sample data in its own fixture file for its page area, and don't edit another area's file. Only issue 01 edits the theme, font, fixture switch and pixel-test setup. Only issue 02 edits the sidebar and menu. Only issue 08 edits the middleware. If you need a change in one of those, stop and ask.
- Use the shared state parts from issue 03 (empty, loading, error, saved, confirm) for every state this issue's pages show (from issue 04 on).
- Existing behaviour, API calls, Clerk logic and tests stay as they are. Update a test only where the markup it checks has changed.
- Before the PR: `git fetch origin && git rebase origin/main`, then re-run this issue's pixel test and checks.

## Done when (for every redesign issue)

- [x] `node design/compare.cjs <this issue's refs>` prints PASS for each ref (pasted below), where the issue lists refs.
- [x] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` all pass (output pasted).
- [x] A `/run` check on the running stack with **real** data shows the pages work, and long names or many rows fit, or any that don't are reported.
- [x] Reported: anything the agent was unsure about or chose itself, and any existing test changed and why.
- [x] `/code-review` run, and findings fixed or answered.

## Comments

- 2026-11-18 — Implemented on branch `redesign-01-foundations` (worktree). Evidence below.

**Once-at-start prompt.** Answered in chat before coding (the one rule, how a page is finished, the build order, 4 questions). Zaf answered: replaced `how-stepping-stones.png` with a full-size one (now 2688×1504 like the rest), and approved the rest: Admin session = real Admin test user plus the cookie, production exclusion through a `NODE_ENV` check proven by grepping the build, and a clock module with a one-line change in `DashboardHome`.

**Images.** All seven PNGs were 2688×1504 and named to match. Converted with `sips -s format jpeg -s formatOptions 90`, replaced `reference/img/*.jpg` (was 1344×751), deleted `img-full/`. Note: 2688×1504 is ratio 1.787, not exactly 16:9 (1.778), the same ratio as the old 1344×751 JPGs, so the framing is unchanged. Copied to `web/public/design/`.

**Baselines rebuilt once** with `node design/shoot.cjs` (all heights unchanged). Diff stat: `41 files changed` (every `baseline/*.png`, binary). Pages with no images also changed by about 0.6% (Account 0.610%, States 0.506%, AdminUsers 0.591%), because this machine's Playwright Chromium draws text slightly differently from whatever made the old baselines. With the old baselines, every page would have failed the 0.5% limit on this machine.

**Theme.** `globals.css` imports `design/tokens.css` as it is (so they can't drift) and sets the reference's page-wide base styles (body 16px/1.55/300, link colours, cream focus outline, reduced motion). `src/app/theme.test.ts` compiles the theme with Tailwind and shows `bg-cream`/`text-ink` resolve while `bg-red-500`, `text-gray-700`, `border-slate-200` and `bg-blue-600` do not. Outfit loads in `layout.tsx` through `next/font/google` (weights 300–600, `--font-outfit`). The built CSS has no default palette variables (0 found).

**Fixture mode.** `env.designFixtures` (`designFixturesOn`: flag `=1` and not production). `chooseApiClient` returns `createFixtureClient` (`lib/design-fixtures/`, one file per area plus `shell.ts` for `/api/me`). Calls without a fixture reject with "No design fixture for <name> yet". `?design=` flags are read through `hasDesignFlag` (fixture mode only). Clock: `currentTime()` fixed at Tue 17 Nov 2026, 8:00 PM Singapore. Tests: `choose-api-client.test.ts` (Alex; Zaf with cookie; no fetch; real client when off), `env.test.ts`, `clock.test.ts`, `design-flags.test.ts`. In the running app (fixture dev server), Home showed Alex / alex@example.com, "Tuesday, 17 November", "Good evening", and `/admin/users` showed Zaf, with **0 requests to the backend**.

**Production build.** `NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm build`, then `grep -rlE 'design-alex|No design fixture for|zeph-design-as' .next` gives **0** files (the control string `/api/me` is found). Without the literal `NODE_ENV` check in `chooseApiClient`, the same grep gave 2 files, so the check stays (explained in its docstring).

**Sessions.** `.claude/skills/run-dashboard/scripts/design-sessions.sh` runs `start-session.sh` for user and admin, saves storageState to `$TMPDIR/zeph-design-sessions/<worktree>/{user,admin}.json` (admin has the `zeph-design-as=admin` cookie), and prints `export STATE_USER=…` / `STATE_ADMIN=…`. `design-sessions-cleanup.sh` deleted both Clerk users (`"deleted":true`, then GET → 404), `DELETE 1` ×2 rows, 0 `run-check-%` users left, folder gone. Documented in the run-dashboard SKILL.md. The stack must run with real data while sessions are made, because `sign-in.mjs` waits for a real `/api/me`.

**Pixel test** (fixture dev server on WEB_PORT 3010, after code-review fixes):
```
FAIL  Dashboard                          12.33% differs, height 800 vs 1268
FAIL  Dashboard--menu-folded             13.79% differs, height 800 vs 1268
2 page(s) drifted. Open design/.diff/<ref>.png to see where.
```
`design/.diff/Dashboard.png` and `Dashboard--menu-folded.png` were written, and git ignores them. FAIL is expected here.

**docs/design** deleted. CLAUDE.md "UI design" now points to `web/design/README.md` and ADR 0018.

**Checks** (web): `pnpm lint` clean, `pnpm format:check` "All matched files use Prettier code style!", `pnpm typecheck` clean, `pnpm test` 72 files / 500 tests passed.

**/run with real data.** Production web container (flag off) with real test users: Home showed "Run check", today's real date and the real Telegram state. `/admin/users` listed the real users through the backend (3 backend calls each). The old pages look broken on the new theme, as the issue expects. A long email wraps in the old Users table, which is for issue 10 to handle.

**Chosen myself / unsure.**
- Zaf's email `zaf@example.com` is not in any reference. It isn't shown, because the admin sidebar shows "Admin".
- Alex's other `Me` fields come from Account.html (Singapore, Asia/Singapore, memory changed in chat 12 Nov, stickers on).
- `.brand-stripe` was removed from `globals.css` because its colours no longer exist. The class names stay in Sidebar/AuthLayout/onboarding for their issues to remove.
- The greeting depends on the home fixture's `time_zone`. A note was added to issue 05.

**Existing tests changed.** None. **New lib files:** `choose-api-client.ts`, `clock.ts`, `design-flags.ts`, `design-fixtures/*`.

**/code-review.** Standards findings: the `process.env.NODE_ENV` read outside `env` is kept on purpose (the build needs it, documented). `DESIGN_AS_COOKIE` and `DESIGN_FIXTURE_NOW` are now private. Docstrings rewrapped. The cookie name is cross-referenced between the TS and the script. The `Proxy` stays, so new `ApiClient` calls need no fixture edits. Spec findings: the 16:9 ratio point is noted above, and the time zone is noted for issue 05. The extra base styles are needed by the README Behaviour section and only issue 01 may edit the theme.

## Completion

- Completed: 2026-11-18
- Commit: <to be filled in after merge>
