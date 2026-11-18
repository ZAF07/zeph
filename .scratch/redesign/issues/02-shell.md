# 02 — Redesign: shell (sidebar, fold, rail, phone bar and menu)

Status: ready-for-agent

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

- [ ] The sidebar, rail, phone bar and menu match the references (the diff images show red only in the content area until issue 05).
- [ ] Test: folding is remembered across a reload, and works when storage is blocked.
- [ ] Test: the phone menu opens, shows a cross, and closes when a link is chosen.
- [ ] Admins see the Admin section and Users don't.
- [ ] Every focusable element has the 2px cream outline with 2px offset. Chevron and hover use only the 150ms ease, and `prefers-reduced-motion` is respected.

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

- [ ] `node design/compare.cjs <this issue's refs>` prints PASS for each ref (pasted below), where the issue lists refs.
- [ ] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` all pass (output pasted).
- [ ] A `/run` check on the running stack with **real** data shows the pages work, and long names or many rows fit, or any that don't are reported.
- [ ] Reported: anything the agent was unsure about or chose itself, and any existing test changed and why.
- [ ] `/code-review` run, and findings fixed or answered.

## Comments
