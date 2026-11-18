# 03 — Redesign: shared state parts

Status: ready-for-agent

Lane: B. README slice: 10 (moved early so both lanes can use it).

## Parent

`.scratch/redesign/PRD.md`

## What to build

Turn every part on the `States` sheet into a reusable part: the empty, loading, error (with Try again), saved and confirm parts (confirm dialog included). Also turn the orange "To build" tag and the save bar states shown there into reusable parts. Each later issue uses these instead of making its own.

Replace the old-theme versions of these parts used by current pages where it's a straight swap. Don't re-layout those pages here.

Refs: `States` has no route, so there's no pixel test. Add a fixture-mode-only preview route that renders the sheet, and screenshot it next to `baseline/States.png`. Report the difference and the diff image. Don't add it to `routes.json`.

## Acceptance criteria

- [ ] Every part on the `States` sheet exists as one reusable part, with the copy and styles from the reference.
- [ ] Preview screenshot next to the baseline, with the difference reported.
- [ ] Tests: Try again calls its handler; the confirm dialog's confirm and cancel do what they say and are reachable by keyboard.
- [ ] The preview route is reachable only in fixture mode.

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
