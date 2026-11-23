# 04 — Messages waiting their turn don't hold a thread

Status: completed

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

- [x] Today's webhook-level tests pass unchanged, using the fake queue.
- [x] New webhook-level test: the webhook returns before the work runs.
- [x] New webhook-level test: a burst of texts sent during a reply gets one reply afterwards, with the texts in order.
- [x] Adapter tests: per-User order, one piece at a time per User, different Users side by side, the N limit, and failed work logged with later work still running. The adapter is added to the contract tests.
- [x] The message pool size is a setting, documented next to the other settings.
- [x] `/run`: in the worktree stack, a User sends texts during a reply (posted to the worktree's webhook) and gets one reply afterwards, and the Dashboard still loads.
- [x] After issue 03 is merged (rebase on `main`), `make load-test` meets the bar: every message answered, no failed replies, no database timeouts, Dashboard API under 1s. Before and after numbers are recorded under `## Comments`. If it misses the bar, record why (for example the database pool) and fix it or raise it.
- [x] `pytest`, `ruff`, `ruff format` and `mypy` pass.

## Blocked by

None - can start immediately. The last load-test criterion needs issue 03 merged first.

## Comments

- 2026-11-23, plan: since this issue was written, message pipeline issue 03 changed the handler: a text is checked even while a reply is written, and can drop it until any of it is sent (ADR-0018 consequences). So "a text sent during a reply is checked after that reply" no longer matches today's code. To keep today's behaviour, the queue takes a key, and each User has two lines on it: their texts to check (keyed by Telegram sender, so `/start`, sticker adding and everything else a sender sends run in order there too) and their replies to write. Each line runs one piece at a time, in order, like the two locks it replaces. A heavy texter holds at most two threads. The webhook calls the handler directly; the handler only adds to the queue.

- 2026-11-23, built: port `UserWorkQueue` (`core/ports.py`), adapter `ThreadPoolUserWorkQueue` (`adapters/user_work_queue.py`; one turn in the pool per key at a time, so a heavy texter can't keep a thread from others), `FakeUserWorkQueue` (`tests/fakes.py`; runs at once, keeps per-key order, can hold work), `InlineUserWorkQueue` for Evals. Setting `MESSAGE_POOL_SIZE` (default 50) in `config.py`, `.env.example` and passed through `docker-compose.yml` (one line, needed so it can be tuned). The webhook calls the handler directly; no more `BackgroundTasks`. The timer only adds "answer" to the User's replies line.
- 2026-11-23, checks: `ruff check`, `ruff format --check` (574 files), `mypy src` (206 files, no issues), `pytest` 1508 passed. Contract test `test_user_work_queues_run_each_keys_work_in_order_one_at_a_time` passes for the thread pool and the fake (`pytest -m contract -k user_work_queues`).
- 2026-11-23, `/run` in the worktree stack (`ai-chat-companion-scaling-04`, backend 8020, web 3020): the real backend (`build_production_app`, real `ThreadPoolUserWorkQueue`, `ThreadTimer`, Postgres, DeepSeek) with only the Telegram chat channel swapped for one that logs sends (a made-up chat can't receive real Telegram sends). Test User inserted with SQL. Posted to `http://127.0.0.1:8020/telegram/webhook` with curl: one text at 11:28:01, then 5 texts the moment the first reply's first part went out (11:28:38). Every webhook post returned 200 in 3–25 ms. Saved in order: the first text, reply part 1, then "wait", "actually it got worse", "he emailed the whole team after", "i feel so small", "what should i do", each saved as it came, while reply part 2 was still going out. After the pause: one reply of 5 parts answering all of it. Model calls: 6 safeguard (one per text), 2 understanding, 2 reply plan, 2 reply; Daily usage counted 2 Messages. Replies ran on `user-work_0`. No tracebacks in the backend log. Dashboard: `/` 200 in 0.08s, `/sign-in` 200 in 0.03s, `/api/me` 401 in 0.02s while the stack ran. Signed-in Dashboard API timing under load is checked by `make load-test`.
- 2026-11-23, `/code-review` (Standards + Spec, since 904ef6a). Standards: no hard breaks. Spec: nothing missing. Fixed:
  - Main finding: a text waiting its turn on the queue wasn't counted as "still being checked", so a reply could start without it. Now a connected User's message counts from when it arrives (`handle`, after one Telegram Connection lookup) until its turn ends. A reply refused meanwhile is held back and added to the replies line once the messages are handled, unless a text started a new wait. New webhook tests: `test_a_text_waiting_its_turn_when_the_wait_ends_joins_the_same_message` and `test_a_reply_held_back_for_a_message_waiting_its_turn_is_sent_once_it_is_handled`. Both were red before the fix.
  - The Evals' `InlineUserWorkQueue` now keeps the port's promise: work added under a running key waits, and failures are logged. `FakeUserWorkQueue` builds on it and can hold one kind of line (`hold(prefix)`). The contract tests run all three queues for order and for failed work.
  - Adapter: the line is moved on in `finally`, so even a `BaseException` doesn't strand a key. The nested lambda became `_queue_answer`.
  - Not changed (judgement calls): string keys with prefixes (same as `message_wait_key`), `max_running` vs `MESSAGE_POOL_SIZE` naming, `Event().wait(0.2)` in an adapter test (same as the timer tests).
  - Known small change: a reply already being written is dropped when the new text's turn starts, not the moment it arrives. The gap is the time to check the User's earlier texts. Under the old locks it was dropped at once.
- 2026-11-23, checks after the fixes: `ruff check` and `ruff format --check` (574 files) clean, `mypy src` no issues, `pytest` 1510 passed, contract `-k user_work_queues` 6 passed.
- 2026-11-23, `/run` again on a rebuilt image, same setup. Sam (new User) sent one text, Maya sent one at the same time. The moment Sam's first reply went out, 4 more texts were posted (each 200 in 3–22 ms). Sam's reply ran on `user-work_0` and Maya's on `user-work_1` side by side. Sam's burst was saved in order ("ok so", "she didnt come to dinner", "and she left me on read", "was it something i said?") and got one reply of 2 parts afterwards (`user-work_3`). Model calls for Sam: 5 safeguard, 2 understanding, 2 reply plan, 2 reply. No tracebacks. Dashboard `/` 200 in 0.66s.
- 2026-11-23, rebased on `main` at 4ddbaea (issue 03 merged): clean rebase. `ruff check`, `ruff format --check` (592 files), `mypy src` (213 files) clean, `pytest` 1551 passed.
- 2026-11-23, load test: `make load-test ARGS="--tick-users 10"` in this worktree (the tick isn't part of the bar, and 100 + 100 takes about 53 minutes). The chat part is the same as the baseline: 50 Users, 10 sending bursts of 8 texts, 320 texts in 180 Messages.

  **Before** (issue 03 baseline, main at 904ef6a, full defaults):
  ```
    PASS  Webhook posts       median 0.45s, worst 18.32s, 0 not 200
    PASS  Texts answered      320 / 320
    PASS  Failed replies      0
    PASS  Database timeouts   0
    FAIL  Dashboard API       median 0.03s, worst 20.01s, 4 of 60 calls over 1s, 0 not 200
    INFO  Reply time          median 42.57s, worst 86.50s
    INFO  Tick                3170.6s for 100 due Check-ins and 100 ended Conversations
  ```
  **After** (this branch, `MESSAGE_POOL_SIZE` default 50):
  ```
  Load test report
    50 Users chatting (10 sending bursts of texts): 320 texts in 180 Messages

    PASS  Webhook posts       median 0.01s, worst 1.04s, 0 not 200
    PASS  Texts answered      320 / 320
    PASS  Failed replies      0
    PASS  Database timeouts   0
    PASS  Dashboard API       median 0.03s, worst 0.33s, 0 of 70 calls over 1s, 0 not 200

    INFO  Reply time          median 40.50s, worst 81.69s (a Message's last text to its first reply, with the Message wait)
    INFO  Fallback answers    0
    INFO  Load-test model     check-in 10, conversation end 10, curiosities 10, life threads 10, patterns 10, portrait 10, reply 180, reply plan 180, safeguard 320, understanding 180
    INFO  Tick                340.6s for 10 due Check-ins and 10 ended Conversations (target 60s, not part of the bar)
  ```
  The bar is met. The Dashboard API's worst call went from 20.0s to 0.33s, and webhook posts from 18.3s to 1.0s, because chat work no longer runs on the web threads. Reply times are about the same, so the 50-thread pool doesn't hold replies back. The default database pool was enough (0 timeouts), so it isn't changed. The tick is still slow (about 17s per item, one after another). That belongs to `.scratch/check-in-job/`.
- Follow-up from issue 03, not done here: `LOAD_TEST_RUN` could move into `config.py` `Settings` now that this issue has landed.

## Completion

- Completed: 2026-11-23
- Commits (fast-forward merged into main at 99f25c9, pushed to origin/main; not merged into `production`, so not live yet):
  - b7ab932 Issue 04: per-User work queue on its own message pool; webhook only hands off
  - bf73272 Issue 04 review fixes: count a User's messages from arrival, faithful inline queue, contract covers failures
  - a4520e5 Issue 04: ADR-0018 and message pipeline doc describe the per-User queue lines
  - 99f25c9 Archive issue 04: per-User work queue verified; load test meets the bar (Dashboard API worst 0.33s, was 20s)
- Note for going live: `MESSAGE_POOL_SIZE` is optional (default 50); the server's `.env` needs no change.
