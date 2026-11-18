# PRD: One backend handles 500 Users

Status: ready-for-agent

## Problem Statement

We expect about 500 signed-up Users. At a busy time, 25–50 of them chat at once, and some send many texts in a row and go back and forth a lot. The backend runs as one process, and today's code is likely to break at that load:

- Every incoming message is worked on in a thread from one shared web pool of 40 threads, the same pool that serves the Dashboard. A text sent while that User's reply is still being made holds its thread while waiting its turn. A User who sends 10 quick texts during a reply ties up 10 threads.
- A few heavy texters can use up the whole pool. Every User's chat then stalls, and Dashboard pages hang.
- We don't know where the real limits are (threads, database connections, CPU for the local embedder), because nothing measures them.

## Solution

- **Measure first.** A repeatable load test (`make load-test`) drives the real stack with many Users chatting at once. Only the model and Telegram sending are faked, so it costs nothing. We run it on today's code to get a baseline, then after the fix.
- **Messages waiting their turn don't hold a thread.** Each User's work (checking texts, answering a Message) goes on that User's queue. The queue runs each User's work one piece at a time, in order. Different Users run side by side on a fixed pool that is kept apart from the web pool. The webhook only hands the message to the queue and returns right away.
- **One process, in memory, for now** (ADR-0018). The queue sits behind a port, so a database-backed queue can replace it when we run 2+ backends (issue 02). Known trade-off: a restart or deploy drops messages not yet answered.

What Users notice: replies keep coming at busy times, and heavy texters don't slow down anyone else. Admins notice the Dashboard stays fast while many Users chat.

## User Stories

1. As a User, I want a reply even when many other Users are chatting at the same time, so that the Companion feels always there.
2. As a User, I want my reply to take about as long at busy times as at quiet times, apart from the model's own speed, so that busy hours don't feel broken.
3. As a User who sends many quick texts, I want them answered together in one reply, as today, so that the Companion reads my whole thought.
4. As a User who sends many quick texts, I want each text still checked for crisis, as today, so that nothing I say is missed.
5. As a User who texts while a reply is being made, I want my new texts handled after that reply, in the order I sent them, so that the chat makes sense.
6. As a User, I want another User's heavy texting not to slow down my replies, so that one person can't hog the Companion.
7. As a User, I want a failure on one of my messages not to stop my later messages being answered, so that one bad moment doesn't silence the chat.
8. As a User, I want "typing" shown while my reply is worked on, as today, so that I know the Companion is on it.
9. As a User, I want the fallback reply if my reply fails, as today, so that I never get silence.
10. As a User, I want to hit my Daily Message Limit exactly as today, so that busy times don't change the rules.
11. As a User whose text is a crisis, I want the Crisis Reply as today, in the same order as today, so that safety behaviour doesn't change under load.
12. As an Admin, I want the Dashboard to load in under a second while many Users chat, so that I can work at busy times.
13. As an Admin adding stickers in chat, I want adding mode to work as today, so that the change doesn't break my tools.
14. As an Admin, I want the size of the message pool to be a setting, so that it can be tuned without a code change.
15. As the owner, I want a repeatable load test that costs no money, so that I can check the platform still copes after any change.
16. As the owner, I want the load test to run on today's code first, so that we only fix what is actually broken.
17. As the owner, I want the load test to report how many messages were answered, the reply times, Dashboard page times, and any database or thread errors, so that I can see where it breaks.
18. As the owner, I want the load test to cover heavy texters (bursts of 8 texts), so that the worst real pattern is tested.
19. As the owner, I want the load test to also time a tick with 100 due Check-ins and 100 ended Conversations, so that the check-in-job work has a target to beat.
20. As the owner, I want the load test run against a worktree's own stack, so that it never touches real Users or the main database.
21. As a developer, I want the per-User queue behind a port, so that a database-backed queue can replace it later without changing core code.
22. As a developer, I want today's webhook-level tests to pass unchanged, so that I know the behaviour is the same.
23. As a developer investigating slowness or lost messages later, I want the restart trade-off written down, so that I know where to look first.

