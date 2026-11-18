# 04 — Messages waiting their turn don't hold a thread

Status: ready-for-agent

## Parent

`.scratch/scaling/PRD.md`

## What to build

Each User's chat work goes on that User's queue, which runs on a fixed message pool kept apart from the web pool (ADR-0018). A heavy texter then uses about one thread, not one per text, and chat load can't freeze the Dashboard.

- **A new port: User work queue.** Core hands it a piece of work for a User. It promises:
  - each User's work runs one piece at a time, in the order it arrived;
  - different Users run side by side;
  - at most N pieces run at once;
  - a piece that fails is logged and doesn't stop that User's later work.
- **An in-memory adapter:** a fixed thread pool, with N from a new setting read through `config.py` and a sensible default. A User with nothing waiting holds no thread.
- **The incoming message handler uses the queue instead of its per-User reply lock.**
  - Checking a text and answering a Message both go on the User's queue.
  - When the grouping wait ends, the timer adds "answer" to the queue and doesn't run it itself.
  - Grouping rules (waits, Albums, texts still being checked), crisis order (a text sent during a reply is checked after that reply), typing, the fallback reply and the Daily Message Limit all stay as today.
- **The webhook only hands off:** the handler adds work to the queue and returns at once.
- **A fake User work queue** for tests, which runs work right away (in the style of `FakeTimer`), so today's webhook-level tests pass unchanged.
- Sticker adding mode, typing, the timer and the tick are not changed.

## Parallel work (another agent is doing issue 03 at the same time)

- Owns: `config.py`, `app.py` (`AppDependencies`), `core/ports.py`, `core/incoming_messages.py`, the Telegram webhook, `tests/fakes.py`, the contract tests and the new queue adapter.
- In `main.py`, only add the queue to `build_production_app` (one line, next to `timer=`). Don't change the `build_*` adapter functions, because issue 03 edits those.
- Don't touch the `Makefile`, Compose files or the load-test script. Add no packages, so lockfiles stay untouched.

## Acceptance criteria

- [ ] Today's webhook-level tests pass unchanged, using the fake queue.
- [ ] New webhook-level test: the webhook returns before the work runs.
- [ ] New webhook-level test: a burst of texts sent during a reply gets one reply afterwards, with the texts in order.
- [ ] Adapter tests: per-User order, one piece at a time per User, different Users side by side, the N limit, and failed work logged with later work still running. The adapter is added to the contract tests.
- [ ] The message pool size is a setting, documented next to the other settings.
- [ ] `/run`: in the worktree stack, a User sends texts during a reply (posted to the worktree's webhook) and gets one reply afterwards, and the Dashboard still loads.
- [ ] After issue 03 is merged (rebase on `main`), `make load-test` meets the bar: every message answered, no failed replies, no database timeouts, Dashboard API under 1s. Before and after numbers are recorded under `## Comments`. If it misses the bar, record why (for example the database pool) and fix it or raise it.
- [ ] `pytest`, `ruff`, `ruff format` and `mypy` pass.

## Blocked by

None - can start immediately. The last load-test criterion needs issue 03 merged first.

## Comments
