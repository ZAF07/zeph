# 08 — Redesign: public pages (Landing, How It Works, `/` routing)

Status: completed

Lane: B. README slice: 9.

## Parent

`.scratch/redesign/PRD.md`

## What to build

- **Landing** at `/` when signed out, to `Landing` and `M-Landing`, with the `hero-pavilion.jpg` and `faq-doorway.jpg` CSS from the README copied exactly.
- **How It Works** at `/how-it-works`, to `HowItWorks` and `M-HowItWorks`, with the `how-stepping-stones.jpg` CSS.
- **Routing.** `/` and `/how-it-works` become public in the middleware (this issue owns the middleware). `/` shows Landing when signed out and Home when signed in.
- **Public header on a phone.** The nav links collapse behind the menu button, as in `M-Landing--nav-open`.

Refs: `Landing`, `M-Landing`, `HowItWorks`, `M-HowItWorks`. `M-Landing--nav-open` isn't in `routes.json`, so open the menu in a browser and compare it with its baseline by eye, and report.

## Acceptance criteria

- [x] All four refs PASS, and the nav-open state is checked against its baseline.
- [x] Test: `/` renders Landing signed out and Home signed in.
- [x] Every other signed-in route is still protected (checked in `/run`).

## Blocked by

- `.scratch/redesign/issues/06-sign-in-and-sign-up.md`

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

- 2026-11-19: implemented on branch `redesign-08-public-pages` in its own worktree (ports 3020/8020/5452). The evidence is below.

**Built.**
- **Routing.**
  - Home moved out of the `(dashboard)` route group into `app/page.tsx`. It shows `Landing` signed out and `DashboardHome` signed in.
  - The signed-in frame the `(dashboard)` layout drew (sign-in redirect, fold cookie, `DashboardShell`, `OnboardingGate`) is now `DashboardFrame`. Both the layout and `/` use it.
  - The middleware's public list moved to `lib/auth/public-routes.ts` and gained `/` and `/how-it-works`. It has tests (`public-routes.test.ts`): 7 public paths, plus 8 protected ones, including `/how-it-works-secret`.
- **Pages.** `Landing` and `HowItWorks` are made of small parts:
  - `SiteHero`, `SiteHeader`, `SiteFooter`, `SectionIntro`, `Eyebrow`;
  - `LandingConversation`, `LandingChatBubble`, `LandingDay`, `LandingPricing`, `LandingPlan`, `LandingFaq`, `HowItWorksStep`;
  - `site-links.ts`, `site-styles.ts`, `site-backgrounds.ts`. The README's image CSS is copied exactly into `site-backgrounds.ts`.
- **Phone header.** `SiteHeader` wraps issue 06's `PublicHeader`.
  - Below 900px, "Log in" and the arrow on "Get Started" hide, and the menu button shows.
  - The button opens the `M-Landing--nav-open` panel under the header, which pushes the page down. Its icon becomes a cross, and choosing a link closes the panel.
- **No fixture file.** These pages only show fixed copy and call no API.
- **Content-box.** Some reference elements are content-box, where Tailwind is border-box: the chat bubbles, the day timeline and the phone menu links. They carry `box-content` so their computed size equals the reference's.

