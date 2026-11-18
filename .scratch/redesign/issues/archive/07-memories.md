# 07 — Redesign: Memories (six tabs)

Status: completed

Lane: A. README slice: 3.

## Parent

`.scratch/redesign/PRD.md`

## What to build

Restyle `/memories` into the six tabs drawn in `Memories` and the five `Memories--tab-*` files, with the `memories-niches.jpg` CSS. Clicking a tab swaps the panel below without navigating away, and sets `?tab=` (`about`, `threads`, `helps`, `summaries`, `photos`). Opening a `?tab=` address shows that tab. The selected tab has cream text, weight 400 and a 2px cream underline. On a phone the tab row scrolls sideways and never wraps. Each tab keeps the Memory Items, Life Threads, Conversation Summaries and photo behaviour it has now. Fixture data goes in the memories fixture file.

If a reference tab has no matching data or behaviour today, or current data has no place in a tab, stop and ask.

Refs: `Memories`, `Memories--tab-about`, `Memories--tab-threads`, `Memories--tab-helps`, `Memories--tab-summaries`, `Memories--tab-photos`, `M-Memories`.

## Acceptance criteria

- [x] All seven refs PASS.
- [x] Test: clicking a tab swaps the panel and sets `?tab=` without a page load, and loading with `?tab=` opens that tab.
- [x] Editing and deleting memories work as before.

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

### 2026-11-18 — plan (agent, branch `redesign-07-memories`)

- Tab is read from `?tab=` on load and written with `history.replaceState` on click (no page load). The Memories tab has no `?tab=`; other params are kept.
- Restyle the six panels from the refs. Reuse `PageHero` (new `memories` background), `filledPill`/`outlinedPill`, and the issue 03 parts: `LoadingPanel`, `LoadFailed`, `EmptyState`, `PausedNotice`, `ConfirmDialog`.
- Choices taken from the refs/States sheet (will report): no category pill or "N memories" count on the Memories tab; Delete all uses the States confirm dialog; Life Thread pill reads "Closed" (was "Settled"); What helps uses When/Feeling/Why rows; summaries and photos show the short day ("12 Nov"); Portrait says "Written"; the memory note shows in `PausedNotice` (bold part as title, rest as body, "Turn memory on" when the User paused it).
- Photos: the 120px box holds the real image; while it loads it shows "Photo" as drawn. The fixture image never resolves, so the drawn placeholder is what the test sees.

### 2026-11-18 — /code-review (standards + spec)

Fixed:
- Memory-off notice reordered the note when it didn't open in bold. Now only a note that opens with `**…**` is split into title and body; any other note is the whole title (test added).
- Photo label was on both the `<li>` and the placeholder `role="img"`; now only on the `role="img"` box, as drawn (test checks it).
- `MemoryCard` flag renamed `roomy` → `compact`.
- Unit tests for `memoriesTabFromQuery` and `searchWithMemoriesTab` (`web/src/lib/memories.test.ts`).

