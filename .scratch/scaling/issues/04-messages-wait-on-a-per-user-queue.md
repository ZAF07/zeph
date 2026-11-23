# 04 — Messages waiting their turn don't hold a thread

Status: in-progress

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

- 2026-11-23, plan: since this issue was written, message pipeline issue 03 changed the handler: a text is checked even while a reply is written, and can drop it until any of it is sent (ADR-0018 consequences). So "a text sent during a reply is checked after that reply" no longer matches today's code. To keep today's behaviour, the queue takes a key, and each User has two lines on it: their texts to check (keyed by Telegram sender, so `/start`, sticker adding and everything else a sender sends run in order there too) and their replies to write. Each line runs one piece at a time, in order, like the two locks it replaces. A heavy texter holds at most two threads. The webhook calls the handler directly; the handler only adds to the queue.

- 2026-11-23, built: port `UserWorkQueue` (`core/ports.py`), adapter `ThreadPoolUserWorkQueue` (`adapters/user_work_queue.py`; one turn in the pool per key at a time, so a heavy texter can't keep a thread from others), `FakeUserWorkQueue` (`tests/fakes.py`; runs at once, keeps per-key order, can hold work), `InlineUserWorkQueue` for Evals. Setting `MESSAGE_POOL_SIZE` (default 50) in `config.py`, `.env.example` and passed through `docker-compose.yml` (one line, needed so it can be tuned). The webhook calls the handler directly; no more `BackgroundTasks`. The timer only adds "answer" to the User's replies line.
- 2026-11-23, checks: `ruff check`, `ruff format --check` (574 files), `mypy src` (206 files, no issues), `pytest` 1508 passed. Contract test `test_user_work_queues_run_each_keys_work_in_order_one_at_a_time` passes for the thread pool and the fake (`pytest -m contract -k user_work_queues`).
- 2026-11-23, `/run` in the worktree stack (`ai-chat-companion-scaling-04`, backend 8020, web 3020): the real backend (`build_production_app`, real `ThreadPoolUserWorkQueue`, `ThreadTimer`, Postgres, DeepSeek) with only the Telegram chat channel swapped for one that logs sends (a made-up chat can't receive real Telegram sends). Test User inserted with SQL. Posted to `http://127.0.0.1:8020/telegram/webhook` with curl: one text at 11:28:01, then 5 texts the moment the first reply's first part went out (11:28:38). Every webhook post returned 200 in 3–25 ms. Saved in order: the first text, reply part 1, then "wait", "actually it got worse", "he emailed the whole team after", "i feel so small", "what should i do", each saved as it came, while reply part 2 was still going out. After the pause: one reply of 5 parts answering all of it. Model calls: 6 safeguard (one per text), 2 understanding, 2 reply plan, 2 reply; Daily usage counted 2 Messages. Replies ran on `user-work_0`. No tracebacks in the backend log. Dashboard: `/` 200 in 0.08s, `/sign-in` 200 in 0.03s, `/api/me` 401 in 0.02s while the stack ran. Signed-in Dashboard API timing under load is checked by `make load-test`.