**Pixel test.** Production web container, final code:
```
PASS  Landing                            0.03% differs, height 4228 vs 4228
PASS  M-Landing                          0.04% differs, height 6099 vs 6099
PASS  HowItWorks                         0.03% differs, height 2293 vs 2293
PASS  M-HowItWorks                       0.02% differs, height 3770 vs 3770
PASS  Login                              0.19% differs, height 800 vs 800 (Clerk card masked)
PASS  M-Login                            1.62% differs, height 982 vs 984 (Clerk card masked)
FAIL  Signup                             12.40% differs, height 885 vs 800 (Clerk card masked)   <- issue 06's accepted FAIL, unchanged
```
- **Fixture dev server** (`NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev`, issue 01's session files). The four refs above PASS with the same numbers. `/` still draws Home correctly after the move:
  ```
  PASS  Dashboard 0.01%, Dashboard--menu-folded 0.00%, M-Dashboard 0.01%, M-Menu 0.01% (heights equal)
  ```
- **Nav-open.** A Playwright script opens the menu at 390 and diffs the page against `baseline/M-Landing--nav-open.png` with `compare.cjs`'s rules: `0.03% differs, height 6357 vs 6357`. By eye it matches the reference: the cross icon, five links with Log in last, the dark panel and the hero pushed down. Choosing FAQ closes the panel and lands on `/#faq`. From the menu, Pricing, FAQ and Conversations each land with their section's top at 0.

**Checks** (`make check`):
- Python: ruff "All checks passed!", ruff format "487 files already formatted", mypy "no issues found in 186 source files", pytest "1319 passed".
- Web: eslint clean, Prettier "All matched files use Prettier code style!", `tsc --noEmit` clean, vitest "96 files, 607 tests passed".
- The "Not implemented: navigation" line in the vitest output comes from the existing `DashboardShell` test.

**/run** on the worktree stack, production web container, real data:
- **Signed out:**
  - `/` shows Landing and `/how-it-works` shows How It Works.
  - All 13 signed-in routes redirect to `/sign-in?redirect_url=…`: `/memories`, `/check-ins`, `/account`, `/connect-telegram`, `/onboarding`, `/plan`, `/admin`, `/admin/users`, `/admin/check-in-log`, `/admin/persona`, `/admin/check-in-kinds`, `/admin/evals`, `/admin/knowledge`.
  - curl can't check this: Clerk's dev instance does its handshake redirect for every document request. So it was checked in Playwright.
- **Signed in as a real User:**
  - `/` shows Home ("Good morning, Run check.") in the sidebar frame, with no Landing.
  - `/memories` and `/check-ins` work.
  - `/admin/users` sends a plain User back to `/`, as before.
  - `/how-it-works` still opens.
- **Signed in as Admin:** the same, and `/admin/users` opens.
- No page errors.
- No sideways scroll on `/` or `/how-it-works` at 390, 600, 899, 900 or 1280. The menu button shows below 900px only.
- **Long text.** These pages show only fixed copy, so no names or rows from real data appear in them.

**Chosen myself / unsure (for Zaf to confirm).**
- Links follow the reference with real routes:
  - `Landing.html` → `/`, `HowItWorks.html` → `/how-it-works`, `Login`/`Signup` → `/sign-in` and `/sign-up`.
  - `Landing.html#pricing` → `/#pricing`. Signed in, those `/#…` links land on Home, which has no such sections.
- The footer's Follow and Legal links stay `#`, as drawn. `/terms` and `/privacy` don't exist, though `AuthLayout` already links to them.
- The phone layout switches below 900px, like the shell and the auth pages.
- The hero heading's line break is hidden on a phone, because `M-Landing` draws the heading without it. `M-HowItWorks` keeps its break.
- The phone menu doesn't reset if the window widens past 900px while it is open. The panel is hidden at that width; it shows again if the window narrows.
- No existing tests changed. New tests: `app/page.test.tsx` (`/` shows Landing signed out and Home signed in), `public-routes.test.ts`, `SiteHeader.test.tsx`, `Landing.test.tsx`, `HowItWorks.test.tsx`.
- Shared files touched: `middleware.ts` (this issue owns it) and `app/(dashboard)/layout.tsx` (its frame moved to `DashboardFrame`). The old `app/(dashboard)/(user)/page.tsx` was deleted.

**/code-review.**
- **Standards.** One hard finding, fixed: SVG strokes used hex values that are tokens. They now use `currentColor` with `text-cream`, `text-soft` or `text-text`.
  - Fixed: the repeated two-column section and tag classes now live in `site-styles.ts`, which also holds `siteColumn` (it had been in `site-links.ts`). The `"zeph" | "person"` union is now one `ChatSender` type. Landing tests now cover the pricing links, the FAQ and the footer.
  - Answered:
    - The path data's trailing zeros (`4.800`) are copied from the reference as-is.
    - `siteColumn` isn't shared with `PublicHeader` and `AuthLayout`: those files are issue 06's, and their phone rules differ.
    - `SiteHero`'s `padding` stays a class string, like `PageHero`'s callers.
    - The last-item checks stay inline; they are one line each.
- **Spec.** Nothing missing.
  - Fixed: the Legal links are back to `#` as drawn.
  - Checked, not real: hash links from the phone menu land at the section top (0px).
  - Answered: the menu state when widening, noted above.

## Completion

- Completed: 2026-11-19
- Commit: merge `1a5b36d` into main (branch `redesign-08-public-pages`: `c16061d` Landing, How It Works and `/` routing, `a92413a` code-review fixes, `ddce8dc` evidence and archive)
