# 11 — Redesign: other table pages

Status: completed

Lane: B. README slice: 12 (the pages the template's foot lists).

## Parent

`.scratch/redesign/PRD.md`

## What to build

Rebuild these pages from the table template in issue 10, using its parts in its order (heading, totals, filters, table, the four states), with each page's real fields and columns: **Safeguard Events, Check-in Schedule, Usage, Model call log, and the Evals lists** (the eval runs list and the eval cases list). Detail pages are issue 15.

There are no references of their own, so there's no pixel test. Each page must use only the template's parts. If a page needs a part the template doesn't have (a chart, a control, an extra panel), stop and ask before building it. Fixture data goes in the admin-tables fixture file.

## Acceptance criteria

- [x] Each page uses only table-template parts in template order. A screenshot of each at both widths is attached to this issue. — `11-screenshots/<page>-1280.png` and `<page>-390.png` for all six pages (real data), plus the Schedule panel, Check in Now result, long-name row and the Eval case Duplicate and Archive dialogs.
- [x] On a phone each table becomes label-and-value cards, with no sideways scroll. — at 390 every page's `scrollWidth` is 390 and rows render as cards (30, 25, 41, 60, 4 and 32 cards); a phone-card test per page.
- [x] Each page's filters, links and actions work as before (the existing tests pass, updated only for markup). — checked on the running stack (see Evidence); tests changed only where markup or the text Zaf chose to drop changed (listed below).
- [x] Any part that didn't fit was asked about, not invented. — four questions asked at the start; answers in the Comments. The few choices left to me are listed below.

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

- [x] `node design/compare.cjs <this issue's refs>` prints PASS for each ref (pasted below), where the issue lists refs. — this issue lists no refs; pages sharing parts I changed are unchanged (pasted below).
- [x] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` all pass (output pasted).
- [x] A `/run` check on the running stack with **real** data shows the pages work, and long names or many rows fit, or any that don't are reported.
- [x] Reported: anything the agent was unsure about or chose itself, and any existing test changed and why.
- [x] `/code-review` run, and findings fixed or answered.

## Comments

- 2026-11-19 — From issue 10: the table template parts are in `web/src/components/`: `AdminPageHeader`, `StatTiles`, `SearchField`, `FilterPills`, `SelectFilter`, `DataTable` (table from 900px, `TableCards` below), `StatusPill`, `TableLoading`, `TableNoMatches`, `TableEmpty`, and the shared `LoadFailed` for "couldn't load". Check-in Schedule already takes `?search=` (`initialSearch`) for the Users panel's link. From issue 12: the Safety page's Helplines table still scrolls sideways on a phone; the README wants rows as cards, so it should move onto these parts here or in a follow-up.
- 2026-11-19 — Decisions (Zaf, asked at start), for parts the template doesn't draw:
  - Extra controls reuse the closest drawn parts: page buttons (New run, Add case, Download CSV, Check in now) are the Check-in Kinds "Add a Check-in Kind" button at the end of the filter row; on/off toggles (Errors only, Show terminal runs) are one filter pill, cream when on; row buttons (Edit, Duplicate, Archive, Schedule's Edit) take the Users "Manage" look in a last "Actions" column (a line on phone cards); paging is outline buttons under the table; panels and the Duplicate/Archive steps use the shared form and confirm parts.
  - Pills: the template's cream / outline StatusPill; only errors and failures (error counts, failed runs, risk type) use the danger colour.
  - Evals tab row (Runs, Cases, Judge, Model Prices) takes the Memories tabs look; the Eval cases row naming each Eval is filter pills as links.
  - Extra text is dropped: captions are just "No message content", and the notes under tables (Safeguard "International fallback…", Usage "Tokens include…", Schedule "Changes here…", Eval cases intro) go.

- 2026-11-19 — Evidence (branch `redesign-11-other-table-pages`, rebased on `origin/main` at `fbb8895`; nothing new on main).

**Checks** (web): `pnpm lint` clean; `pnpm format:check` "All matched files use Prettier code style!"; `pnpm typecheck` clean; `pnpm test` 105 files, 665 tests passed.

**Pixel test** (fixture dev server on 3010, sessions from `design-sessions.sh`). This issue has no refs; pages sharing parts I changed (filter pills, status pill, Memories tabs) give the same numbers as before:
```
PASS  Memories                           0.02% differs, height 1060 vs 1060
PASS  Memories--tab-about                0.01% differs, height 800 vs 800
PASS  Memories--tab-threads              0.01% differs, height 858 vs 858
PASS  Memories--tab-helps                0.01% differs, height 800 vs 800
PASS  Memories--tab-summaries            0.01% differs, height 800 vs 800
PASS  Memories--tab-photos               0.01% differs, height 800 vs 800
PASS  M-Memories                         0.05% differs, height 1436 vs 1436
FAIL  AdminUsers                         2.84% differs, height 800 vs 888
FAIL  AdminCheckInLog                    0.11% differs, height 837 vs 1470
FAIL  M-AdminCheckInLog                  6.32% differs, height 2238 vs 3216
```
The three FAILs are issue 10's accepted numbers, unchanged. In fixture mode all six pages show their fixture rows with no page errors.

**/run with real data** (worktree stack; seeded 40 opted-in Users incl. "Maximiliana Featherstonehaugh-Whittington the Third of Somewhere" with an 84-character email, 30 Safeguard Events, 280 usage rows, 60 traces with 6 errors, 6 Eval Runs (2 from the terminal), the 88 seeded Eval Cases; real Admin session; no eval run started):
- Safeguard Events: 30 rows; Abuse → 8; period All time shown in the box; Medical emergency + 7 days → 4.
- Check-in Schedule: 25 rows, "Page 1 of 2"; Next page → 15 rows, "Page 2 of 2"; search "Maximiliana" → 1 row; clicking the row opened "Check-in settings for Maximiliana …"; "For a day" saved ("Paused until Fri 20 Nov 11:27" in the panel and the row); "zzz-nobody" → "Nothing matches these filters."; selecting one User → "1 selected · goes past pause, Quiet Hours and the Feature switch"; Check in now → "0 of 1 requested · Seed User 5: Refused — no Telegram Connection" (seeded Users have no Telegram link).
- Usage: today 40 rows; Last 7 days → 280 rows and totals "· last 7 days"; Download CSV saved `usage-last-7-days.csv`.
- Model call log: 60 traces; Errors only → 6; plus a User and Reply step → "Nothing matches these filters."; the Time link opened `/admin/model-calls/<trace id>`.
- Evals: 4 runs, Show terminal runs → 6; tabs Runs, Cases, Judge, Model Prices; Cases → Safeguard 32 rows, Persona 9; Archive asked "Archive small-talk?" and Keep it closed it; Archive on another case saved (row shows Archived); Duplicate as "small-talk-run11" opened its editor.
- At 390 and 1280 no page scrolls sideways. No page errors.
- **Doesn't fit as drawn (reported):** at 1280 the Schedule's nine columns are a few pixels wider than the card, so the "Actions" heading is clipped and the table scrolls a little inside its card ("Edit" itself shows). Long names and emails wrap inside their cell.

**Chosen myself / unsure (for Zaf to confirm).**
- Model call log has no caption: "No message content" would be wrong there (Admins' own chats and Evals keep content), and the page lead already says "Content only for Admins’ own chats and Evals".
- Schedule: the "Select everyone on this page" checkbox moved from the table head into the filter row with its label shown (phone cards have no head); the checkboxes use the cream accent; the "Select Users…" / "N selected · …" line stays beside Check in now, because it is the button's own state, not a note. Rows still open the panel on click (desktop table; phone cards use Edit), without a hover colour since none is drawn.
- Download CSV keeps the secondary button (as before; the Check-in Kinds reference draws both looks), the other page buttons are primary.
- Pills: Works, Finished = cream; Feature off, Check in Now waiting, limit reached, Queued, Running, Cancelled, Archived, Edited = outline; risk type, errors, Stopped over limit, Interrupted = danger.
- Filters that narrow (risk type, User, step, Errors only, Schedule search) show the template's "Nothing matches these filters."; otherwise each page keeps its own empty words. This replaces the Schedule's "No one matches that search".
- Eval case Archive uses the shared confirm dialog (title "Archive <key>?", the old sentence as its body, Keep it / Archive). A failed archive closes it and shows "Couldn’t archive the case. Try again." above the table (the confirm part has no error slot). Duplicate is a small dialog on the same surface with the field "Key for the copy".
- The Schedule settings panel and the Check in Now result were moved onto the tokens (deep dialog surface, cream heading, outline buttons; results in a panel box with Dismiss in the row-action look). The rest of the panel's look is unchanged.
- Usage numbers are left-aligned like every template column; dates and times don't wrap.
- Shared changes: `StatusPill` takes `danger`; `DataTable` takes `onRowClick`; new `FilterToggle`, `FilterPillLinks`, `filter-pill-styles.ts`, `tab-styles.ts` (Memories tabs use it, pixel test unchanged), `dialog-styles.ts` (ConfirmDialog uses it), `rowActionButton` (Users' Manage uses it); `EvalCaseRow` is replaced by the table plus `EvalCaseDuplicateDialog`. Pages return fragments like the Check-in log, so the frame spaces them.
- Follow-up, not done here: the Safety page's Helplines table still scrolls sideways on a phone (from issue 12's note).

**Existing tests changed.**
- All six page tests: queries scoped to the table, since the phone cards repeat each row; new tests for phone cards and, where filters narrow, the no-match state.
- `SafeguardEvents.test.tsx`: caption is "No message content" (count dropped, Zaf); the User link goes to `/admin/users`.
- `AdminUsage.test.tsx`: caption is "No message content" (limits dropped) and the "Tokens include…" note is gone (Zaf).
- `CheckInSchedule.test.tsx`: caption count dropped; new test for opening the panel by clicking the row.
- `EvalCasesList.test.tsx`: rows are table rows; Archive confirms in the dialog, Duplicate's field is in its dialog; new tests for a failed archive and for one call however often Archive is pressed.
- New `lib/evals.test.ts` for the eval case addresses.

**Code review** (two sub-agents, standards and spec). No hard standards breaches. Fixed: Archive could be sent twice while saving (test red before, green after); the dialog surface was copied in three files (`dialog-styles.ts`); the case editor address was built in two places (`evalCasesHref`, `evalCaseEditHref` in `lib/evals`); the undrawn row hover was removed. Answered, not changed: the Schedule's select parts, hint line, panel and results restyle were covered by Zaf's "reuse closest drawn parts" answer (the question named them); Download CSV stays secondary; the Model call caption (above); `StatusPill` keeps `filled` so issue 10's callers don't change; periods stay strings because selects give strings (as in issue 10); `name ?? email` fallbacks keep each page's old words.

## Completion

- Completed: 2026-11-19
- Commit: <to be filled in after merge>
