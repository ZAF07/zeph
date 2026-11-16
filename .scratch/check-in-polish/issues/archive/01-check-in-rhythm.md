# 01 — Check-in polish: steady Due Times, "a few times a day", User Portrait for Check-ins

Status: completed

Track: A (User side). Runs alongside track B (issues 03, 04).

## Parent

`.scratch/check-in-polish/PRD.md`

## What to build

Make a User's Check-ins keep the rhythm they picked, and let them pick a faster one.

- **Steady Due Times.** After a Check-in is sent or skipped, the next Due Time is the first of "previous Due Time + n × frequency gap" that is still to come. Due Times missed while held back (e.g. a long pause) are not made up. A Due Time never falls within half a frequency gap of the last *sent* Check-in; one that would is moved to the end of that half gap. A User with no previous Due Time keeps today's behaviour for their first one. No backfill (platform not live).
- **"A few times a day".** A fourth Check-in Frequency, `a_few_times_a_day`.
  - Dashboard label: "A few times a day".
  - Chat wording: "at most a few times a day". The chat tool that changes the frequency accepts it (ADR-0006).
  - Its gap is set by Admins in Platform Settings like the other three. Default 6 hours, shown and editable on the admin Platform Settings page.
  - A data migration adds `a_few_times_a_day: 6` to the stored gaps where it's missing, because reading the gaps fails when a frequency is missing.
- **User Portrait for the standalone Check-in model.** Its input gains the User's User Portrait, next to the Memory Items and Conversation Summaries it already gets. The prompt is unchanged.
- **Conversation quiet gap seed default** becomes 15 minutes. This applies to fresh databases only.

Terms: Due Time, Check-in Frequency (`CONTEXT.md`).

## Acceptance criteria

- [x] A User on "most days" whose Check-in is held back by Quiet Hours or a Conversation gets the following one at their original rhythm, not shifted by the hold-back (end-to-end test through scheduler ticks).
- [x] After a long pause, the User gets one Check-in and then their normal rhythm, with no burst of missed ones.
- [x] A Check-in is never sent within half a frequency gap of the last sent one.
- [x] A skipped Check-in doesn't shift the rhythm.
- [x] Pure decision-function tests cover: several missed Due Times, the half-gap pushing a Due Time, Quiet Hours across midnight, and a first Due Time with no previous one.
- [x] A User can pick "A few times a day" on their Dashboard Check-ins page and in chat. Zeph confirms with "at most a few times a day".
- [x] Admins see and edit the "a few times a day" gap on the Platform Settings page.
- [x] The migration adds the missing gap to an existing database, and reading the gaps works afterwards (tested).
- [x] The standalone Check-in model's input includes the User Portrait (test via the scripted chat model).
- [x] The seed default for the Conversation quiet gap is 15 minutes.
- [x] `pytest`, `ruff`, `ruff format --check`, `mypy`, `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test` all pass.
- [x] Verified in the running app with `/run`. Move DB timestamps back instead of waiting.

## Blocked by

None - can start immediately.

## Notes for parallel work

Track B also changes the Check-in decision and tick code and adds migrations. Whichever merges second rebases, and renumbers its migration if they clash.

## Comments

**2026-11-16 — done.**

