# 14 — Redesign: To build pages (Plan, Admin Overview, admin Plans)

Status: ready-for-agent

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

- [ ] All three refs PASS.
- [ ] `/admin` shows the Overview, not a redirect.
- [ ] Outside fixture mode, these pages show the same drawn sample values and the "To build" tags, and make no backend calls for them.
- [ ] Admin Plans shows the "To build" empty state.

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

- [ ] `node design/compare.cjs <this issue's refs>` prints PASS for each ref (pasted below), where the issue lists refs.
- [ ] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` all pass (output pasted).
- [ ] A `/run` check on the running stack with **real** data shows the pages work, and long names or many rows fit, or any that don't are reported.
- [ ] Reported: anything the agent was unsure about or chose itself, and any existing test changed and why.
- [ ] `/code-review` run, and findings fixed or answered.

## Comments

- 2026-11-18 — From issue 02: the menu already links Overview → `/admin`, Plans → `/admin/plans` and Plan → `/plan`, with their "To build" tags. Overview is marked only on `/admin` itself, so once `/admin` stops redirecting, the `Admin` ref's sidebar will match. No sidebar edits are needed.
