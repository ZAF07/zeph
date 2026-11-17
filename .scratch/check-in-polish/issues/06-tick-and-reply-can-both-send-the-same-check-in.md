# 06 — Bug: the tick and a reply can both send the same Check-in

Status: ready-for-agent

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

- [ ] A reply that weaves in a Check-in while the tick is deciding it leads to one Check-in sent and one logged, for a scheduled Check-in and for a Check in Now (end-to-end tests, red before the fix).
- [ ] When the tick's save is refused, nothing is sent and the woven-in Check-in's Due Time and cleared Check in Now stay as the reply saved them.
- [ ] The tick still sends normally when nothing else decided the Check-in (existing Check-in sending, hold-back, daily-limit, send-failure and Check in Now tests pass).
- [ ] Tick reads stay flat as due Users grow (`tests/test_check_in_hold_back.py::test_reads_per_tick_stay_the_same_as_due_users_grow` passes).
- [ ] Checks pass: `uv run pytest`, `uv run ruff check src tests`, `uv run ruff format --check src tests`, `uv run mypy src`.
- [ ] Verified with `/run`.

## Comments
