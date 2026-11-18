# 03 — Load test, and a baseline on today's code

Status: ready-for-agent

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

- [ ] `make load-test` runs end to end against a worktree stack and prints the report.
- [ ] The load-test adapters can only be switched on through the Compose override, and a normal `make up` still uses DeepSeek, Tavily and Telegram.
- [ ] No model, search or Telegram network call is made during a run (shown by the load-test adapters' logs, or by no outbound traffic).
- [ ] Tests cover the load-test chat model answering each call shape the app makes, so the app doesn't fail on a canned answer.
- [ ] A baseline run on today's code is recorded under `## Comments`: the full report, plus which bar lines fail and why (for example web pool used up, database pool timeouts, or CPU).
- [ ] The test Users and data it creates stay in the worktree's database, and the run never touches the main stack.

## Blocked by

None - can start immediately

## Comments
