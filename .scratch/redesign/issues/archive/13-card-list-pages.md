# 13 — Redesign: card-list pages (Check-in Kinds template and the rest)

Status: completed

Lane: A. README slice: 14.

## Parent

`.scratch/redesign/PRD.md`

## What to build

- **Check-in Kinds** (`/admin/check-in-kinds`) to `AdminCheckInKinds`, `AdminCheckInKinds--all-folded` and `M-AdminCheckInKinds`. This is the **card-list template**:
  - The whole top row of a card toggles it, and the chevron points right when folded and down when open.
  - Several cards can be open at once. Expand all and Collapse all do what they say.
  - A card with unsaved edits shows the orange "Unsaved changes" tag on its folded row and keeps its text when folded.
  - It has the remove confirm, the empty, loading and couldn't-load states, and "could not save" in the save bar.
  - `?design=all-folded` renders every card folded in fixture mode.

  Build it as reusable parts.
- Then **Memory Categories, Needs, Moves, Sticker Library and Knowledge**, from the template. Each card keeps the order folded row, fields, save bar. Pages with more fields add field rows inside the open card and change nothing else. No pixel test for these. The Knowledge Document detail page is issue 15.
- If a page needs a part the template doesn't have, stop and ask. Fixture data goes in the admin-cards fixture file.

Refs: `AdminCheckInKinds`, `AdminCheckInKinds--all-folded`, `M-AdminCheckInKinds`.

## Acceptance criteria

- [x] All three refs PASS. (By parts, as Zaf decided: see Evidence.)
- [x] Tests: whole-row toggle, several open at once, Expand all / Collapse all, and the unsaved tag keeping text while folded.
- [x] Each of the other five pages uses only card-list parts, with screenshots at both widths attached.
- [x] Add, edit and remove work as before on every page (`/run`).

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

- 2026-11-19 — Decisions (Zaf, asked at start):
  - Pixel test: as issues 09/10/12, no "Sample data" pill and no orange builder notes or samples. Checked by parts. The "Unsaved changes" tag on "A follow-up" comes from a real edit in the check script, not from fixture data.
  - Needs and Moves: the extra fields (ruled-out Moves checkboxes; "Needs a Feature" select and "asks a question" checkbox) are form-template field rows inside the open card. Move up/down are 44px round arrow buttons at the left of the save bar (as Helplines). The fallback Need has no Remove, and its bar says so.
  - Memory Categories: Name, Description, and "Always include" as a switch field row that still saves the moment it is flipped (as now), apart from the card's Save. Archive replaces Remove (with the confirm). Archived categories are a second "Archived" list of folded cards; their open card has only Restore.
  - Sticker Library: folded row has the picture, emoji, start of the note (or "Needs a note"). Open card: "When to use" field and the save bar (Save replaces save-on-leave), Remove with the confirm. "Add stickers" stays above the list as the adding box, with its tabs.
  - Knowledge: folded row has title, "source · tradition", status pill, added day. Open card: read-only lines (type, file name, failure reason); the bar has "Open document", Retry (if failed) and Delete with the confirm (replacing the browser confirm). The upload form stays above as the adding box.

- 2026-11-19 — Evidence (branch `redesign-13-card-list-pages`, rebased on `origin/main` at `fbb8895`, after issues 10 and 17 landed).

**Pixel test** (`NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev --port 3020`, `BASE_URL=http://localhost:3020`, sessions from `design-sessions.sh`):
```
FAIL  AdminCheckInKinds                  0.08% differs, height 1147 vs 2270
FAIL  AdminCheckInKinds--all-folded      0.14% differs, height 800 vs 1915
FAIL  M-AdminCheckInKinds                8.12% differs, height 1484 vs 3381
PASS  Dashboard                          0.01% differs, height 1268 vs 1268
PASS  Dashboard--menu-folded             0.00% differs, height 1268 vs 1268
PASS  Account                            0.03% differs, height 1503 vs 1503
FAIL  AdminPersona                       1.10% differs, height 800 vs 1672   (accepted in issue 12)
```
The three refs fail only on what Zaf chose to leave out: the "Sample data" pill and the builder notes with their samples. On a phone the pill sits on its own line, so everything below it moves down by 40.6px; that is the 8.12%. Checked by parts: the reference file is opened in the browser with only the pill and the notes deleted, then compared with the app the same way as `compare.cjs` (full page, threshold 0.1). "A follow-up" gets one edit and is folded, so it shows the drawn "Unsaved changes" tag:
```
PASS  AdminCheckInKinds                0.00% differs, height 1147 vs 1147 (reference without pill and builder notes)
PASS  AdminCheckInKinds--all-folded    0.00% differs, height 800 vs 800 (reference without pill and builder notes)
PASS  M-AdminCheckInKinds              0.00% differs, height 1488 vs 1488 (reference without pill and builder notes)
```