How the rhythm is kept: hold-backs move `check_in_next_due_at` (so a held-back User isn't re-read every tick) and save the Due Time the Check-in was first due at in a new column, `users.check_in_held_back_due_at` (migration 0047). A decision counts the next Due Time from it (`CheckInSettings.rhythm_due_at`), then clears it. A refused send that is retried, and a daily-limit skip, keep it too. Turning Check-ins off or on, or changing the frequency, clears it, since the rhythm starts again.

Decisions made without asking:
- After an "until I resume" pause, the rhythm continues from the Due Time before the pause (the issue expected a fresh one). Either way the User gets one Check-in and then their normal rhythm.
- None of the frequency gaps was on the admin Platform Settings page, so all four are now editable there (new `hours_by_frequency` setting kind, 1–720 hours each).

Notes for track B: track B merged first with 0046, so this is 0047. `HoldBack` keeps its shape. `AskModel` now has `next_due_if_sent` and `next_due_if_skipped`. `SkipForDailyLimit` has `stays_due_at`.

## Evidence

- Rhythm, end to end through scheduler ticks: `tests/test_check_in_rhythm.py`. It covers:
  - holding back by Quiet Hours or by a Conversation
  - a skip
  - a long pause (one Check-in, then the normal rhythm)
  - the half gap
  - a refused retry
  - a frequency change resetting the rhythm

  Four of these failed on the old code.
- Pure decision tests: `tests/test_check_in_decision.py::test_next_due_after_decision` (several missed Due Times, the half gap, no previous Due Time), plus `test_decide_check_in` cases:
  - Quiet Hours across midnight
  - a send pushed by the half gap
  - a daily-limit skip after a hold-back
- "A few times a day":
  - in chat: `tests/test_settings_via_chat.py::test_asking_for_check_ins_a_few_times_a_day_in_chat`
  - Dashboard API: `tests/test_check_ins.py::test_user_can_pick_a_few_times_a_day`
  - Dashboard page: `CheckInsSettings.test.tsx` "lets a User pick a few times a day"
  - Admin gaps:
    - `tests/test_admin_settings.py::test_the_check_in_gaps_can_be_changed_and_are_explained_when_refused`
    - `PlatformSettingsForm.test.tsx` "shows each frequency's Check-in gap and saves them together"
- Migration: `tests/test_check_in_gaps_migration.py` (adds the gap and reads it afterwards; keeps one already set).
- User Portrait: `tests/test_check_in_sending.py::test_the_check_in_model_is_given_the_user_portrait`.
- Quiet gap seed of 15: `tests/test_admin_settings.py::test_admin_sees_each_editable_setting_with_its_seeded_value`, `tests/test_setting_keys.py`.
- Checks: backend 1117 passed, with ruff, ruff format --check and mypy clean. Web: lint, format:check and typecheck clean, 426 tests passed.
- `/run` on the worktree stack (ports 3020/8020):
  - `make db-copy` from the main stack (at 0045), then a restart migrated it to 0046 (now numbered 0047, after track B took 0046). Gaps became `{"weekly": 168, "most_days": 24, "few_times_a_week": 56, "a_few_times_a_day": 6}`, and the stored quiet gap stayed 15.
  - Signed in as Admin, `/admin/settings` showed all four gaps (168/56/24/6). Changing "A few times a day" to 5 saved to the database, then it was set back to 6.
  - On `/check-ins`, "A few times a day" was picked and still showed after a reload. The next Due Time became now + 6 h.
  - The real `CheckInService` ran in a backend container on the worktree database, with the live backend stopped and only the chat channel and model stubbed (the worktree has no real Telegram chat). Times moved by shifting DB rows. Due Time D = 13:06:37, Quiet Hours covering now:
    - the hold-back set next_due_at to 14:16:37 and kept held_back_due_at = 13:06:37
    - after Quiet Hours were shifted off and the Check-in was sent, the next Due Time was 2026-11-17 13:06:37 (D + 24 h), not 13:16:37 (the old rule)
    - the model input included the User Portrait

- After rebasing onto track B (issue 03, which took migration 0046), this issue's migration became 0047.
  - The real-data copy, reset to its 0045 state, migrated 0045 → 0046 → 0047. The users table gained `check_in_held_back_reason`, `check_in_held_back_until`, `settings_changed_by_admin` and `check_in_held_back_due_at`, and the 6 h gap was added.
  - The in-container Check-in run was repeated on the merged code with the same result: next Due Time D + 24 h (13:26:26 tomorrow), not 13:36:26. Track B's held-back reason showed `quiet_hours` while held back and was cleared once sent.
  - Track B's `test_quiet_hours_show_as_held_back_until_they_end_then_clear_once_sent` expected the old rule. It now expects send time + 12 h: the next Due Time (09:00Z) fell 9.5 h after the send, so the half-gap rule pushed it to send time + 12 h.
  - Checks after the rebase: backend 1137 passed with ruff, ruff format --check and mypy clean. Web: lint, format:check and typecheck clean, 448 tests passed.

## Completion

- Completed: 2026-11-16
- Commits: 04686bc (implementation), 9e87408 (review fixes), f7e713d (archive), plus the rebase-onto-issue-03 commit and the merge commit recorded below