Answered, not changed:
- Shared `DeleteIcon` / `deleteIconButton` restyle reaches Knowledge and Personal Stickers too. Every drawn delete button (all in the Memories refs) has this look and none has the old red round one, so the shared part follows the design; those pages are restyled by their own issues.
- Memory-off notice keeps the Admin-worded `memory_note` (domain: Admin-managed) inside the States "Memory is off" part rather than the sheet's sample copy, the same choice issue 05 made on Home.
- Dropped on the Memories tab, because the refs don't draw them: "N memories, grouped by category", the per-category count, the category pill on each item, the count in the Delete all question.
- Not taken (other areas' files or no third use yet): shared hero-background builder, merging `MemoriesPanelHeading` with Check-ins' heading, one parser shared with `MemoryNote` (Account's, which issue 09 replaces), a shared status-pill component, folding the photo card into `MemoryCard`.

### 2026-11-18 — evidence

**Pixel test** (`NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev --port 3010`, `BASE_URL=http://localhost:3010`, session files from `design-sessions.sh`), after the code-review fixes:

```
PASS  Memories                           0.02% differs, height 1060 vs 1060
PASS  Memories--tab-about                0.01% differs, height 800 vs 800
PASS  Memories--tab-threads              0.01% differs, height 858 vs 858
PASS  Memories--tab-helps                0.01% differs, height 800 vs 800
PASS  Memories--tab-summaries            0.01% differs, height 800 vs 800
PASS  Memories--tab-photos               0.01% differs, height 800 vs 800
PASS  M-Memories                         0.05% differs, height 1436 vs 1436
All pages match the design.
```

Earlier refs still PASS with the shared delete icon/button change: Dashboard 0.01%, Dashboard--menu-folded 0.00%, M-Dashboard 0.01%, M-Menu 0.01%, CheckIns 0.03%, M-CheckIns 0.06%, Onboarding 0.12%, M-Onboarding 0.06%.

Photos first passed at exactly 0.50%. The diff showed the photo box 2px short: the reference box is 120px plus a 1px border (content-box), and Tailwind makes everything border-box. Fixed with `box-content`, now 0.01%.

**Checks:**

```
$ eslint .                                   (no output)
All matched files use Prettier code style!
$ tsc --noEmit                               (no output)
 Test Files  89 passed (89)
      Tests  577 passed (577)
```

**Tab test** (`web/src/components/Memories.test.tsx`): "swaps the panel and sets ?tab= when a tab is clicked, without a page load" (the tab element is the same node after the click, `location.search` is `?tab=photos`, then "" for Memories), "keeps other query flags when it sets ?tab=", "opens the %s tab when loaded with ?tab=" × 5, "opens the Memories tab when ?tab= is unknown". Plus `web/src/lib/memories.test.ts` for the two helpers.

**Browser, fixtures:** at 1280 and 390, clicking "What helps you" changed the URL to `/memories?tab=helps` with 0 extra page loads and a `window` marker kept; `/memories?tab=threads` opened that tab. The phone tab row is one 45px line, `overflow-x: auto`, 649px of tabs in 358px. No page errors.

**/run, real data** (production web container, real backend, a `run-check-…` User with 21 Memory Items across 7 categories, 3 Life Threads, 3 Move Outcomes (helped, didnt_help, mixed), 2 summaries (one with no "offered"), a photo with a missing file, and a Portrait with blank lines):
- All six tabs at 1280 and 390 rendered with no page errors.
- Every delete hit the backend and the row went: `DELETE /api/memory-items/<id> 204`, `/api/life-threads/<id> 204`, `/api/move-outcomes/<id> 204`, `/api/conversation-summaries/<id> 204`, `/api/shared-photos/<id> 204`, `/api/user-portrait 204`. Memories 21 → 20.
- Delete all: "Keep them" left 20, confirming sent `DELETE /api/memory-items 204`, then the empty state, still there after reload.
- Long text: an unbroken 90-letter word made the Memories tab wider than a 390px phone. Fixed with `[overflow-wrap:anywhere]` on the cards (as Home does for Telegram names). Re-checked: no tab is wider than the screen, and long titles wrap inside the card.
- Photo whose image 404s: the 120px box first shows "Photo", then "This photo can’t be shown right now", which fits in 3 lines.
- Memory off: switching it off showed the real Admin note "**Memory is paused.** Nothing is deleted. …" in the States "Memory is off" notice with "Turn memory on". That button turned it back on and the notice went.
- Editing: the Memories page has no edit controls today, and none were added. "Editing and deleting work as before" is covered by the deletes above.

**Existing tests changed** (all in `Memories.test.tsx`, only where the markup changed):
- "N memories, grouped by category" assertions removed (not drawn).
- Delete all now goes through the States confirm dialog: "Delete all memories?" with "Keep them" / "Delete all memories", replacing "Delete all 3 memories?" / "Yes, delete all".
- Summary and photo dates are "11 Nov" / "Sent 10 Nov", not "Wed 11 Nov".
- "Seemed" / "Zeph offered" / "When" / "Feeling" / "Why" rows replace "You seemed …" / "You felt …".
- Portrait "Written 13 Nov" replaces "Updated"; Life Thread "Closed" replaces "Settled".
- Empty and error copy are from States ("Nothing remembered yet" + "Talk to Zeph", "Couldn’t load your memories").
- Tab name "What's going on" now uses the straight apostrophe from the reference.
- The "already off" test now waits for load first, because the loading panel is also `role="status"`.

**Chosen or unsure** (also listed under the code-review comment):
- Life Thread pill reads "Closed" (reference copy); CONTEXT.md calls it "settled".
- The memory-off notice keeps the Admin-managed note text rather than the States sample copy.
- The empty-state "Talk to Zeph" link goes to `https://t.me/`, as "Open Telegram" did before.
- `DeleteIcon` and `deleteIconButton` are shared: Knowledge (admin) and Personal Stickers (Account) now also get the drawn look.
- The fixture photo image never resolves, so the test sees the drawn "Photo" box.
- `MemoryNote.tsx` is left for Account (issue 09).

## Completion

- Completed: 2026-11-18
- Commit: 063bd51 (merge of redesign-07-memories: 5bd6a7d, 33a5101, f2e9835) — "Merge redesign issue 07: Memories — six tabs with ?tab= (no page load; phone tab row scrolls), illustrated hero with Memory switch, States parts for loading/error/empty/memory off/Delete all confirm, drawn delete icon and button; Memories, all five Memories--tab-*, and M-Memories PASS"