**Checks** (web): `pnpm lint` clean; `pnpm format:check` "All matched files use Prettier code style!"; `pnpm typecheck` clean; `pnpm test` 107 files, 676 tests passed.

**Template tests** (`CheckInKindsManager.test.tsx`):
- whole-row toggle (clicking the summary and the count);
- first card open, the rest folded;
- several open at once;
- Expand all / Collapse all;
- folded card shows "Unsaved changes" and keeps its text;
- Discard;
- remove confirm inside the card, Keep it, and a failed remove shown in the save bar;
- could-not-save in the save bar, with the text kept;
- empty state with Add, loading list, couldn't-load.

New unit tests: `need-draft`, `move-draft`, `useCardAction`.

**Card-list parts** (all new, used by every page):
- `CardList` (toolbar + cards) and `CardListToolbar` (count, Expand all, Collapse all, Add);
- `FoldingCard` (whole-row toggle, chevron right/down with a 150ms turn, unsaved tag; the open part stays mounted so text is kept);
- `CardTag`, `CardCount`, `CardTextField`, `CardSaveBar`, `CardRemoveConfirm`, `NewCardBox`, `CardListLoading`, `CardListFlash`;
- for the agreed extras: `CardMoveButtons` and `CardCheckbox`;
- hooks `useOpenCards` (with `?design=all-folded`) and `useCardAction`.

Pages with more fields add form-template `FieldRow`s inside the open card, as decided.

