# 10 — Redesign: admin Users and Check-in Log (table template)

Status: completed

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

- [x] All three refs PASS. — **FAIL accepted, as Zaf chose:** the "Sample data" pill is never shown, the Users panel stays closed until Manage, and (as in issue 09) the builder notes are left out of the Check-in Log. With only the pill put back for the check: AdminCheckInLog 0.05% and M-AdminCheckInLog 0.06% above the notes, AdminUsers 0.04% with Manage pressed (see Evidence).
- [x] Each of the four table states matches its drawn sample (test per state). — `CheckInLog.test.tsx`: loading, filters match nothing, nothing logged yet, couldn’t load (with Try again).
- [x] Filters and role changes work as before. — Check-in Log search, outcome pills and period, and Make/Remove admin (with the last-Admin message), shown in tests and on the running stack. The Users filter buttons were dropped (Zaf).

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
  - Users: drop the All / Admins / Telegram not connected filters. Search only, as drawn.
  - Users panel Feature switches: the switch shows whether the Feature works for the User. Flipping sets On or Off for them; flipping to the same value as everyone's switch sets Default.
  - "Sample data" pill: never shown (both pages).
  - Users panel: no User open until a row's Manage is pressed (so AdminUsers can't PASS as drawn; checked by parts instead).
- 2026-11-19 — Chosen by me (following issue 09's decision): the orange builder notes and the state samples under them are left out of the Check-in Log page. The four states are tested per state in component tests.

- 2026-11-19 — Evidence (gathered on `origin/main` at `2fd47ce`; re-run after rebasing on `b75cb21`, which brought issue 12: checks 104 files / 645 tests passed, the three refs gave the same numbers, and AdminPersona stayed at issue 12's 1.10%).

**Pixel test** (`NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev --port 3010`, `BASE_URL=http://localhost:3010`, sessions from `design-sessions.sh`), as shipped:
```
FAIL  AdminUsers                         2.84% differs, height 800 vs 888
FAIL  AdminCheckInLog                    0.11% differs, height 837 vs 1470
FAIL  M-AdminCheckInLog                  6.32% differs, height 2238 vs 3216
```
Why, and the parts compared on their own with the same pixelmatch settings:
- AdminUsers: the panel only opens on Manage (Zaf). With Manage pressed on the first row: 0.07% (the missing pill).
- AdminCheckInLog: the notes are left out, so the page is shorter. Above the notes: 0.08%.
- M-AdminCheckInLog: on a phone the missing pill takes its own 40.6px row, so everything below sits higher. Every block is the drawn size (header, totals 189, filters 98, cards 1622).
- With only the pill put back for this check (not committed): AdminCheckInLog 0.05%, M-AdminCheckInLog 0.06% above the notes, AdminUsers 0.04% with Manage pressed. What is left is the totals’ digits: they are worked out from the six drawn rows (3, 2, 50%, 1), not the drawn 212, 41, 64%, 2.
- Pages sharing parts I changed still pass: Dashboard 0.01%, Dashboard--menu-folded 0.00%, M-Dashboard 0.01%, Memories and its five tabs ≤0.02%, CheckIns 0.03%, M-CheckIns 0.06%, Account 0.03%, M-Account 0.07%, Onboarding 0.12%, M-Onboarding 0.06%, M-Menu 0.01%, Landing, HowItWorks and their phone files ≤0.04%.

**Checks** (web): `pnpm lint` clean; `pnpm format:check` "All matched files use Prettier code style!"; `pnpm typecheck` clean; `pnpm test` 101 files, 631 tests passed.

**/run with real data** (worktree stack, 40 seeded Users incl. "Maximiliana Featherstonehaugh-Whittington the Third of Somewhere" with an 84-character email, 60 Check-in log rows incl. 150-character skip reasons; real Admin session):
- Users: "41 users · 1 admin". Manage opened the long-named User in the panel with 9 Feature switches. Flipping Web Search off saved Off ("Off for this user", "Changed … by …"); flipping it back saved Default (no `user_feature_switches` row left). Make admin → "… is now an Admin.", the row's pill became Admin, "41 users · 2 admins"; Remove admin → "… is no longer an Admin.". The Check-in Schedule link opened `/admin/check-in-schedule?search=<email>` with the email in its search box. Search "seed1" → 10 rows; "nobody-xyz" → "Nothing matches these filters.".
- Check-in log: 60 rows, totals Sent 36 / Skipped 20 / Replied to 38% / Paused by ignore rule 4. Skipped → 20 rows; user filter → 1 row; period → "Last 30 days" shown in the box and the 30-day log loaded.
- At 390 both pages are 390 wide (no sideways scroll); rows are cards; long names, emails and skip reasons wrap. No page errors.
- **Doesn’t fit as drawn (reported):** at 1280 a very long name or email widens the Users table’s first column, so the table scrolls sideways inside its card (the drawn table already scrolls a little: 720px in a ~600px card) and the dates and Telegram status wrap onto two lines.

**Chosen myself / unsure (for Zaf to confirm).**
- Paused rows say the drawn "Three in a row went unanswered", but the Ignore Threshold is an Admin setting (3 now). If it changes, this text is wrong.
- The Feature switch is on when the Admins’ switches allow the Feature for the User. That is the same as "works" except when the User turned it off themselves (or Stickers is off): then the switch is on and the line under it says why it is off.
- Feature lines not drawn: "Works: on for this user", "Off for this user", "Off: the user turned it off", "Off: Stickers is off for this user". Stickers off: "Off for everyone · N personal stickers kept". The "Changed … by …" line stays under a Feature set for one User.
- The Users panel has no close (none drawn); Manage on another row swaps it. Its heading takes focus when it opens.
- Role-change notes use the shared SavedNote / SaveFailedNote, 8px under the Role row (gap not drawn). Users empty and error states keep today’s words. Users phone cards end with an "Actions" line holding Manage.
- Portrait shows "Not written" when there is none (only "Written" is drawn).
- Users search stays client-side. The page header and the "N users · N admins" line follow the reference; totals and filters only appear in the order drawn.
- Check-in Log totals show once the log has loaded (they come from the rows), so the loading and error states show the filters then the state.
- Shared changes: the admin layout no longer wraps pages in a 1120px `text-sm` column (the references put admin pages straight in the main column), so pages from later issues change a little; `LockIcon` is the drawn padlock everywhere it appears; `formatDay` and `formatWeekdayDay` write "Sep" not "Sept" everywhere, as the design does; Check-in Schedule takes `?search=` (new `initialSearch` prop) so the panel’s link opens that User.
- The period select is the drawn box with a native select laid over it unseen, so it is as wide as the chosen option.

**Existing tests changed.**
- `AdminUsers.test.tsx`: rewritten for the new markup — no filter buttons, the "No message content · …" caption and Features dialog are gone, role changes happen in the side panel ("Make admin"/"Remove admin"), and Life threads / Move outcomes / Portrait moved to the panel. New tests: phone cards, no-match, loading, panel only on Manage, "Not written".
- `UserFeaturesPanel.test.tsx` → `UserFeatureSwitches.test.tsx`: the Default/On/Off dialog became switches in the panel (Zaf); tests cover the lines, Off for one User, back to Default, failed save, Try again.
- `CheckInLog.test.tsx`: queries scoped to the table (cards repeat the text); paused text, empty and error copy follow the reference; new tests for the time format, phone cards, loading and no-match.
- `features.test.ts`: `reasonText` replaced by `userFeatureLine`, `isOnForUser`, `switchForUser`.
- `choose-api-client.test.ts`: the "no fixture yet" example is now `getModelCallTrace`, since `listAdminUsers` has a fixture.

**Code review** (two sub-agents, standards and spec): no hard standards violations. Fixed: one `displayNameOf` / `roleLabel` helper (`lib/users.ts`), and direct tests for `DataTable` (with `TableCards`), `FilterPills` and `SelectFilter`. Answered, not changed: the Users table stays hand-built beside `DataTable` because its reference draws a different table (titled card, highlighted row, To build header); the period stays a string because selects give strings; `minWidthClass` and `labelShown` match the two drawn variants. Spec points (Ignore Threshold text, switch meaning, no close, undrawn lines, shared changes) are listed above for Zaf.

- 2026-11-19 — After rebasing on issue 12: it made the same `AdminPageHeader` and admin layout changes, so those merged cleanly; the dates test kept both new functions. The period select now uses issue 12's `ChevronDownIcon`. Not changed: the Users panel switches keep the shared `Switch` (the reference draws plain rows, not issue 12's field-row box). Note for Zaf: issue 12's `formatLastSavedAt` still writes "Sept" in September, while `formatDay` now writes "Sep".

## Completion

- Completed: 2026-11-19
- Commit: merge `355658d` into main (branch `redesign-10-admin-tables`: `b1b9bd0` admin Users and Check-in Log in the new look with the table template parts, `af1dc04` code-review fixes, `89af056` evidence, archive and CONTEXT update, `f417a5b` shared ChevronDownIcon, `536733c` evidence re-run after rebasing on issue 12)
