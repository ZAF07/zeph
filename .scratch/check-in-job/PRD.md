# Improve the Check-in background job

Status: needs-triage

> **Owner: when you revisit this, run `/grill-with-docs` first.** Nothing here is decided. The findings and options below came from a code read on 2026-11-18, not from measurements. The issues are a first cut and may change after the grill.

## How it works today (2026-11-18)

- One background thread in the backend runs a scheduler tick, waits 60 seconds after it finishes, then runs the next one (`adapters/scheduler.py`, `SCHEDULER_INTERVAL_SECONDS` in `main.py`).
- Each tick does everything in a row (`core/scheduled_work.py`): end quiet Conversations, process ended ones, rewrite requested User Portraits, **decide on due Check-ins**, delete expired messages, delete pending auth accounts.
- Check-ins (`CheckInService.send_due` in `core/check_ins.py`): the facts for every due User are read in a few bulk queries, `decide_check_in` plans each one, and held-back Users are saved in one statement. Then each User to carry out is handled **one at a time**. For the ones that go to the Check-in model, each waits on a model call (60s timeout in the DeepSeek adapter).
- A save only goes through if the User's Due Time is still the one read (`_add_if_still_due` in the Postgres repositories). This already stops a Check-in being sent twice, even across processes.

## Findings

1. **Slow with many due Users.** Model calls run one after another. 100 due Users at about 5s each is about 8 minutes for one tick. The biggest bursts are likely when Quiet Hours end, since many Users become due at the same time.
2. **It holds up the other tick work.** While Check-ins run, quiet Conversations aren't ended or processed, and the next tick can't start. Conversation ends and Woven-in Check-in timing slip too.
3. **Times go stale.** `now` is read once at the start of the tick. A User handled minutes later gets an old `decided_at`, and the model is told the wrong local time.
4. **Per-User queries in the model step.** For each User sent to the model there are about 7 more queries: Shared Photos, waiting Curiosities, recent Check-ins, User Portrait, Memory Items, Conversation Summaries, and the full list of Memory Categories, which is the same for every User. This goes against the "bulk loads, not per-User queries" rule.
5. **No backoff when a decision fails.** If the model keeps giving an answer we can't use (`InvalidCheckInAnswerError`) or the call keeps failing, the User is tried again on every tick, forever. Each retry is a paid model call.
6. **One process only.** Two backends would *not* double-send (see the save check above; `.scratch/scaling/issues/01-run-more-than-one-backend.md` overstates this). But both would make the same model calls, which doubles the cost, and the work can't be shared between processes.
7. **Nothing to see.** Nothing logs how long a tick takes, how many Users are due, or how far behind it is. Shutdown also waits for a running tick to finish, which could take minutes.

## Options

**A. Quick fixes, same design (small, likely no ADR)**

- Read the model-step facts for all due Users at once.
- Run Check-in model calls side by side with a small fixed number of threads (e.g. 5, set by an Admin or in config). The Due Time save check already keeps each User's work separate.
- Read the time for each User, not once per tick.
- When a decision fails, move the User's Due Time back a little. After a few failures in a row, record a Skipped Check-in with the reason.
- Give Check-ins their own loop, apart from Conversation ending and the other tidy-up work.
- Log tick duration and how many Users are due.

**B. Claim work in the database (medium, needs an ADR)**

- Each worker claims a batch of due Users with `SELECT … FOR UPDATE SKIP LOCKED` and a short claim lease, so any number of backends or workers can run without two of them deciding on the same User.
- The `Scheduler` port stays as it is. The job could run in its own worker container in Docker Compose (touches ADR-0003 and ADR-0005).
- Covers the Check-in part of `.scratch/scaling/issues/01-run-more-than-one-backend.md`.

**C. A real job queue (large, needs an ADR)**

- E.g. Procrastinate (runs on Postgres) or arq/Celery (need Redis). Each Check-in becomes its own job, with retries and rate limits built in.
- Only worth it if many more kinds of background work are coming.

**Recommendation at the time:** do A, measuring first, then do B as part of the scaling work. Skip C for now.

## Issues

1. `issues/01-tick-timing-and-backlog-logged.md`: measure first
2. `issues/02-failed-check-in-decisions-back-off.md`
3. `issues/03-check-ins-run-in-their-own-loop.md`
4. `issues/04-bulk-load-check-in-model-facts.md` (blocked by 01)
5. `issues/05-check-in-model-calls-side-by-side.md` (blocked by 01, 03, 04)
6. `issues/06-share-check-in-work-across-backends.md` (blocked by 05 and the scaling grill)

## Comments

- 2026-11-18: Filed from a code-read investigation. Owner will revisit and run `/grill-with-docs` before any work starts.