**/run with real data** (worktree stack, production web container, real Admin session; script drives each page at 1280 and 390). Screenshots are in `13-screenshots/` beside this file (archive folder). All steps PASS, with no page errors (the sidebar's `/plan` prefetch 404 is issue 14 and is filtered out). Every page is 390 wide at 390.
- Check-in Kinds:
  - edited "A casual hello": folding showed "Unsaved changes" and kept the text; Save showed "Saved A casual hello."; then put back;
  - Expand all / Collapse all;
  - added "Run check kind", then removed it with the confirm.
- Memory Categories:
  - added a category and edited it;
  - Always include switched on (the "Always included" tag shows) and off, each saved at once;
  - Archive with the confirm moved it to the archived list, Restore brought it back, then archived again.
  - The run-check categories stay archived, because there is no delete. They are in the worktree database only.
- Needs: added one ruling out a Move (the rule-out was saved), edited it, moved it up (the order changed), removed it.
- Moves: added one needing a Feature and asking a question (both saved), edited it, removed it.
- Sticker Library:
  - the "Needs a note" sticker got a note through Save; the tag went away; then it was removed with the confirm;
  - the Add stickers box opens, both tabs work, Cancel closes it.
  - Run-check stickers were inserted by SQL; there were none.
- Knowledge: uploaded a text file and saw "Uploaded … It’s being indexed now."; Open document links to `/admin/knowledge/<id>`; deleted it with the confirm.
- Long names: a 50-character sticker set name with no spaces first pushed the page to 484px at 390. Fixed: card titles may now break anywhere. The long Needs and Moves texts end in "…" on folded rows and wrap in the open fields.

**Chosen myself / unsure (for Zaf to confirm).**
- The first card starts open, as drawn; the archived categories list starts all folded.
- The add boxes (Add stickers, Add a document) open from the toolbar's Add button, like the template's "Adding a new one, shown above the list". Before, they were always shown. They are not reachable while the list is loading or has failed to load.
- Empty and couldn't-load use the shared `EmptyState` and `LoadFailed` from issue 03. The card-list's drawn empty sample is 4px smaller in padding and 1px smaller in title (22/24px, 16px) than the shared one (26/28px, 17px). I kept the shared part, as the issue's rules say.
- Copy that isn't drawn:
  - the confirm bodies on Needs ("Zeph stops picking this Need."), Moves ("Zeph stops making this Move.") and Stickers ("Zeph stops sending it.");
  - the save bar notes on Needs, Moves and Memory Categories ("Changes apply to the next message after saving.");
  - the Sticker note ("Zeph reads this note to choose a sticker, and uses them sparingly.") and the Knowledge note ("Only Ready documents are used.");
  - the archived-category note ("Zeph saves no new memories here until it is restored.");
  - the field hints, taken from the old "— …" label captions;
  - the Sticker flashes "Saved the note." and "Removed the sticker.";
  - the Memory Categories lead's last sentence ("Categories can’t be deleted, because Memory Items belong to them: archive one instead."), from the old yellow note. The note's second half became the Archive confirm's body.
- Each existing page keeps its own Add label ("Add Need", "Add Move", "Add category"), its own load-error words and its own saved/removed flashes.
- Check-in Kinds now uses the drawn copy: lead, "Add a Check-in Kind", hints, empty and couldn't-load text, confirm. The open card no longer has the Shared Photo / Curiosity explanation lines; the folded row's locked tags ("Sends a Shared Photo", "Asks a Curiosity") say it.
- Sticker title is "emoji + set name" ("🌱 CalmCreatures"; "Single sticker" with no set), since stickers have no name. The note saves with Save (as decided), not on leaving the field; spaces alone don't count as a change.
- Knowledge status tag: Ready plain, Pending orange, Failed coral. Retry shows only when a document failed.
- Ruled-out Moves and "Asks a question" are native tick boxes in the cream accent colour (none is drawn).
- `useCardAction` shows the backend's reason for 422 and 409 on every card. Before, Check-in Kinds and Needs showed it for 422 only.
- `KnowledgeFileDrop` (also used on the document page, issue 15) is reskinned with tokens only. It still used old colour classes that no longer exist.
- Cards keep the 48px left inset of the open part from 900px up and 20px below, the same switch as the shell.

**Existing tests changed** (markup only):
- `CheckInKindsManager.test.tsx`: rewritten for cards (counts on the row, tags instead of caption lines, confirm in an alertdialog, "Add a Check-in Kind").
- `NeedsManager` / `MovesManager`: the card helper presses Expand all first (cards start folded); Remove confirms inside the alertdialog.
- `MemoryCategoriesManager`: cards instead of rows. The add/edit form is now the add box and the open card. Archive goes through the confirm. Errors are in the shared failed note (`alert`). "Nothing archived." is gone: no archived list is shown.
- `StickerLibrary`: card regions; the add box opens from Add stickers; Save replaces save-on-leave (now tested); Remove confirms.
- `KnowledgeLibrary`: card regions; the upload box opens from Add a document and closes after an upload; delete uses the in-card confirm instead of `window.confirm`.

**Code review** (two sub-agents, standards and spec).
- Fixed:
  - archived categories start folded;
  - Sticker row: dropped the made-up "No note yet" and ignores spaces-only edits (as before);
  - Knowledge: Pending has its own tag colour, and Open document comes before Retry;
  - unit tests for `need-draft`, `move-draft` and `useCardAction`;
  - `needInputOf` to match `moveInputOf`;
  - a hook-order slip in `useOpenCards` found while fixing.
- Answered, not changed:
  - Needs/Moves managers and cards still look alike: they were alike before, and merging them would hide which fields each has;
  - the client-side "complete" checks only switch Save on, as before;
  - the Memory Categories 409 reason in its own mutation is the old code, kept as it was;
  - the left-out "Archived" word: the list's count reads "N archived";
  - the 409 widening and the add boxes opening from the toolbar are listed above for Zaf.

## Completion

- Completed: 2026-11-19
- Commit: <filled in after the merge>
