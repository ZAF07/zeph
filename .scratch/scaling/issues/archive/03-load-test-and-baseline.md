# 03 — Load test, and a baseline on today's code

Status: completed

## Parent

`.scratch/scaling/PRD.md`

## What to build

A repeatable, free load test, started with `make load-test` against a worktree's own running stack. Run it on today's code and record where it breaks.

- **Load-test adapters**, chosen through the existing adapter settings, for the parts that cost money or reach outside:
  - a chat model that waits a random 3–8s per call and returns a fitting canned answer. It must work for every call shape the app makes: replies, Understanding, crisis checks, Check-ins, post-Conversation work;
  - a photo viewer;
  - web search;
  - a Telegram chat channel that records sends and makes no network calls;
  - whatever auth the script needs to call one Dashboard API page.

  Postgres, the local embedder, the thread pools and the webhook endpoint stay real.
- **A Compose override file** that only the load test uses, so these adapters can never be on in a normal run.
- **The script:**
  1. creates test Users with Telegram Connections in the worktree's database;
  2. posts Telegram updates to the backend's webhook: 50 Users at once, 10 of them sending bursts of 8 texts, the rest going back and forth normally;
  3. calls a Dashboard API page every few seconds while that runs;
  4. separately, makes 100 Users due a Check-in and ends 100 Conversations, then times one tick;
  5. reports messages answered vs sent, reply times (median and worst), failed replies, database timeouts or pool errors from the backend logs, Dashboard API times, and tick time.
- **The bar** (pass or fail for each line in the report): every message answered, no failed replies, no database timeouts, Dashboard API under 1s. The tick is reported against a 60s target, but it doesn't fail the run: speeding up the tick belongs to `.scratch/check-in-job/`.

## Parallel work (another agent is doing issue 04 at the same time)

- Touch only: the `build_*` adapter functions in `main.py` (add load-test choices; don't change `build_production_app`), new load-test adapter files, the new load-test script and Compose override, and a new `Makefile` target.
- Don't touch `config.py`, `app.py`, `core/ports.py`, `core/incoming_messages.py`, the Telegram webhook, `tests/fakes.py` or the contract tests. Issue 04 owns those.
- Add no packages, so lockfiles stay untouched. If one is truly needed, say so in the PR.

## Acceptance criteria

- [x] `make load-test` runs end to end against a worktree stack and prints the report.
- [x] The load-test adapters can only be switched on through the Compose override, and a normal `make up` still uses DeepSeek, Tavily and Telegram.
- [x] No model, search or Telegram network call is made during a run (shown by the load-test adapters' logs, or by no outbound traffic).
- [x] Tests cover the load-test chat model answering each call shape the app makes, so the app doesn't fail on a canned answer.
- [x] A baseline run on today's code is recorded under `## Comments`: the full report, plus which bar lines fail and why (for example web pool used up, database pool timeouts, or CPU).
- [x] The test Users and data it creates stay in the worktree's database, and the run never touches the main stack.

## Blocked by

None - can start immediately

## Comments

### 2026-11-23 — Built, and baseline on today's code

**What was built**

- `src/companion/adapters/load_test/`: `LoadTestChatModel` (waits 3–8s, tells each call apart by comparing its instructions with the prompts in Platform settings, then gives a fitting canned answer for all 14 call shapes), `LoadTestPhotoViewer`, `EmptyWebSearch`, `LoggingChatChannel` (logs each send with its chat, sends nothing), `LoadTestAccounts` (sign-in for `load-test-…` tokens), `TimedScheduler` (the real scheduler, logging each tick's length).
- `main.py`: a `load_test` choice in the `build_*` functions. Each one refuses to start unless `LOAD_TEST_RUN=true`.
- `docker-compose.load-test.yml` sets `LOAD_TEST_RUN` and the choices. The main Compose file never passes `LOAD_TEST_RUN`, so `.env` alone can't turn them on (tested, and checked in the running backend).
- `scripts/load_test/` and `make load-test` (`ARGS="--tick-users 10"` for a shorter run).

**Decisions and follow-ups**

- `LOAD_TEST_RUN` is read by a small settings class in `adapters/load_test/switch.py`, not `config.py`, because issue 04 owns `config.py`. Follow-up: move it into `Settings` once 04 lands.
- The fake chat model reads prompts through its own database engine, because `build_production_app` was off-limits. It is a separate small pool, so it doesn't add to the app pool's numbers.
- The script deletes its test Users at the start and end of a run. Otherwise a normal backend on the same database would later make real, paid model calls and Telegram sends for them (Check-ins, Conversation ends). They live only in the worktree's database while the run lasts.
- The Safeguard always answers "none", so the crisis path isn't load-tested.
- The backend stays on the load-test adapters after a run; `make restart` puts it back.

**Baseline report (main at 904ef6a, `make load-test`, full defaults)**

```
Load test report
  50 Users chatting (10 sending bursts of texts): 320 texts in 180 Messages

  PASS  Webhook posts       median 0.45s, worst 18.32s, 0 not 200
  PASS  Texts answered      320 / 320
  PASS  Failed replies      0
  PASS  Database timeouts   0
  FAIL  Dashboard API       median 0.03s, worst 20.01s, 4 of 60 calls over 1s, 0 not 200

  INFO  Reply time          median 42.57s, worst 86.50s (a Message's last text to its first reply, with the Message wait)
  INFO  Fallback answers    0
  INFO  Load-test model     check-in 100, conversation end 100, curiosities 100, life threads 100, patterns 100, portrait 100, reply 180, reply plan 180, safeguard 320, understanding 180
  INFO  Tick                3170.6s for 100 due Check-ins and 100 ended Conversations (target 60s, not part of the bar)
```

**Which bar lines fail and why**

- **Dashboard API fails** (worst 20.0s, 4 of 60 calls over 1s). Cause: the web pool is used up. The webhook answers at once but hands each text to FastAPI `BackgroundTasks`. Sync background tasks run in the same 40-thread pool as the Dashboard's endpoints. Each text check holds a thread for its Safeguard call (3–8s), and a heavy texter's later texts sit in that pool waiting on the User's check lock. During the bursts the pool is full, so Dashboard calls and webhook posts queue behind them: webhook posts reached 18.3s at the same time. It is not the database: 0 timeouts or pool errors. CPU was not measured on its own, but a CPU limit wouldn't leave the median Dashboard call at 0.03s. This is what issue 04 fixes.
- Every other line passes: all 320 texts answered, no failed replies, no database timeouts, no fallback from any canned answer.
- **Tick**: 3,170.6s (53 min) against the 60s target. Each Conversation end makes about 5 model calls and each Check-in one, all one after another (about 26s per Conversation), so 100 + 100 take most of an hour. That belongs to `.scratch/check-in-job/`.
- No model, search or Telegram call was made: the load-test model answered all 1,560 model calls (above), and every send went through the logging channel.
- Running-app checks: the test Users were removed afterwards (0 left). On the load-test backend the env showed `LOAD_TEST_RUN=true` and every chosen adapter `load_test`. After `docker compose up -d backend` without the override it showed deepseek, tavily, telegram, clerk and in_process, with no load-test log lines. `CHAT_MODEL_ADAPTER=load_test` without `LOAD_TEST_RUN` raised `LoadTestNotAllowedError` in the running backend.
- Checks: `pytest` 1539 passed, `ruff`, `ruff format`, `mypy` clean.

## Completion

- Completed: 2026-11-23
- Commit: <to be filled in after merge>
