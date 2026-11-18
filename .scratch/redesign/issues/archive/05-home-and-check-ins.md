# 05 — Redesign: Home and Check-ins

Status: completed

Lane: A. README slices: 2 and 4.

## Parent

`.scratch/redesign/PRD.md`

## What to build

- **Home** (`/` signed in) to `Dashboard` and `M-Dashboard`, with the `home-bench.jpg` background CSS from the README copied exactly. "To build" parts are drawn on fixture data, with their tags.
- **Check-ins** (`/check-ins`) to `CheckIns` and `M-CheckIns`, with the `checkins-beacon.jpg` CSS. Check-in Frequency is one row of four equal segments on desktop and two rows of two on a phone, and the selected one is the cream pill. Same Check-in settings behaviour as now.
- Fixture data goes in the home and check-ins fixture files. Now that the content matches, re-run `Dashboard--menu-folded` and `M-Menu` too.

Refs: `Dashboard`, `M-Dashboard`, `Dashboard--menu-folded`, `M-Menu`, `CheckIns`, `M-CheckIns`.

## Acceptance criteria

- [x] All six refs PASS.
- [x] Choosing a Check-in Frequency, pausing and Quiet Hours save as before (the existing tests still pass, updated only for markup).

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

- From issue 01 (2026-11-18): in fixture mode the clock stands at Tue 17 Nov 2026, 8:00 PM Singapore (`currentTime()` in `web/src/lib/clock.ts`). `DashboardHome` greets in `home.time_zone`, so the home fixture must return `time_zone: alex.time_zone` (Asia/Singapore, from `design-fixtures/shell.ts`). Otherwise the greeting uses the browser's time zone, and a test machine on UTC reads "Good afternoon".

- 2026-11-18 — Started on branch `redesign-05-home-and-check-ins` (own worktree, ports 3010/8010/5442). Zaf's answers to the gaps between the references and today's pages:
  - **Time zone on Check-ins:** dropped. It is set on Account & privacy only, as drawn.
  - **Hero "last talked" line:** "You last talked with Zeph today." / "…yesterday." / "…on 10 Nov." With none: "You haven't talked with Zeph yet."
  - **Home "Last check-in" day:** "Today", "Yesterday", a weekday for up to 7 days ago, then "10 Nov". No Kind. Reply status as now.
  - **Home Check-ins card when not On:** outline pill "Paused" or "Off" (the "No reply" style). Paused: first row "Paused · until Wednesday, 18 November", then quiet hours and last check-in. Off / not available: one row "Zeph only replies when you message" / "Not available on your account". The settings link always shows.
  - Defaults stated and not objected to: no date line or Sign out in Home's header (Sign out is in the sidebar); `AttentionCard` when Telegram isn't connected; "Memory is on." line while memory is on, the backend's note in the same box while off; copy as drawn ("Weekly", "11:00 PM to 7:00 AM", "Zeph gave you space", "Tuesday 10 Nov", straight apostrophes); States-sheet parts and copy for paused, empty, save-failed and loading; `Switch` and the change captions restyled to the references (shared parts).

- 2026-11-18 — Implemented on branch `redesign-05-home-and-check-ins`. Evidence below.

**Pixel test** (fixture dev server on WEB_PORT 3010, final code after the code-review fixes):
```
PASS  Dashboard                          0.01% differs, height 1268 vs 1268
PASS  Dashboard--menu-folded             0.00% differs, height 1268 vs 1268
PASS  M-Dashboard                        0.01% differs, height 2091 vs 2091
PASS  M-Menu                             0.01% differs, height 2448 vs 2448
PASS  CheckIns                           0.03% differs, height 1516 vs 1516
PASS  M-CheckIns                         0.06% differs, height 2348 vs 2348
All pages match the design.
```
The first run failed by 1px per row on Home and 51px on CheckIns. The reference rows have no `box-sizing`, so their `min-height` adds to the border and padding (`content-box`). The Check-ins card rows and the Recent check-ins rows now use `box-content`, as issue 03 found for the States sheet.

