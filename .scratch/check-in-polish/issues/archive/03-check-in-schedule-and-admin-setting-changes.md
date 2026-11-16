# 03 — Check-in polish: Check-in Schedule page and Admin Setting Changes

Status: completed

Track: B (Admin side). Runs alongside track A (issues 01, 02).

## Parent

`.scratch/check-in-polish/PRD.md`

## What to build

A new admin **Check-in Schedule** page where Admins see every opted-in User's Check-in state and can change their Check-in settings for them.

- **Held-back reason.** When a tick holds a User back, it saves the reason, and the time until when it's known, in the same bulk write as the Due Time. Any decision (sent, skipped, ask about fewer) clears it. No history is kept.
- **Schedule (admin API and page),** searchable by name or email and paged. Each row has:
  - name and email
  - Due Time, shown as "in 3 h · Tue 10:00 their time", or "due now"
  - Check-in Frequency, Quiet Hours and pause (and until when)
  - whether the Check-ins Feature works for them
  - held back now: the reason and until when (e.g. "Quiet Hours, until 07:30")

  No message content anywhere.
- **Admin Setting Change.** Clicking a row opens a side panel where the Admin changes the User's frequency and Quiet Hours, or pauses (a day, a week, until resumed) and resumes them.
  - These are the User's **real** settings, changed through the same Check-in service rules the User's own changes use (e.g. changing Quiet Hours that hold a Check-in back decides it again straight away).
  - Each changed setting is marked "changed by an Admin", stored like the existing chat marks.
  - The User's own change (Dashboard or chat) clears the admin mark. A chat change sets the chat mark instead.
  - Admins **can't** opt a User in or out. Stopping Check-ins for a User is the existing per-User Feature switch.
- **User side:** the User's Check-ins page shows "Changed by an Admin" next to each marked setting.
- **Admin nav** gains the page, next to Check-in Log and Check-in Kinds. Build it from `docs/design/zeph-admin.html` table and side-panel patterns (skip anything tagged "Later"). All calls go through the API client (ADR-0012).

Terms: Admin Setting Change, Held-back Check-in, Due Time (`CONTEXT.md`).

## Acceptance criteria

- [x] The Schedule lists only opted-in Users, with Due Time, settings, Feature status and current held-back reason and until, searchable and paged (`test_the_schedule_lists_only_opted_in_users_with_their_due_time_and_settings`, `test_the_schedule_is_searchable_by_name_or_email_and_paged`, `test_a_user_with_check_ins_off_by_an_admin_shows_the_feature_not_working`; /run screenshot of the page)
- [x] Held-back reasons appear for paused, Quiet Hours, no Telegram Connection, today's message limit used up and no Kind to send, and clear once the Check-in is decided (one test per reason in `tests/test_check_in_schedule.py`; `test_quiet_hours_show_as_held_back_until_they_end_then_clear_once_sent`; /run: a real tick saved "Paused, until Mon 23 Nov 21:15")
- [x] Schedule reads stay bulk: no per-User queries (`test_schedule_reads_stay_the_same_as_users_grow`: SELECTs by table identical for 5 and 20 Users)
- [x] An Admin can change a User's frequency and Quiet Hours, and pause or resume them. The User's real settings change, and the rules match the User's own changes (`test_an_admin_changes_a_users_real_frequency_and_quiet_hours_marked_as_theirs`, `test_changing_quiet_hours_that_hold_a_check_in_back_decides_it_again_now`, `test_an_admin_pauses_and_resumes_a_user`; all go through `CheckInService` with `ChangedBy.ADMIN`)
- [x] The User's Check-ins page shows "Changed by an Admin". The User changing it back clears the mark, on the Dashboard and in chat (`test_the_users_own_dashboard_change_clears_the_admin_mark`, `test_the_users_change_in_chat_swaps_the_admin_mark_for_the_chat_mark`, `test_an_admin_change_drops_the_chat_mark`; `CheckInsSettings.test.tsx`; /run: three marks as the User, two after they changed frequency back)
- [x] There's no way for an Admin to turn a User's Check-ins switch on or off (`test_an_admin_can_never_turn_a_users_check_ins_on_or_off`: `enabled` → 422, not opted in → 409 for change and pause; panel test "offers no way to turn…"; /run: 0 switches in the panel)
- [x] Non-Admins get refused by the new endpoints (`test_non_admins_are_refused_by_the_schedule_endpoints`: all four → 403)
- [x] Component tests cover the Schedule table, the side panel and the "Changed by an Admin" mark (`CheckInSchedule.test.tsx` 6, `UserCheckInSettingsPanel.test.tsx` 7, `CheckInsSettings.test.tsx` +2, `check-in-schedule.test.ts` 7)
- [x] All backend and web checks pass (backend: ruff, ruff format, mypy, pytest 1109 passed; web: lint, format:check, typecheck, 446 tests passed)
- [x] Verified with `/run-dashboard` as a signed-in Admin: see the Schedule, change a User's settings, see the mark as that User (see Comments)

