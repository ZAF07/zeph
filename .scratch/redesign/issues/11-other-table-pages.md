# 11 — Redesign: other table pages

Status: ready-for-agent

Lane: B. README slice: 12 (the pages the template's foot lists).

## Parent

`.scratch/redesign/PRD.md`

## What to build

Rebuild these pages from the table template in issue 10, using its parts in its order (heading, totals, filters, table, the four states), with each page's real fields and columns: **Safeguard Events, Check-in Schedule, Usage, Model call log, and the Evals lists** (the eval runs list and the eval cases list). Detail pages are issue 15.

There are no references of their own, so there's no pixel test. Each page must use only the template's parts. If a page needs a part the template doesn't have (a chart, a control, an extra panel), stop and ask before building it. Fixture data goes in the admin-tables fixture file.

## Acceptance criteria

- [ ] Each page uses only table-template parts in template order. A screenshot of each at both widths is attached to this issue.
- [ ] On a phone each table becomes label-and-value cards, with no sideways scroll.
- [ ] Each page's filters, links and actions work as before (the existing tests pass, updated only for markup).
- [ ] Any part that didn't fit was asked about, not invented.

## Blocked by

- `.scratch/redesign/issues/10-admin-users-and-check-in-log.md`

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

- 2026-11-19 — From issue 10: the table template parts are in `web/src/components/`: `AdminPageHeader`, `StatTiles`, `SearchField`, `FilterPills`, `SelectFilter`, `DataTable` (table from 900px, `TableCards` below), `StatusPill`, `TableLoading`, `TableNoMatches`, `TableEmpty`, and the shared `LoadFailed` for "couldn't load". Check-in Schedule already takes `?search=` (`initialSearch`) for the Users panel's link. From issue 12: the Safety page's Helplines table still scrolls sideways on a phone; the README wants rows as cards, so it should move onto these parts here or in a follow-up.
