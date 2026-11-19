# 10 — Redesign: admin Users and Check-in Log (table template)

Status: ready-for-agent

Lane: B. README slices: 11, and the template part of 12.

## Parent

`.scratch/redesign/PRD.md`

## What to build

- **Admin Users** (`/admin/users`) to `AdminUsers`, with the role changes and per-User Check-in tools as now.
- **Check-in Log** (`/admin/check-in-log`) to `AdminCheckInLog` and `M-AdminCheckInLog`. This is the **table template**: heading, totals, filters, table, then the four states (loading, filters match nothing, nothing logged yet, couldn't load) exactly as drawn under its annotation. On a phone each row becomes a card of label and value lines, with no sideways scrolling.
- Build the table template as reusable parts, since issue 11 builds six more pages from it.
- Fixture data goes in the admin-users and admin-tables fixture files.

Refs: `AdminUsers`, `AdminCheckInLog`, `M-AdminCheckInLog`.

## Acceptance criteria

- [ ] All three refs PASS.
- [ ] Each of the four table states matches its drawn sample (test per state).
- [ ] Filters and role changes work as before.

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

- 2026-11-19 — Decisions (Zaf, asked at start):
  - Users: drop the All / Admins / Telegram not connected filters. Search only, as drawn.
  - Users panel Feature switches: the switch shows whether the Feature works for the User. Flipping sets On or Off for them; flipping to the same value as everyone's switch sets Default.
  - "Sample data" pill: never shown (both pages).
  - Users panel: no User open until a row's Manage is pressed (so AdminUsers can't PASS as drawn; checked by parts instead).
- 2026-11-19 — Chosen by me (following issue 09's decision): the orange builder notes and the state samples under them are left out of the Check-in Log page. The four states are tested per state in component tests.