## Blocked by

None - can start immediately.

## Notes for parallel work

Track A (issue 02) adds a "waiting to be woven in" held-back state. Leave room for more reasons. Track A also changes the Check-in decision and tick code and adds migrations. Whichever merges second rebases, and renumbers its migration if they clash.

## Comments

### 2026-11-16 — plan (branch `check-in-polish-03-schedule`)

- **Held back:** `HoldBackReason` moves to `models.py` (still importable from `check_in_decision`). `CheckInSettings` gains `held_back: HeldBack | None` (reason + until). The tick's bulk `save_next_due_times` writes it with the Due Time; "until" is the new Due Time unless the User stays due (then unknown). `check_ins.add` (any decision) clears it. `users.update` never writes it (the tick owns it).
- **Marks:** `ChangedBy` (dashboard / chat / admin) replaces the `in_chat` bool in `record_where_changed`, `CheckInService.change_settings/pause/resume` and `UserService.update_preferences`. New JSONB column `settings_changed_by_admin`, next to the chat marks. Admin change sets the admin mark and drops the chat mark; chat sets chat and drops admin; Dashboard drops both.
- **Core:** new `CheckInScheduleService` (`core/check_in_schedule.py`): list (search, page; opted-in only, soonest Due Time first, Feature status worked out in bulk), change frequency / Quiet Hours, pause, resume — all through `CheckInService` with `ChangedBy.ADMIN`. Refuses a User who hasn't opted in (409). Never touches `enabled`.
- **API:** `GET /api/admin/check-in-schedule?search=&page=`, `PATCH /api/admin/check-in-schedule/{user_id}` (no `enabled` field; extra fields → 422), `PUT|DELETE /api/admin/check-in-schedule/{user_id}/pause`. `/api/check-ins` gains `changed_by_admin`.
- **Migration** `0046`: three new `users` columns. Renumber if track A takes 0046 first.
- **Web:** `CheckInSchedule` (search, table, paging), `UserCheckInSettingsPanel` (dialog like `UserFeaturesPanel`), `ChangedByAdminCaption` on the User's Check-ins page, nav item next to Check-in Kinds / Check-in log. Formatting in `lib/check-in-schedule.ts`.
- Leaves room for issue 04 (Check in Now: row checkboxes) and issue 02 (new held-back reason).

### 2026-11-16 — code review and decisions

- **Fixed from review:** a settings change that moves the Due Time now clears the saved held-back reason (it no longer applies; the User is decided again now or isn't due until later). One that keeps the Due Time (e.g. changing Quiet Hours while there's no Telegram Connection) keeps it. Tests for both. The settings panel now calls `reloadUserPages()` and reloads the Check-ins page (ADR-0012), so an Admin editing their own row sees it straight away. The three date helpers became one.
- **Side panel:** the design file has no separate drawer, so the edit view reuses the existing `UserFeaturesPanel` dialog (a centred panel). Easy to restyle later if wanted.
- **Kept on purpose:** `AdminCheckInChanges` stays its own type, so "no on/off switch" shows in the type. The API takes an optional `page_size` (1–100, default 25). The panel's dialog shell copies `UserFeaturesPanel`; a shared admin panel component would be a separate tidy-up.
- **Not done:** the search runs on every keystroke with no delay. That's fine at today's scale.

### 2026-11-16 — /run-dashboard (worktree stack, ports 3010/8010)

- Signed in a plain User (set to opted in, "most days", Singapore, due in 3 h) and an Admin.
- As Admin, `/admin/check-in-schedule`:
  - the nav link is there, next to Check-in Kinds and Check-in log;
  - the row read "in 3 h · Tue 00:14 their time · Most days · 22:00–07:30 · Not paused · Works · —".
- In the panel I changed:
  - frequency to Once a week;
  - Quiet Hours "From" to 21:00;
  - pause to For a week.

  The row then read "in 7 d · Mon 21:15 their time · Once a week · 21:00–07:30 · Paused until Mon 23 Nov 21:15". The panel has no on/off switch.
- As the User, `/check-ins` showed "Changed by an Admin · 16 Nov" under frequency, Quiet Hours and pause. The User picked Most days, and the frequency mark went (two marks left).
- I moved the Due Time 1 minute into the past, and the real scheduler saved held back `paused` until the pause end. The Schedule showed "Paused, until Mon 23 Nov 21:15".
- At 390 px the page works like the other admin pages, and the table scrolls sideways. No page errors.
- I cleaned up both test Users. The shared Playwright in `$TMPDIR/zeph-run-playwright` was half-installed (probably another agent), so I used a private copy.

## Completion

- Completed: 2026-11-16
- Commits: `1af1db0` (backend: held-back reason, Schedule API, Admin Setting Changes, migration 0046), `313f759` (Dashboard: Schedule page, settings panel, Changed by an Admin marks), `cac7af0` (review fixes), `b60e3fc` (archive, CONTEXT.md); merged to main in `69f10f2`
