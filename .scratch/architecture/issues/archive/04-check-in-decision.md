# 04 — Pull the Check-in decision into a pure module

Status: completed

## Parent

Architecture review, 14 Nov 2026, point 3. Decided in a `/grill-with-docs` session.

## Why

`CheckInService._check_in_if_due` (`core/check_ins.py`) mixes repository reads with the "send, skip or hold back" rules, spread across SQL, models and the service. Testing one Quiet Hours edge case needs Postgres, the webhook and the scheduler. Held-back Users stay due and are reloaded every tick, which won't scale.

## What to build

Gather facts → decide (pure) → act.

- `CheckInFacts`: the `UserSnapshot` (issue 03), Telegram Connection, open Conversation, used up the Daily Message Limit, limit skip already today, ignored Check-ins in a row, has Shared Photos, allowed Check-in Kinds.
- `decide_check_in(facts, now)`, pure, returns one of:
  - `HoldBack(retry_at)`: Check-ins off, paused, Quiet Hours, no Telegram Connection, or mid-Conversation. Nothing is logged.
  - `SkipForDailyLimit`: one Skipped Check-in per User-day; the User stays due.
  - `AskAboutFewer`: send the "would you like fewer?" message, then pause.
  - `AskModel(kinds)`: the Check-in model picks a Kind or skips.
- Next-due rules (frequency gap, retry gap, `retry_at`) live in the same pure module.
- `HoldBack.retry_at` is saved as the next due time:
  - Quiet Hours → when Quiet Hours end
  - paused until a time → that time
  - mid-Conversation → when the Conversation could end (quiet gap)
  - paused until resumed, or no Telegram Connection → no due time; resuming or connecting sets one again
- Facts are gathered in bulk for all due Users (`load_many` plus `IN (...)` queries). Only `AskModel` Users cost a model call.
- The due-Users query also skips Users whose Check-ins are off on the Admin side (for everyone or for them). They stay due, so a Check-in can go out on the first tick after an Admin turns it back on (keeps the features/04 decision).

## Decisions

- No change in what Users receive; only fewer wasted reloads.
- Tests: a table of facts → decision for the pure module; keep a few end-to-end tests.

## Acceptance criteria