**Checks** (web): `pnpm lint` clean, `pnpm format:check` "All matched files use Prettier code style!", `pnpm typecheck` clean, `pnpm test` 86 files / 545 tests passed. The production build is the web Docker image (`docker compose up -d --build web`), which built and ran this code.

**/run with real data** (production web container, flag off, real Clerk test User, this worktree's database):
- New User (no Telegram, nothing remembered): Home shows "You haven't talked with Zeph yet.", the orange `AttentionCard` with Connect Telegram, the Check-ins card "Off" with "Status · Zeph only replies when you message", and both empty states. Check-ins shows the "Check-ins are off" notice and "No check-ins yet". No page errors and no sideways scroll at 1280 or 390.
- Seeded real rows: the name "Maximiliana Alexandra Featherstonehaugh-Whittington", Telegram user `@maximiliana_featherstonehaugh_whittington_long`, 6 long Goals, 8 long Memory Items, 13 Check-ins (sent, replied, no reply, skipped). Everything fits at 1280. At 390, the long Telegram username pushed Home 33px sideways. Fixed (`[overflow-wrap:anywhere]` on that line), and re-checked at 0px. The last check-in two days back reads "Monday · you replied".
- Behaviour through the real backend, checked in the `users` row after each step: Most days → `most_days`; Until 07:15 → `quiet_hours_end 07:15:00`; For a week → `check_ins_paused t`, with the notice "Check-ins are paused until 25 Nov"; Resume now → `f`; switch off → `check_ins_enabled f` with the "Check-ins are off" notice; switch on → `t`. Home then showed "Most days" and "10:30 PM to 7:15 AM".
- Other User pages after the `(user)` layout was deleted: Memories, Account and Connect Telegram have no sideways scroll at 1280. At 390, Connect Telegram is 4px wide because its old card prints the long username. That is issue 09's content (note added there).

**Chosen myself / unsure.**
- Copy for states the references don't draw:
  - The Home Check-ins card's row label "Status" for off / not available.
  - "None yet" when no Check-in was sent.
  - Home empty states keep today's copy: "Nothing here yet" for Goals, and "No memories yet" / "They’ll appear after your first Conversation." for Recently remembered.
  - Check-ins "off" and "not available" use `PausedNotice` with today's copy and no button. `PausedNotice.action` is now optional.
- `app/(dashboard)/(user)/layout.tsx` (the 880px column) is deleted. Every User reference puts the page straight in `<main>`. This also widens Memories, Account and Connect Telegram until their issues land.
- `design-fixtures/shell.ts` (shared): Alex's `changed_in_chat` gained `quiet_hours: 12 Nov`, because CheckIns.html shows "Changed in chat · 12 Nov" under quiet hours.
- "Weekly" replaces "Once a week" everywhere it is listed (`checkInFrequencyOptions`), so the admin Check-in Schedule, Platform settings and User Check-in panel now say "Weekly" too. Onboarding.html also says "Weekly".
- Shared parts restyled to the references: `Switch` (byte-for-byte the same as issue 04's in-flight version, so the merge is clean), `ChangedInChatCaption` / `ChangedByAdminCaption` (12px soft, no icon), `QuietHoursFields` (dark field). The admin User Check-in panel uses the last two as well.
- New `CheckInFrequencySegments` for the Check-ins page grid. `CheckInFrequencyPicker` is left alone, because issue 04 is restyling it for Onboarding's different look.
- Native time field: Chromium shows "07:00 AM" with a leading zero and a clock icon, where the reference draws "7:00 AM". It is within the limit (0.03% / 0.06%).
- Hero image CSS is in `components/hero-backgrounds.ts` as Tailwind arbitrary `[background:…]` values (spaces as `_`), copied from the README with only the `url()` changed. `globals.css` is issue 01's file.
- **Known, not from this issue:** at 1280 the sidebar's Plan link (issue 02) makes Next prefetch `/plan`, which doesn't exist until issue 14. That request never finishes, so `drive.sh` (which waits for the network to go quiet) times out on any signed-in page at 1280. It is the same on `/account`. Direct visits work. Note added to issue 14.
- **For issue 04** (in flight in another worktree, so its file isn't edited here): `check-ins.ts` and `check-ins.test.ts` are changed near issue 04's `formatQuietHour`. `home.ts` has its own 12-hour quiet hours formatting, which can switch to `formatQuietHour` once both are on main.

**Existing tests changed, and why.**
- `DashboardHome.test.tsx`: new copy and markup (hero line, card rows, "Remembered 2 Oct", the category alone, the Memory line as a `span` not `strong`, `AttentionCard` instead of the banner region). The Sign out test was removed, because Home no longer has Sign out (the sidebar does, tested in `DashboardShell.test.tsx`). Added: the Plan card test, and the "Memory is on." line.
- `CheckInsSettings.test.tsx`: Settings is now an `aria-label` region, not a heading. Also new copy for off, not available, paused, save failed, no check-ins yet, the kinds heading and the "tell Zeph" line, and full weekday dates without a time. The time zone half of the quiet hours test now checks there is no Time zone field (Zaf: dropped).
- `lib/home.test.ts` and `lib/check-ins.test.ts`: the new wording helpers. `todayHeading`, `lastConversationText` and `formatCheckInSentAt` were removed with their tests, because nothing uses them now.
- `CheckInSchedule.test.tsx`, `UserCheckInSettingsPanel.test.tsx`, `PlatformSettingsForm.test.tsx`: "Once a week" → "Weekly" only.
- New: `lib/dates.test.ts` `calendarDaysAgo`.

**/code-review.**
- Standards:
  - Fixed: the duplicated calendar-day count (now `calendarDaysAgo` in `dates.ts`, used by `formatAddedDay` and Home); the pill and card-row class strings, now one `card-styles.ts`, with `checkInStatusLabels` holding `isFilled` instead of class names; `PausedNotice.action` made optional.
  - Answered: the undrawn-state copy is listed above. `HomeMemoryLine` parses `**` in the component, as `MemoryNote` does.
- Spec: nothing was implemented wrong. Changes reaching beyond these pages (the layout, `shell.ts`, "Weekly" on admin screens, the shared restyles) are reported above.

**Rebase onto issue 04's merge** (`3f41b8b`, which landed while this was being finished):
- One conflict in `lib/check-ins.ts` and its test: kept issue 04's `formatQuietHour` and this issue's `pausedText`.
- `Switch.tsx` and the "Weekly" label were already identical.
- `lib/home.ts` now uses `formatQuietHour` for "11:00 PM to 7:00 AM" instead of its own copy.

After the rebase:
```
PASS  Onboarding                         0.12% differs, height 4302 vs 4302
PASS  M-Onboarding                       0.06% differs, height 4681 vs 4681
PASS  Dashboard                          0.01% differs, height 1268 vs 1268
PASS  Dashboard--menu-folded             0.00% differs, height 1268 vs 1268
PASS  M-Dashboard                        0.01% differs, height 2091 vs 2091
PASS  M-Menu                             0.01% differs, height 2448 vs 2448
PASS  CheckIns                           0.03% differs, height 1516 vs 1516
PASS  M-CheckIns                         0.06% differs, height 2348 vs 2348
All pages match the design.
```
- Checks: `pnpm lint` clean, `pnpm format:check` clean, `pnpm typecheck` clean, `pnpm test` 88 files / 555 tests passed.
- `/run` again on the rebuilt container with the same real data: pause, resume, quiet hours and the switch save, with no page errors and no sideways scroll on Home at 1280 or 390.
