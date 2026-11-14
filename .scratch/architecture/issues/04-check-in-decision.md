# 04 — Pull the Check-in decision into a pure module

Status: ready-for-agent

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

- [ ] `decide_check_in` is pure (no repositories, no clock) and covers every branch above
- [ ] Table tests for `decide_check_in`, including Quiet Hours across midnight and pause edges
- [ ] Held-back Users get `retry_at` as their next due time; resuming and connecting Telegram set a due time again
- [ ] Admin-off Users are skipped in SQL and are picked up on the first tick after it's back on
- [ ] Query count per tick stays flat as due Users grow (test)
- [ ] Existing Check-in tests pass; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [ ] `/run`: a due User gets a Check-in; a User in Quiet Hours is held back and gets one after (shift DB times, don't wait)

## Blocked by

- `.scratch/architecture/issues/03-user-snapshot.md`