## Implementation Decisions

- **New port: User work queue.** Core hands it a piece of work for a User. It promises that each User's work runs one piece at a time, in the order it arrived; that different Users' work runs side by side; that at most N pieces run at once; and that a piece that fails is logged and doesn't stop that User's later work.
- **In-memory adapter:** a fixed-size thread pool (N from settings, read through `config.py`), with a list of waiting work per User. A User with nothing waiting holds no thread.
- **The incoming message handler uses the queue instead of its per-User reply lock.** Checking a text and answering a Message are both added to the User's queue. When the grouping wait ends, the timer adds "answer" to the queue and doesn't run it itself. The rules for grouping a Message (waits, Albums, texts still being checked) don't change.
- **The webhook only hands off.** Parsing and the secret check stay. The handler adds work to the queue and returns at once, so web threads are never held by chat work.
- **Crisis checks keep today's order:** a text sent during a reply is checked after that reply.
- **Nothing else changes:** sticker adding mode, typing, the timer and the tick stay as they are. They are single-process (ADR-0018, issue 02).
- **Database pool:** connections are opened per query and not held during model calls, so the default pool should be enough. Change it only if the load test shows database timeouts.
- **Load test:** a script started by `make load-test` against the worktree's running stack.
  - It posts Telegram updates to the backend's webhook for many test Users, and calls a Dashboard API page while that runs.
  - The backend runs with a fake chat model (each call waits a random 3–8s and returns a fitting canned answer) and a fake Telegram sender (records sends, no network). Postgres, the local embedder, the pools and the webhook endpoint are real.
  - The fakes are switched on by a setting that only the load test sets.
  - The test Users are made by the script in the worktree's database.
  - The bar: 50 Users at once, 10 of them sending bursts of 8 texts. Every message answered, no failed replies, no database timeouts, Dashboard API under 1s.
  - A tick with 100 due Check-ins and 100 ended Conversations is timed and reported against a 60s target. That target belongs to the check-in-job work, not this PRD.
- **Order of work:** (1) the load test and a baseline on today's code, (2) the queue and the message pool, (3) a rerun of the load test, with numbers recorded in the issue.

## Testing Decisions

- Good tests check behaviour seen from outside (what the User is sent and in what order, what is saved), not how the queue works inside.
- **Webhook level (existing seam, highest).** Today's tests post updates to `/telegram/webhook` with fakes and must pass unchanged. They use a fake User work queue that runs work right away, in the style of `FakeTimer`. New tests at this level check that the webhook returns before the work runs, and that a burst of texts sent during a reply gets one reply afterwards, in order.
- **The in-memory queue adapter, on its own.** Same style as the thread timer's adapter tests. It checks per-User order, one piece at a time per User, different Users side by side, the N limit, and that failed work is logged and later work still runs. It is added to the adapter contract tests.
- **The load test is not part of `pytest`**, because it is slow and needs the running stack. Its results are recorded in the issue as evidence.
- Prior art: the thread timer's adapter tests, the in-process scheduler's adapter tests, the adapter contract tests, and the Telegram webhook tests with their helpers.

## Out of Scope

- Running 2+ backend processes, a database-backed queue, and keeping unanswered messages across restarts (issue 02).
- Making the tick faster: parallel Check-ins, a separate Check-in loop, bulk loading (`.scratch/check-in-job/`). This PRD only measures the tick.
- Checking crisis texts sooner, while a reply is still running.
- Model provider limits or a second provider.
- Any change to the Dashboard.

## Further Notes

- Decision: ADR-0018. Grilling notes: `.scratch/scaling/issues/01-one-backend-handles-500-users.md`.
- `make load-test` is free, because the model is faked. Real evals are separate and cost money.
