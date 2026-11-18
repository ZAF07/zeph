# 02 — Redesign: shell (sidebar, fold, rail, phone bar and menu)

Status: completed

Lane: A. README slice: 1.

## Parent

`.scratch/redesign/PRD.md`

## What to build

The Dashboard frame every signed-in page sits in, for Users and Admins.

- **Sidebar (1280).** Sticky (`position: sticky; top: 0; height: 100vh`, with its own scroll if it's taller). It has the User section (Home, Memories, Check-ins, Account & privacy, Plan "To build") and, for Admins, the Admin section exactly as listed in `Admin.html`, including Overview and Plans with their "To build" tags. It ends with the AI notice and the signed-in person with Sign out.
- **Fold.** The fold button swaps the sidebar for the 76px icon rail in `Dashboard--menu-folded`. The choice is kept in `localStorage`, wrapped so blocked storage doesn't break the page. `?design=menu-folded` forces the rail in fixture mode.
- **Phone (below 900px).** A sticky top bar replaces the sidebar (`M-Dashboard`). The menu button opens the panel in `M-Menu`, pushing content down, and its icon becomes a cross. Choosing a link closes it. `?design=menu-open` forces it open.
- Admin menu items whose pages aren't redesigned yet still link to their current pages.
- This issue owns the sidebar and menu. Later issues don't edit them.

Refs: `Dashboard--menu-folded`, `M-Menu`. The page content inside the frame may still differ until issue 05, so for this issue compare the shell area. Record the % and the diff image, and confirm the only red is in the content area.

## Acceptance criteria

- [x] The sidebar, rail, phone bar and menu match the references (the diff images show red only in the content area until issue 05).
- [x] Test: folding is remembered across a reload, and works when storage is blocked.
- [x] Test: the phone menu opens, shows a cross, and closes when a link is chosen.
- [x] Admins see the Admin section and Users don't.
- [x] Every focusable element has the 2px cream outline with 2px offset. Chevron and hover use only the 150ms ease, and `prefers-reduced-motion` is respected.

## Blocked by

- `.scratch/redesign/issues/01-foundations.md`

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

- 2026-11-18 — Started on branch `redesign-02-shell` (own worktree). Zaf's answers to the three gaps the references don't draw:
  - **Folded rail for Admins:** User icons only, as drawn. Admins unfold the menu to reach admin pages.
  - **Phone menu for Admins:** the sidebar's Admin group, same styles, after Plan inside the menu's nav, before the person row.
  - **Links for pages not built yet:** Overview → `/admin` (redirects to Users until issue 14), Plans → `/admin/plans` and Plan → `/plan` (404 until issue 14).

- 2026-11-18 — Implemented on branch `redesign-02-shell`. Evidence below.

**Gaps Zaf answered during the work (beyond the three above).**
- Outfit never loaded: the font variable sat on `<body>` but the theme reads it on `<html>`. Issue 03 fixed it on main. This branch rebased onto it, and nothing here touches `app/layout.tsx`.
- `next.config.ts`: `devIndicators: false`. In dev, Next's "N" badge sat over the sidebar's Sign out, so the pixel test saw it. Dev only. This is a shared config file.
- A long name or email in the person row is cut with "…", with the full text in `title`. With real data the email ran 8px past the 240px sidebar and gave it a sideways scroll.
- The fold choice is also saved in a `zeph-menu-folded` cookie (a year, `samesite=lax`), and the Dashboard layout reads it. Before that, a folded User saw the full sidebar for about 320ms on every reload before it jumped to the rail. `localStorage` is still written and read, and a blocked one is ignored.

**Pixel test** (fixture dev server on WEB_PORT 3010, after rebasing onto main with the Outfit fix):
```
FAIL  Dashboard--menu-folded             13.05% differs, height 800 vs 1268
FAIL  M-Menu                             15.83% differs, height 844 vs 2448
```
As this issue says, the page content differs until issue 05, which re-runs both refs. In both diff images (`design/.diff/Dashboard--menu-folded.png`, `M-Menu.png`), the red is only in the content area. The shell area alone, cropped from the app and the baseline and run through the same pixelmatch (threshold 0.1):
```
Dashboard--menu-folded  rail     0,0 77x800    0 px differ (0.000%)
Dashboard               sidebar  0,0 241x800   0 px differ (0.000%)
M-Menu                  bar+menu 0,0 390x420   0 px differ (0.000%)
M-Dashboard             top bar  0,0 390x61    0 px differ (0.000%)
Admin (/admin/users)    sidebar  0,0 241x800 195 px differ (0.101%)
```
The Admin sidebar differs only in which item is marked. The reference marks Overview, but `/admin` redirects to Users until issue 14.

**Behaviour in a real browser** (fixture server, Playwright):
- Sticky, scrolled 1200px: the sidebar's top stays at 0 and its height is 800 (100vh). On a phone, the top bar's top stays at 0.
- Fold: the rail is 76px. After a reload, `localStorage` is `1` and the rail is drawn from the first frame. Sidebar widths over the reload frames were `[[4,76]]` on the real build and `[[8,76]]` in dev; before the cookie they were `[[6,240],[321,76]]`.
- Focus on the fold button: `solid 2px rgb(243,232,214)`, offset `2px`. Menu links: `transition 0.15s ease`, cream on hover. With reduced motion: `0s`.
- Phone: no sidebar. The menu button opens the panel, `aria-expanded=true`, with the cross. The page is pushed down to y=418. Choosing Memories goes to `/memories` and the menu closes.

**Tests.** New: `DashboardShell.test.tsx` (17) covers the sidebar menu, AI notice and person; Sign out; fold remembered across a reload; folding when storage is blocked; the fold cookie for the first paint and how it is saved; `?design=menu-folded` and `menu-open` in fixture mode only; the phone menu opening, cross, and closing on a link, on the wordmark and on a page change; the Admin section with Overview/Plans "To build" and "Admin" in place of the email; marking under admin sub-pages; and Users seeing no Admin section. `menu-fold.test.ts` (6) covers storage and cookie reads and writes when blocked. `choose-api-client.test.ts` now also checks the AI notice fixture.

**Checks** (web, after the rebase): `pnpm lint` clean, `pnpm format:check` "All matched files use Prettier code style!", `pnpm typecheck` clean, `pnpm test` 86 files / 544 tests passed.

**/run with real data** (production web container, flag off, real Clerk test users): no page errors.
- As a User on `/check-ins`: no Admin section. The long test email `run-check-1795009352-13459+clerk_test@example.com` shows as `run-check-1795009352…`. The sidebar's `scrollWidth` equals its `clientWidth` (239), with no sideways scroll. The phone menu's `scrollWidth` is 390.
- As an Admin on `/admin/users`: the Admin section is there with Users marked, and "Run check / Admin" is in the person row. In the phone menu, the Admin group comes after Plan, and choosing Persona goes to `/admin/persona` and closes the menu. The Admin section makes the sidebar taller than 800, so it scrolls inside, as designed.
- On a phone, the old Users table is wider than the screen. That is content for issue 10, not the shell.

**Chosen myself / unsure.**
- In the rail and both Sign out spots, the reference draws an `<a>`. This build uses a `<button>` styled the same (underline, colour, `aria-label`/`title`), because sign-out goes through Clerk's `useSignOut`, not a link.
- Added `aria-controls="phone-menu"` on the menu button. Hover goes cream with the 150ms ease on links, as the reference's `a:hover` does. The fold and menu buttons don't change on hover, as drawn.
- `getPlatformContent` now has a fixture in `design-fixtures/shell.ts` with the drawn AI notice. Its other fields are empty, except `message_retention_days: 30` (Account.html). Issues 04 and 09 may need the rest of its text.
- The loading placeholders in the person row keep their old shape and 4px radius, because no reference draws them.
- `SidebarAdminBadge` was deleted, because the reference shows "Admin" under the name instead.

**Existing tests changed.**
- `SidebarNav.test.tsx`: the `items` prop is gone, and the Admin list now has Overview and Plans with their tags.
- `SidebarAccount.test.tsx`: no initial letter; "Admin" now replaces the email instead of being a badge.
- `OnboardingGate.test.tsx`: uses `SidebarAccount` instead of the deleted badge.

**/code-review.**
- Standards: no hard breaches. The current-page check for User links is now one helper (`isUserItemCurrent`). Kept as they are: the two fold SVGs, since each is used once; the `action` and `className` props, which the two layouts need; and `browserStorage()`, the injected default.
- Spec: fixed the phone menu staying open after the wordmark or Back (it now closes on any page change), the missing 150ms ease on wordmark hover, and the fold flash (cookie, above). The `<a>` → `<button>` change is answered above.


## Completion

- Completed: 2026-11-18
- Commit: merge `1e89ef3` into main (branch `redesign-02-shell`: `bc04bea` shell, `9209318` code-review fixes, `9f51e3c` fold cookie, `d401de0` evidence and archive)
