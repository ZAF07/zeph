# 01 — Run more than one backend process

Status: needs-triage

## Why

We expect many Users at the same time. Today the backend assumes one process, so running two or more copies would break things:

- The per-User reply lock is a `threading.Lock` in memory (`core/incoming_messages.py`, `_turn_lock_for`). Two processes could answer the same User at once.
- Album grouping waits on an in-memory timer (`Timer` port, `adapters/timer.py`).
- The Check-in scheduler is an in-process loop (`adapters/scheduler.py`). Two processes would send double Check-ins.

## Possible directions (not decided)

DB-backed locks (e.g. Postgres advisory locks), a job queue for replies and Check-ins, one scheduler leader.

## Next

**Run `/grill-with-docs` again before any work on this.** It is a hard-to-reverse choice and needs an ADR (it touches ADR-0003 ports and ADR-0005 Docker Compose).

Raised during the architecture review grilling, 14 Nov 2026.

## Also

- A Check-in tick handles due Users one by one, each `AskModel` User waiting on a model call. Many due Users make a tick slow. Spread across workers or a queue as part of this work.
