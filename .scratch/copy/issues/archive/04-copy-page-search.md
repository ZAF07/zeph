# 04 — Copy: search across tabs

Status: completed

Lane: A.

## Parent

`.scratch/copy/PRD.md`

## What to build

A search box on the Copy page finds slots by their current text across every tab. Picking a result opens that slot's tab with the slot in view, ready to edit. Unsaved edits in the current tab still prompt before the tab changes.

## Acceptance criteria

- [x] Typing part of a sentence lists the matching slots from any tab, with tab and slot name.
- [x] Picking a result opens its tab and brings the slot into view.
- [x] With unsaved edits, picking a result in another tab asks first.
- [x] The search box is the shared `SearchField`; no matches shows the shared `EmptyState`. No new colours, sizes or gaps (`web/design/README.md`, "Building new UI").
- [x] Tests cover search, jump and the prompt; all web checks pass.
- [x] `/run`: as an Admin, from one tab, search for a sentence that lives in another tab and land on it.

## Blocked by

- `.scratch/copy/issues/01-landing-end-to-end.md`

## Comments

- 2026-11-19 — Done (branch `copy-04-page-search`).
  - `searchCopySlots` (`web/src/lib/copy-search.ts`) finds slots in every tab whose text holds what was typed (letter case and outer spaces ignored), in tab and page order.
  - `CopySearchResults` lists each match as "Tab · Slot name" above the slot's text, in the panel card with card-list rows; no matches shows the shared `EmptyState` ("No slots match").
  - `CopyEditor` has the shared `SearchField` above the tabs. Picking a result in another tab goes through the same tab-switch prompt as the tabs; once on the tab it clears the search, scrolls the slot to the middle of the screen and puts the cursor in it. `CopySlotField` carries an id (`copySlotFieldId`) for this.
- Decisions:
  - **Search reads saved text, not unsaved edits.** The issue says "current text"; the slot list from the backend is what every Admin sees, and unsaved edits are thrown away on a tab switch anyway.
  - **A result in the tab already open jumps without asking** and keeps the edits, since nothing is lost.
  - The Copy page has no reference (PRD: built from existing parts), so the results list and its words ("Search all tabs by text", "No slots match", "No tab has a slot with that text. Try a few words from the sentence.") are new on an admin page, using only existing parts and token values. Admin pages' own words are not Copy.

### Evidence per criterion

1. Lists matches from any tab with tab and slot name: `copy-search.test.ts` (4 tests); `CopyEditor.test.tsx` "lists the slots from any tab whose text holds the words searched for". Live: from Landing, "first conversation" listed "How it works · Sign-up band: line under the heading".
2. Opens the tab and brings the slot into view: `CopyEditor.test.tsx` "opens a result's tab with its slot in view, ready to edit" (tab selected, textarea focused, `scrollIntoView` called on the slot, search cleared) and "jumps to a result in the same tab without asking and keeps the edits". Live: landed on How it works with that slot focused at top 412 / bottom 532 of a 900px window (1280) and 425 / 545 (390).
3. Asks first with unsaved edits: `CopyEditor.test.tsx` "asks before opening a result in another tab with unsaved edits" (Keep editing keeps the tab and the edit; Switch tab lands on the slot). Live: "Switch tabs and lose your changes?" shown; Keep editing kept Landing and the edit.
4. Shared `SearchField` and `EmptyState`, no new colours, sizes or gaps: `CopyEditor.tsx` uses `SearchField`; `CopySearchResults.tsx` uses `EmptyState`, `panelCard`, `cardListRow` and only classes already used elsewhere (`text-[14px] text-text`, `text-[13px] text-soft`, `min-h-11`, `gap-1`). Checked by eye at 1280 and 390 (`04-screenshots/`).
5. Tests and web checks: 5 new `CopyEditor` tests, 4 `copy-search` tests. `pnpm lint` clean, `pnpm format:check` all files use Prettier code style, `pnpm typecheck` clean, `pnpm test` 123 files, 788 passed.
6. /run (worktree stack, real data, Admin): from the Landing tab with an unsaved edit, searched "first conversation" (a How it works sentence), got the prompt, chose Switch tab and landed on the slot, at 1280 and 390, no page errors (`04-screenshots/1-results-*.png`, `2-prompt-*.png`, `3-landed-*.png`, `4-empty-*.png`). Nothing was saved, so no data to undo.

## Completion

- Completed: 2026-11-19
- Commit: <filled in after merge>