- [x] `decide_check_in` is pure (no repositories, no clock) and covers every branch above
- [x] Table tests for `decide_check_in`, including Quiet Hours across midnight and pause edges
- [x] Held-back Users get `retry_at` as their next due time; resuming and connecting Telegram set a due time again
- [x] Admin-off Users are skipped in SQL and are picked up on the first tick after it's back on
- [x] Query count per tick stays flat as due Users grow (test)
- [x] Existing Check-in tests pass; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [x] `/run`: a due User gets a Check-in; a User in Quiet Hours is held back and gets one after (shift DB times, don't wait)

## Blocked by

- `.scratch/architecture/issues/03-user-snapshot.md`

## Comments

### 14 Nov 2026 — plan

Branch `arch-04-check-in-decision`, worktree `ai-chat-companion-arch-04`, built on issue 03's branch (not merged yet); rebase on main once it lands.

- New pure module `core/check_in_decision.py`: `CheckInRules` (Admin settings and Kinds, read once per tick), `CheckInFacts`, the four results, `decide_check_in(facts, rules, now)`, and the next-due rules (frequency gap, retry gap, Quiet Hours end, due time after a settings change, resume or pause change). Rules are a separate argument so the facts stay per User.
- "No due time" becomes `next_due_at = NULL`. Today NULL means "due now", so the due query drops that, and migration 0024 gives any Check-ins-on User with no due time a due time of now (keeps them due).
- `HoldBack.retry_at` equal to the current due time means "stays due" (Admin turned Check-ins off between the query and the snapshot, no Kind can be sent, limit skip already today). Nothing is written then.
- Held-back due times are saved in one statement per tick, only where the due time hasn't changed since it was read (so a settings change made meanwhile wins).
- Resuming, or changing a pause, sets a due time of now when the pause had set it (none, or equal to the old pause end). Connecting Telegram sets a due time of now when there is none.
- Bulk reads for all due Users: Telegram Connections, newest Conversations, message counts for each User's day, newest Check-in, newest sent Check-ins (up to the ignore threshold), who has Shared Photos.
- Due query also leaves out Users whose Check-ins are off on the Admin side.
- Known edge (accepted): a User held back until Quiet Hours end who then changes their Quiet Hours or time zone waits until the old end time (at most a day).

### 14 Nov 2026 — done

- Built test-first. `tests/test_check_in_decision.py` (47 table cases) was red before `core/check_in_decision.py` existed. `tests/test_check_in_hold_back.py` was red (6 of 7) before the tick was rewritten.
- `core/check_in_decision.py`: `CheckInRules`, `CheckInFacts`, `HoldBack(reason, retry_at)`, `SkipForDailyLimit`, `AskAboutFewer`, `AskModel`, `decide_check_in(facts, rules, now)`, and the next-due rules (`next_due_after_check_in`, `retry_after_refusal`, `quiet_hours_end_after`, `next_due_after_change`, `next_due_after_quiet_hours_move`). `is_in_quiet_hours` moved here.
- Tick (`CheckInService.send_due`): due query → one `load_many` → bulk facts → decide each → save held-back due times in one statement → carry out the rest.
  - Bulk reads: Telegram Connections, newest Conversations, message counts on each User's day, newest Check-in, newest sent Check-ins (up to the ignore threshold), who has Shared Photos. Kinds and settings are read once.
  - Only `AskModel` Users read more (recent Check-ins, memory, photos) and call the model.
- Due query: `next_due_at <= now` only, so no due time means not due. Admin-off Users (switch for them, else for everyone, else the default) are left out in SQL and keep their due time. Migration 0024 gives Check-ins-on Users with no due time a due time of now. This is a shared file; call it out in the PR or merge note.
- Stays due: a `HoldBack` whose `retry_at` is the current due time writes nothing. This covers Check-ins off (a race with the due query), no Kind to send, and a limit skip already done today.
- Code review (Standards and Spec in parallel). Fixed:
  - Race: a User who resumed or connected Telegram during a tick could be left with no due time. Held-back due times are now saved before any sends. Resume, pause changes and connecting set "due now" when the due time is unset or passed, so the tick's guarded write no longer applies.
  - Changing Quiet Hours or time zone while held back until Quiet Hours end makes the User due now (the edge noted in the plan, now closed).
  - The "would you like fewer?" message is read once per tick. The flat-reads test covers limit-skip and "fewer?" Users too.
  - Names: `current_due_at`, `due_time_change`, and `is_limit_skip_on_their_today(CheckIn | None)`.
  - Not changed: the Admin-switch rule is repeated in the due query (the issue asks for SQL); the `sent_only` flag; `decide_check_in` takes `rules` as a third argument so facts stay per User.
- `/run` (worktree DB on 5552, real DeepSeek): the production app (`build_production_app`) with only the chat channel swapped for one that records, and the scheduler run by hand. It was 12:49 in Singapore. Two Users in Singapore were due:
  - Maya, outside Quiet Hours, got "Hey Maya, just a Saturday hello — hope the afternoon's being kind to you." Her next due time was one day later.
  - Sam, in Quiet Hours 11:49–14:49, was held back. His next due time was saved as 06:49 UTC (14:49 Singapore, when his Quiet Hours end). He was not loaded on the next tick.
  - Shifting Sam's due time and Quiet Hours back by 1:59 (instead of waiting), the next tick sent "Hey Sam, just saying hi. Hope your Saturday's being kind to you so far." Both were saved as `sent`.

## Completion

- Completed: 2026-11-14
- Evidence per criterion:
  - Pure: `src/companion/core/check_in_decision.py` imports only `models` and the pure `timing.is_open` / `local_now`, with no repositories and no clock. It covers HoldBack (off, paused, Quiet Hours, no Telegram Connection, mid-Conversation), SkipForDailyLimit, AskAboutFewer and AskModel.
  - Table tests: `test_decide_check_in`, `test_next_due_after_change`, `test_next_due_after_quiet_hours_move` (47 cases, including Quiet Hours before and after midnight, start and end edges, timed pause ending now, and pause plus Quiet Hours).
  - Held-back due times, resume and connect: `test_a_user_in_quiet_hours_is_due_again_when_they_end_and_not_reloaded_before`, `test_a_user_paused_until_resumed_has_no_due_time_until_they_resume`, `test_a_user_held_back_to_the_end_of_a_timed_pause_gets_one_when_resuming_early`, `test_a_user_with_no_telegram_connection_gets_a_due_time_once_they_connect`, plus the two mid-tick race tests.
  - Admin-off in SQL: `test_users_with_check_ins_off_by_an_admin_are_not_loaded_and_stay_due` (no switch reads while off, sent on the first tick after it is back on) and `test_with_check_ins_off_by_an_admin_none_are_sent_until_it_is_back_on`.
  - Flat queries: `test_reads_per_tick_stay_the_same_as_due_users_grow` (every SELECT by table, equal for 5 and 15 due Users across all five no-model paths).
  - Checks: `pytest` 678 passed (9 evals deselected), `ruff check` and `ruff format --check` clean, `mypy src` no issues in 101 files.
  - `/run`: due User sent; User in Quiet Hours held back to the Quiet Hours end and sent after shifting DB times. See Comments.
