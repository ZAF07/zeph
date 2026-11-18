# 07 — Redesign: Memories (six tabs)

Status: in-progress

Lane: A. README slice: 3.

## Parent

`.scratch/redesign/PRD.md`

## What to build

Restyle `/memories` into the six tabs drawn in `Memories` and the five `Memories--tab-*` files, with the `memories-niches.jpg` CSS. Clicking a tab swaps the panel below without navigating away, and sets `?tab=` (`about`, `threads`, `helps`, `summaries`, `photos`). Opening a `?tab=` address shows that tab. The selected tab has cream text, weight 400 and a 2px cream underline. On a phone the tab row scrolls sideways and never wraps. Each tab keeps the Memory Items, Life Threads, Conversation Summaries and photo behaviour it has now. Fixture data goes in the memories fixture file.

If a reference tab has no matching data or behaviour today, or current data has no place in a tab, stop and ask.

Refs: `Memories`, `Memories--tab-about`, `Memories--tab-threads`, `Memories--tab-helps`, `Memories--tab-summaries`, `Memories--tab-photos`, `M-Memories`.

## Acceptance criteria

- [ ] All seven refs PASS.
- [ ] Test: clicking a tab swaps the panel and sets `?tab=` without a page load, and loading with `?tab=` opens that tab.
- [ ] Editing and deleting memories work as before.

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

### 2026-11-18 — plan (agent, branch `redesign-07-memories`)

- Tab is read from `?tab=` on load and written with `history.replaceState` on click (no page load). The Memories tab has no `?tab=`; other params are kept.
- Restyle the six panels from the refs. Reuse `PageHero` (new `memories` background), `filledPill`/`outlinedPill`, and the issue 03 parts: `LoadingPanel`, `LoadFailed`, `EmptyState`, `PausedNotice`, `ConfirmDialog`.
- Choices taken from the refs/States sheet (will report): no category pill or "N memories" count on the Memories tab; Delete all uses the States confirm dialog; Life Thread pill reads "Closed" (was "Settled"); What helps uses When/Feeling/Why rows; summaries and photos show the short day ("12 Nov"); Portrait says "Written"; the memory note shows in `PausedNotice` (bold part as title, rest as body, "Turn memory on" when the User paused it).
- Photos: the 120px box holds the real image; while it loads it shows "Photo" as drawn. The fixture image never resolves, so the drawn placeholder is what the test sees.
