# 01 — One backend handles 500 Users

Status: blocked

## Why

We expect about 500 signed-up Users: 25–50 chatting at once, some sending many texts in a row. With one backend process, today's code likely breaks at that load:

- Every message waiting for its User's turn holds a web thread (40 in total, shared with the Dashboard). A few heavy texters can use them all and freeze every chat and the Dashboard.
- The tick (ended Conversations, Portrait rewrites, Check-ins) handles each item one by one, each often waiting on a model call. A big tick makes Check-ins late.

Design decided in ADR-0018. Running 2+ backends is parked in issue 02.

## Next

Blocked by the tick speed-up in `.scratch/check-in-job/` (mainly issue 05, Check-in model calls side by side). Close this once the full load test (100 due Check-ins and 100 ended Conversations) passes with the tick under 60s.

## Comments

### 18 Nov 2026 — grilling, scope changed

- Goal now: **one process per service handles 500 signed-up Users** (about 25–50 chatting at once, some heavy texters). Running 2+ backends stays parked.
- Load test bar (fake model 3–8s per call, no model cost): 50 Users at once, 10 heavy texters sending bursts of 8 texts. Every message answered, no DB timeouts, Dashboard pages under 1s, a 100-Check-in tick under 60s.
- Messages waiting their turn go on an **in-memory per-User queue behind a port**, so they stop holding a thread each.
- **Known trade-off: a restart or deploy drops messages not yet answered.** If the platform gets slow or Users report lost messages, look here first. The fix is a database adapter for the same port.
- Message work runs on **its own fixed thread pool** (size in settings), apart from the web pool, so the Dashboard and webhooks never starve. DB connections are per query, so the default DB pool should hold; the load test confirms it.
- The tick does more than Check-ins: ended Conversations, Portrait rewrites, Check-ins. Each item runs in parallel on **its own small tick pool** (size in settings). The tick waits for all items before the next starts. Load test adds 100 ended Conversations.
- Crisis checks keep today's order: a text sent during a reply is checked after that reply. Changing that is its own issue, if wanted.
- Load test fakes only the chat model (sleeps 3–8s) and Telegram sending. Postgres, the local embedder, the pools and the webhook endpoint stay real. Runs on the worktree's stack.
- Order: (1) `make load-test` plus a baseline run on today's code, (2) per-User queue plus message pool, (3) parallel tick items. Rerun after each slice and record the numbers here. Skip any fix the baseline shows isn't needed.
- Decision recorded in ADR-0018. Next: `/to-prd` then `/to-issues`.

### 23 Nov 2026 — triage, blocked on the tick

- Done: 03 (load test and baseline) and 04 (per-User queue plus message pool), both archived.
- Load test, before 04 → after 04: Dashboard API worst 20.01s (fail) → 0.33s (pass); webhook worst 18.32s → 1.04s; 320/320 texts answered, 0 failed replies, 0 DB timeouts; reply median 42.6s → 40.5s.
- Not done: the tick. 340.6s for 10 due Check-ins and 10 ended Conversations (run with `--tick-users 10`), against a target of under 60s for 100 + 100. That work lives in `.scratch/check-in-job/` issues 01–06, none finished yet.
- Status set to `blocked` until the tick meets the bar.
