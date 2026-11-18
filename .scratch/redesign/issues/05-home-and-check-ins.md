# 05 — Redesign: Home and Check-ins

Status: ready-for-agent

Lane: A. README slices: 2 and 4.

## Parent

`.scratch/redesign/PRD.md`

## What to build

- **Home** (`/` signed in) to `Dashboard` and `M-Dashboard`, with the `home-bench.jpg` background CSS from the README copied exactly. "To build" parts are drawn on fixture data, with their tags.
- **Check-ins** (`/check-ins`) to `CheckIns` and `M-CheckIns`, with the `checkins-beacon.jpg` CSS. Check-in Frequency is one row of four equal segments on desktop and two rows of two on a phone, and the selected one is the cream pill. Same Check-in settings behaviour as now.
- Fixture data goes in the home and check-ins fixture files. Now that the content matches, re-run `Dashboard--menu-folded` and `M-Menu` too.

Refs: `Dashboard`, `M-Dashboard`, `Dashboard--menu-folded`, `M-Menu`, `CheckIns`, `M-CheckIns`.

## Acceptance criteria

- [ ] All six refs PASS.
- [ ] Choosing a Check-in Frequency, pausing and Quiet Hours save as before (the existing tests still pass, updated only for markup).

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
