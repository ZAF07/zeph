# 06 — Bug: the tick and a reply can both send the same Check-in

Status: completed

## Parent

`.scratch/check-in-polish/PRD.md` (user story 56: "never get the same Check-in twice"). Found in code review of issue 05.

## Symptom

A User can get the same Check-in twice within seconds: once woven into Zeph's reply, and once as its own message from the scheduler tick. The Check-in Log then shows two Check-ins for one Due Time, or two for one Admin's Check in Now.

Expected: exactly one Check-in. Whichever saves first wins and the other sends nothing.

Affects scheduled Check-ins (since issue 02) and Check in Now (since issue 05). No crash or error; the User sees a duplicate.

## How it happens

1. The Conversation ends (quiet gap passes). A tick reads the User as due, with no open Conversation, and asks the Check-in model what to send. That takes a few seconds.
2. Meanwhile the User sends a message. The reply flow reads the same User as still due and the woven-in call says "weave in". `add_woven_in` saves it (it checks the Due Time is still the one read, which it is), moves the Due Time on and clears any Check in Now.
3. The tick's model call returns. `check_ins.add` saves its own Check-in **without** checking the Due Time it read, overwrites the Due Time and the tick sends the message.

The other order is already safe: if the tick saves first, `add_woven_in` sees a changed Due Time and weaves nothing in.

## Repro

Not yet run as a test; the path is confirmed by reading the code. It can be made deterministic end to end with the existing fakes: in the test, make the scripted Check-in model's answer for the tick's call post a webhook message (scripted to weave the Check-in in) before returning. Then check that the fake chat channel received one Check-in, not two, and that the Check-in Log has one entry. Run it for a scheduled Check-in and for a Check in Now.

## Decided fix (owner, 2026-11-17)

**The tick's save checks the Due Time it read, like `add_woven_in` does.**

- The tick's saves (sent, skipped, and the Ignore Threshold "would you like fewer?") go through only if the User's Due Time is still the one the tick read. This is one conditional update, in the same transaction as the insert.
- The save reports whether it saved. If it didn't, someone else already decided this Check-in: the tick saves nothing, sends nothing and moves on.
- Accepted side effect: if the User changes their Check-in settings during the tick's model call, the Due Time changes, so the tick drops that Check-in and the next tick decides again with the new settings (at most about a minute later).
- Not chosen: claiming the User before the model call (new stored state, stale marks), or re-checking the Conversation before saving (only narrows the gap).

## Suspected location

- `src/companion/core/check_ins.py`: the tick's `check_ins.add` calls (sent via `_save_then_send`, skipped, Ignore Threshold, daily-limit skip).
- `src/companion/core/ports.py` and `src/companion/adapters/postgres/repositories.py`: `PostgresCheckInRepository.add` (unconditional update today); compare `add_woven_in`.

## Acceptance criteria

- [x] A reply that weaves in a Check-in while the tick is deciding it leads to one Check-in sent and one logged, for a scheduled Check-in and for a Check in Now (end-to-end tests, red before the fix).
- [x] When the tick's save is refused, nothing is sent and the woven-in Check-in's Due Time and cleared Check in Now stay as the reply saved them.
- [x] The tick still sends normally when nothing else decided the Check-in (existing Check-in sending, hold-back, daily-limit, send-failure and Check in Now tests pass).
- [x] Tick reads stay flat as due Users grow (`tests/test_check_in_hold_back.py::test_reads_per_tick_stay_the_same_as_due_users_grow` passes).
- [x] Checks pass: `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run mypy src`.
- [x] Verified with `/run`.

## Comments

### 2026-11-17 — done (agent, branch `check-in-polish-06-tick-reply-race`)

What changed:
- `CheckInRepository.add` now takes `due_at_read` and returns whether it saved. Like `add_woven_in`, it moves the Due Time on only if it is still the one read, and inserts the Check-in in the same transaction; both now share `PostgresCheckInRepository._add_if_still_due`.
- The tick passes the Due Time it read (`user.check_ins.next_due_at`) on every save: model skip, daily-limit skip, sent (`_save_then_send`) and "would you like fewer?". A refused save sends nothing, so no Curiosity is marked raised and no Shared Photo goes.
- Accepted side effect, as decided: a settings change or a new Check in Now during the tick's model call also moves the Due Time, so that tick drops the Check-in and the next tick decides again.

Evidence per acceptance criterion:
- One sent, one logged, scheduled and Check in Now: `tests/test_woven_in_check_ins.py::test_a_check_in_woven_in_while_the_tick_decides_it_is_sent_once` and `::test_a_check_in_now_woven_in_while_the_tick_decides_it_is_sent_once`. The scripted Check-in model posts a webhook message (scripted to weave in) during the tick's call. Both failed on the code without the fix (the User also got "hey, how was your day?") and pass with it.
- Refused tick save leaves the reply's work alone: the same tests assert the Due Time is the reply's (`due_at + 1 day`, or `decided_at + 1 day` for Check in Now) and the Check in Now is no longer waiting. `tests/test_check_in_now.py::test_a_check_in_now_asked_while_a_scheduled_one_is_decided_still_waits` now decides from the Due Time read before the request: `add` returns False and the Check in Now still waits.
- Tick still sends normally: `test_check_in_sending.py`, `test_check_in_hold_back.py`, `test_check_ins_over_daily_limit.py`, `test_check_in_send_failures.py`, `test_check_in_now.py` and `test_woven_in_check_ins.py` all pass (93 passed).
- Tick reads stay flat: `tests/test_check_in_hold_back.py::test_reads_per_tick_stay_the_same_as_due_users_grow` passes; the change adds no reads.
- Checks: `uv run pytest` 1185 passed; `ruff check src tests`, `ruff format --check src tests` and `mypy src` clean. Web (no web changes): lint, format:check, typecheck clean, 462 passed.
- `/run` (worktree stack 3020/8020/5452, backend container stopped so its scheduler couldn't tick): the real app (`create_app`, real Postgres repositories) ran on the worktree's migrated database, seeded by the real `companion.prestart`. Only the chat channel (recording), chat model (scripted), Clerk, clock, scheduler and timer were stand-ins, so the race could be timed. Maya's message posted to `/telegram/webhook` during the tick's Check-in model call. Branch code: scheduled → one text sent, Check-in Log `[sent, woven in]`, Due Time 12 Nov → 13 Nov 09:00, 1 `check_ins` row. Check in Now → one text, Log `[sent, woven in, requested by the Admin]`, Check in Now cleared, 1 row. Same script on `main`'s `src`: both cases sent two texts and logged two Check-ins (`[sent woven in, sent not woven in]`).
- `CONTEXT.md`: Check-in says that if a reply weaves one in while it is being decided on its own, whichever is saved first wins and the other sends nothing.

Caveats:
- The live check used a scripted model, not the real one. The race needs the User's message to land during the tick's model call, which can't be timed by hand with a real model, and the change doesn't touch any model call.

## Completion

- Completed: 2026-11-17
- Commits: <filled in after merge>
