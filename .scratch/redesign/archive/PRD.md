# PRD: Redesign — the Dashboard rebuilt to match the design folder exactly

Status: completed

## Problem Statement

The Dashboard still wears its first light theme, and it was built page by page from loose mockups in `docs/design/`. Pages don't quite agree with each other, and they don't match the new Zeph look Zaf made in Claude Design (dark teal, cream headings, illustrations, Outfit type).

There is also no public face: a signed-out visitor at `/` is sent straight to sign-in, with nothing that says what Zeph is or how it works.

Past UI work drifted from the design in small ways (a gap, a weight, a colour from Tailwind's default palette) that no one noticed one page at a time. Zaf wants this redesign built so closely to the design that there is nothing left to correct.

## Solution

Rebuild every Dashboard page against `web/design/`, the build contract from Claude Design. Its `README.md` is the rulebook, `reference/*.html` holds the exact design for every page and state (desktop 1280px and phone 390px), `tokens.css` holds the theme, and `compare.cjs` is the acceptance test. A page is done only when the pixel test says PASS at both widths (see ADR 0018).

The work is a reskin and re-layout. Existing behaviour, API calls and Clerk logic stay as they are. It adds a few new pages: a public Landing page, a public How It Works page, an Admin Overview, and a Plan page. Parts tagged "To build" in the design (no backend yet) are built exactly as drawn on sample data, with the orange tag left showing. Making them real is PRD `to-build-features`.

The work goes in the README's slices, plus one more (slice 16) for admin pages the design doesn't cover. Each slice is its own issue, branch and PR, and merges to main when done.

## User Stories

**Visitors (signed out)**

1. As a visitor, I want a Landing page at `/` that tells me what Zeph is, so that I can decide whether to sign up.
2. As a visitor, I want a How It Works page, so that I understand what Zeph does before I give it my details.
3. As a visitor on a phone, I want the public nav links behind a menu button, so that the header fits my screen.
4. As a visitor, I want sign-in and sign-up pages in the same look as the rest of Zeph, so that it feels like one product.
5. As a signed-in User visiting `/`, I want to land on Home, not the Landing page, so that I get straight to my own things.

**Users (signed in)**

6. As a User, I want the whole Dashboard in the new Zeph look, so that it feels calm and finished.
7. As a User on a desktop, I want the sidebar to stay in view while I scroll, so that I can always move between pages.
8. As a User on a desktop, I want to fold the sidebar into a narrow icon rail, so that I have more room.
9. As a User, I want the Dashboard to remember whether I folded the sidebar, so that I don't have to fold it every visit.
10. As a User on a phone, I want a sticky top bar whose menu button opens the page list and turns into a cross, so that I can move around on a small screen.
11. As a User on a phone, I want the menu to close when I choose a page, so that I see the page straight away.
12. As a User, I want Home to greet me and show what Zeph has been up to, so that I see at a glance where things stand.
13. As a User, I want Memories split into six tabs I can switch between without the page reloading, so that I can look through what Zeph keeps without getting lost.
14. As a User, I want the selected Memories tab kept in the address, so that a link or a refresh opens the same tab.
15. As a User on a phone, I want the Memories tab row to scroll sideways instead of wrapping, so that it stays one tidy row.
16. As a User, I want the Check-ins page in the new look, with Check-in Frequency as four equal segments (two rows of two on a phone), so that choosing how often Zeph reaches out is clear.
17. As a User, I want Account & privacy in the new look, so that settings and data controls are easy to find.
18. As a User, I want the Connect Telegram page and each of its states in the new look, so that linking Telegram feels like part of the product.
19. As a User on a phone, I want Connect Telegram to show a button instead of a QR code, so that I can connect from the phone I'm holding.
20. As a new User, I want Onboarding in the new look, one step at a time as now, so that getting started feels welcoming.
21. As a User, I want to see a Plan page, so that I know plans are coming (shown as "To build").
22. As a User, I want every empty, loading, error, saved and confirm state to look the same on every page, so that I always know what's happening.
23. As a User who uses the keyboard, I want a clear cream focus outline on everything I can tab to, so that I can see where I am.
24. As a User who prefers reduced motion, I want the Dashboard to respect that, so that nothing moves that I didn't ask for.
25. As a User, I want every button and link at least 44px tall, so that they're easy to tap.

**Admins**

26. As an Admin, I want an Overview page at `/admin` with counts and a "Needs attention" list, so that I see the platform's health at a glance instead of being sent to Users.
27. As an Admin, I want Users, Check-in Log, Persona and Check-in Kinds in the new look, so that the admin area matches the product.
28. As an Admin, I want every table page (Users, Safeguard Events, Check-in Log, Check-in Schedule, Usage, Model call log, the Evals lists) laid out the same way (heading, totals, filters, table, states), so that I learn one layout once.
29. As an Admin on a phone, I want each table row shown as a card of label and value lines, so that I never have to scroll sideways.
30. As an Admin, I want every settings page (Persona, Prompts & models, Safety, Platform Settings, Features) to use the same editor or field rows and the same save bar, so that saving works the same everywhere.
31. As an Admin, I want every card-list page (Check-in Kinds, Memory Categories, Needs, Moves, Sticker Library, Knowledge) to fold and unfold the same way, so that long lists stay manageable.
32. As an Admin, I want to open several cards at once, and to Expand all or Collapse all, so that I can compare or tidy up quickly.
33. As an Admin, I want a folded card with unsaved edits to show an orange "Unsaved changes" tag and keep my text, so that I don't lose work.
34. As an Admin, I want the eval, Knowledge Document and model-call detail pages restyled in the new look, so that nothing in the admin area is left in the old theme.
35. As an Admin, I want a "Plans" item in the admin menu that opens a "To build" empty state, so that the coming page isn't forgotten.

**Zaf (building and reviewing)**

36. As Zaf, I want each page proven to match the design by a pixel test, so that I don't have to spot drift by eye.
37. As Zaf, I want a red-marked diff image when a page fails, so that I can see exactly what's wrong.
38. As Zaf, I want each slice to stop for my review with its PASS lines and a list of anything the agent was unsure about, so that I stay in control.
39. As Zaf, I want the full-resolution illustrations used everywhere, so that the hero images are sharp on big screens.
40. As Zaf, I want the old `docs/design/` mockups gone and CLAUDE.md pointing at `web/design/`, so that agents have one source of truth.

## Implementation Decisions

**The contract**

- `web/design/README.md` is the rulebook and wins over this PRD on any detail of look, copy or behaviour. Where they differ, stop and ask. Agents read it in full before slice 0, and re-read the reference files for their slice before coding.
- Agents must not add or change colours, sizes, weights, spacing, radii, shadows, icons, animations or copy, use Tailwind's default palette, or use bold. They must not loosen `LIMIT`, add a mask, or edit a baseline.
- Stop and ask when a reference conflicts with existing behaviour, a page needs a part no reference shows, real data won't fit the drawn layout, a PASS seems impossible without changing the test, or a value would have to be chosen that isn't in a reference file.

**Slices** (one issue, one branch and one PR each, merged to main when done; numbering as in the README)

0. Foundations: see below.
1. Shell: sidebar, fold, rail, phone bar and menu.
2. Home.
3. Memories: six tabs.
4. Check-ins.
5. Account & privacy.
6. Connect Telegram and its states.
7. Onboarding.
8. Sign in and sign up.
9. Public pages: Landing, How It Works, and the `/` routing.
10. Shared states from `States`, applied across all pages above.
11. Admin shell and Users.
12. Table pages: Check-in Log, then the pages its foot lists.
13. Form pages: Persona, then the pages its foot lists.
14. Card-list pages: Check-in Kinds, then the pages its foot lists.
15. To build: Plan and Admin Overview, UI on sample data only. No billing code. The admin menu's "Plans" item opens the "To build" empty state from `States`.
16. Uncovered admin pages: eval run, eval result, eval case list and case editors (new and edit), new eval, judge, costs, case history, Knowledge Document detail, model-call trace. Restyle them with the tokens and existing parts only (cards, field rows, tables, save bar, states), without changing their layout or behaviour. No pixel test. The agent lists everything it had to choose itself.

**Slice 0, in this order**

1. Full-resolution images: Zaf puts PNGs in `web/design/img-full/`, named to match the existing JPGs. Convert each to a JPG of the same name at quality 90, keeping size and framing, replace the files in `web/design/reference/img/`, then delete `img-full/`. If any file is missing or misnamed, stop and ask.
2. Re-run `shoot.cjs` once to rebuild the baselines from the new images. This is the only baseline change allowed in the whole PRD.
3. Replace the theme with `tokens.css`, load Outfit with `next/font/google` (weights 300 to 600), and copy the images to the app's public `design/` folder.
4. Design-fixture mode (see below).
5. Wire `compare.cjs`: add `playwright`, `pixelmatch` and `pngjs` as dev dependencies, ignore `design/.diff/`, and leave `design/` out of ESLint and Prettier. `design/`'s `.cjs` scripts stay plain JavaScript.
6. A script that makes the two saved sign-in sessions the test needs (`STATE_USER`, `STATE_ADMIN`) by reusing the run-dashboard skill's `start-session.sh`. The admin session also carries the `zeph-design-as=admin` cookie. Files go outside the repo, never into it, and a matching clean-up removes the Clerk test users.
7. Delete `docs/design/` and change CLAUDE.md's "UI design" section to point to `web/design/README.md`.

Existing pages will look broken after slice 0. That's expected.

**Design-fixture mode** (ADR 0018)

- On only when `NEXT_PUBLIC_DESIGN_FIXTURES=1`, read through the typed `env` module. It must never be reachable in a production build.
- It lives in the API client: the client factory returns a fixture client with the same interface instead of the real one. Pages and components don't know about it.
- Every value comes from the reference files. The User is Alex (`alex@example.com`). With the `zeph-design-as=admin` cookie, `/api/me` returns Zaf as an Admin. Memories, Check-ins, users, log rows and counts are the ones drawn. The clock is fixed so the greeting reads "Good evening".
- `?design=` flags work only in fixture mode: `all-steps` (Onboarding, steps stacked), `menu-folded`, `menu-open`, `all-folded`.

**Routing and pages**

- `/` is public. Signed out, it shows Landing. Signed in, it shows Home, as now. `/how-it-works` is public. The middleware's public routes grow to include both.
- `/admin` shows the new Overview instead of redirecting to Users.
- `/plan` is a new User page (UI only).
- Memories tabs set `?tab=` (`about`, `threads`, `helps`, `summaries`, `photos`) and swap the panel without navigating away.
- The sign-in and sign-up card is the Clerk widget, styled through its existing appearance settings to match the reference card, with `data-clerk-card` on its wrapper. Clerk stays inside the auth files.

**Behaviour** (as the README's "Behaviour" section says)

- The sidebar is sticky at 1280px, and the fold choice is kept in `localStorage` (wrapped so a blocked storage doesn't break the page). Below 900px a sticky top bar replaces the sidebar.
- Layouts respond by wrapping, with exact flex-basis and wrap values. The only breakpoint-style switches are the ones the README lists.
- Illustrations are CSS backgrounds with the README's declarations copied exactly, gradient layers included. Only the `url()` path changes. Don't use `next/image` for them.
- Motion: none beyond a 150ms ease on chevron rotation and hover colour. Respect `prefers-reduced-motion`.
- Focus: a 2px cream outline with 2px offset on every focusable element. Keep every `aria-` attribute and label from the reference.

**Running the test**

- In a worktree: `NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev`, then `node design/compare.cjs <Refs>` with `BASE_URL=http://localhost:$WEB_PORT` and the two session files. No backend is needed for the pixel test.

## Testing Decisions

- **Seams.** The pixel test is the main seam for look. Component tests (Vitest + React Testing Library) cover behaviour a screenshot can't show. One small test covers fixture mode.
- **What makes a good test.** Test what a person sees and does (text, roles, labels, clicks, the address), not class names or internal state.
- **Pixel test.** Every reference in `routes.json` must PASS (at most 0.5% of pixels differ, height within 8px). Sign-in and sign-up mask the Clerk card and allow 8%. Paste the PASS/FAIL lines in each slice's issue.
- **Component tests** for:
  - the sidebar fold being remembered and restored;
  - the phone menu opening, showing a cross, and closing on a link;
  - Memories tabs swapping panels and setting `?tab=`;
  - card lists: whole-row toggle, several open at once, Expand all / Collapse all, and the "Unsaved changes" tag keeping text while folded;
  - `/` showing Landing when signed out and Home when signed in.

  Prior art: the existing `*.test.tsx` beside each component (for example the DashboardHome, CheckInKindsManager and AdminUsers tests), rendered through the shared query test helper with the shared test fixtures.
- **Fixture mode test:** it returns the sample data when the flag is on, and the real client when it's off.
- **Existing tests:** update them only where the markup they check has changed, and say which in the issue.
- **Real data:** each slice also gets a `/run` check against the running stack with real data, to catch long names and many rows that fixtures hide. Nothing is ticked without that evidence.
- **Checks:** `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` all green for each slice.

## Out of Scope

- Making any "To build" part real: billing, Plan, admin Plans, Paying subscribers, and the Overview's real counts. That is PRD `to-build-features`.
- New backend endpoints or schema changes.
- Changes to existing behaviour, API calls or Clerk logic.
- New designs for pages the design doesn't cover. Slice 16 only restyles them.
- Anything in the Telegram chat itself.

## Further Notes

- Decided in a grilling session on 2026-11-18. Rules: ADR 0018.
- Before slice 0, Zaf puts the full-resolution PNGs in `web/design/img-full/`.
- `web/design/PROMPTS.md` has the prompts Zaf uses to start each slice. The once-at-start prompt (restate the rule, how a page is finished, the build order and open questions, then wait) applies before slice 0.
- After each slice: report the PASS lines, the four check results and the `/run` evidence, list anything unsure, and stop for Zaf.

## Comments

- 2026-11-19 — PRD close-out check on `main` at `da739cc`. All 18 issues (01–18) are `completed` and archived in `issues/archive/`.
  - **Checks:** `pnpm lint` clean, `pnpm format:check` clean, `pnpm typecheck` clean, `pnpm test` 114 files / 711 tests passed.
  - **Pixel test, all 37 refs in `routes.json`:** signed-out refs on a production build (Clerk's dev-mode route check never lets `/sign-in` reach `networkidle`), signed-in refs on `NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev`. 27 PASS. The 10 FAILs match, to the decimal, the FAILs already accepted in their slices: Signup 12.40% (issue 06), ConnectTelegram 2.60% / M-ConnectTelegram 2.16% (issue 09), AdminUsers 2.84%, AdminCheckInLog 0.11%, M-AdminCheckInLog 6.32% (issue 10), AdminPersona 1.10% (issue 12), AdminCheckInKinds 0.08%, AdminCheckInKinds--all-folded 0.14%, M-AdminCheckInKinds 8.12% (issue 13). No drift since.
  - **Fixture mode stays out of production:** in the production build, signed-in pages called the real API, as `designFixturesOn` in `web/src/env.ts` intends.
  - **Running app, real data (main stack, port 3000):** all 35 Dashboard pages (5 public, 6 User, 24 admin) visited at 1280 and 390 as a signed-in Admin. Every page loaded with status 200, no page errors, no error state and no sideways scroll. One caveat outside this PRD: on Sticker Library, `/api/admin/stickers/<id>/image` returns 404 for the one sticker in the database (backend returns 404 when the sticker has no image a browser can show, or it couldn't be downloaded). The page still renders.
  - **Contract items:** `docs/design/` is gone, CLAUDE.md's "UI design" section points to `web/design/README.md`, `web/design/img-full/` is gone, `/`, `/how-it-works` and `/pricing` are public, and `/admin` shows the Overview.

## Completion

- Completed: 2026-11-19
- Commit: branch `redesign-prd-close-out`, merged into main
