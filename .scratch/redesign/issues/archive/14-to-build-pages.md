# 14 — Redesign: To build pages (Plan, Admin Overview, admin Plans)

Status: completed

Lane: B. README slice: 15.

## Parent

`.scratch/redesign/PRD.md`

## What to build

UI only, on fixture data only, with every "To build" tag showing. No billing code and no new backend calls. Making these real is `.scratch/to-build-features/PRD.md`.

- **Plan** (`/plan`) to `Plan` and `M-Plan`.
- **Admin Overview** (`/admin`) to `Admin`, replacing today's redirect to Users. The counts, "Needs attention" list and Features summary come from the overview fixture file, and show the "Sample data" label as drawn. The "Open …" links go to the real admin pages.
- **Admin Plans**: the admin menu item opens the "To build" empty state from issue 03's parts.

Placeholders in `[SQUARE BRACKETS]` render literally.

Refs: `Plan`, `M-Plan`, `Admin`.

## Acceptance criteria

- [x] All three refs PASS. — Plan 0.00%, M-Plan 0.01%, Admin 0.03% (below).
- [x] `/admin` shows the Overview, not a redirect. — `admin/page.tsx` renders `AdminOverview`; `admin/page.test.tsx`; /run: the menu's Overview stays on `/admin` and is marked current.
- [x] Outside fixture mode, these pages show the same drawn sample values and the "To build" tags, and make no backend calls for them. — the pages read `planSample` / `overviewSample` directly; /run on the production container: the only backend calls are the sidebar's `/api/me` and `/api/platform-content`.
- [x] Admin Plans shows the "To build" empty state. — `admin/plans/page.tsx` (`EmptyState` + `ToBuildTag`), its test, and /run via the menu's Plans.

## Blocked by

- `.scratch/redesign/issues/02-shell.md`
- `.scratch/redesign/issues/03-shared-states.md`

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

- 2026-11-18 — From issue 02: the menu already links Overview → `/admin`, Plans → `/admin/plans` and Plan → `/plan`, with their "To build" tags. Overview is marked only on `/admin` itself, so once `/admin` stops redirecting, the `Admin` ref's sidebar will match. No sidebar edits are needed.

- 2026-11-18 — From issue 05: until `/plan` exists, the sidebar's Plan link makes Next prefetch `/plan?_rsc=…` at 1280, and that request never finishes. So the run-dashboard `drive.sh` (`networkidle`) times out on every signed-in page at 1280. Building `/plan` should end it; re-check with `drive.sh / shot.png 1280`.

- 2026-11-19 — Zaf chose the Admin Plans copy (it has no reference): header "Plans" with the To build tag, lead "The plans Users can choose and what each includes.", empty state "No plans yet" / "Plans and billing aren’t built yet. This page will list them once they are."

- 2026-11-19 — Evidence (branch `redesign-14-to-build-pages`, rebased on `origin/main` at `a25b4cb`).

**Pixel test** (`NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev --port 3019`, `BASE_URL=http://localhost:3019`, sessions from `design-sessions.sh`):
```
PASS  Plan                               0.00% differs, height 1142 vs 1142
PASS  M-Plan                             0.01% differs, height 2216 vs 2216
PASS  Admin                              0.03% differs, height 1013 vs 1013
```
Pages touched by the shared-part changes still pass: Landing 0.03%, M-Landing 0.04%, Dashboard 0.01%, Dashboard--menu-folded 0.00%, M-Dashboard 0.01%, Account 0.03%, M-Account 0.07%. The rest of the signed-in set is unchanged (ConnectTelegram and the admin template refs fail by exactly the numbers accepted in issues 09–13). Login/M-Login/Signup time out waiting for `networkidle` on Clerk's scripts, against both the fixture dev server and the stack's own web container. This issue doesn't touch sign-in; worth a look separately.

**Checks** (web): `pnpm lint` clean; `pnpm format:check` "All matched files use Prettier code style!"; `pnpm typecheck` clean; `pnpm test` 113 files, 705 tests passed.

**/run with real data** (worktree stack, production web container, real Clerk Admin and plain User sessions; script drives each page at 1280 and 390). Screenshots in `14-screenshots/` beside this file. All steps PASS, no page errors.
- `/admin`, `/admin/plans`, `/plan` at 1280 and 390: each settles (`networkidle`), no sideways scroll, To build tags shown. Backend calls on each: only `GET /api/me` and `GET /api/platform-content` (the sidebar's account and AI notice).
- "Open Check-in Schedule", "Open Safeguard Events" and "Open Features" land on those real admin pages; "Sample data" label shown.
- Menu Plans opens the To build empty state; menu Overview stays on `/admin` (no redirect) and is marked current.
- Plain User: `/plan` works at both widths; `/admin` sends them home, as before.
- Issue 05's note: `drive.sh / shot.png 1280` now finishes (the `/plan` prefetch no longer hangs).
- Long names / many rows: these pages show fixed sample data only, so real data can't overflow them yet. That's for `to-build-features`.

**Chosen myself / unsure (for Zaf).**
- Sample data sits in the area's fixture files (`design-fixtures/plan.ts`, `overview.ts`) as `planSample` / `overviewSample`, with their types, and the pages import them in every mode. When `to-build-features` makes these real, the types should move beside the API client.
- The buttons (Switch to this plan, Update, Cancel plan) do nothing, and Receipt is `href="#"`, as drawn. Only the title's To build tag says so.
- Shared parts changed (no markup change on existing pages, pixel tests above): `PageHeader` and `AdminPageHeader` take a title with a tag; `AdminPageHeader` gets an `aside` (the Sample data label); `HomeCard` gets `main`/`side` widths for the Overview; Landing's plan list moved into `PlanIncludesList`, shared with the Plan page. New: `CardRow` (48px row), `CardFooterLink`, `OverviewCountTile`, `MessagesChart`, `PlanSummaryCard`, `PlanChoiceCard`, `PlanDetails`, `AdminOverview`.
- The "Sample data" pill keeps the drawn 4px 12px padding, not the smaller shared `outlinedPill`.
- No existing test changed.

**Code review.** Fixed: one `CardFooterLink` for the repeated Open links; clearer sample names (`weekday`, `isToBuild`, `sampleIncludes`, `samplePayment`); inclusion test no longer finds cards by class name; a `/plan` page test for the header. Answered, not changed: types in the fixture files (above); `HomeCard` keeps its name (renaming touches many files); the usage count, limit and bar share stay separate sample values (all placeholders until billing exists); index keys are fine for fixed sample rows.

## Completion

- Completed: 2026-11-19
- Commit: <to be filled in after merge>
