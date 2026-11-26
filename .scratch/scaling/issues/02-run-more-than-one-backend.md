# 02 — Run more than one backend process

Status: needs-triage (parked)

## Why

Later we may want 2+ backend copies, to handle more Users or to stay up if one dies. Today the backend assumes one process (ADR-0032), so a second copy would break things:

- The per-User reply lock is held in memory (`core/incoming_messages.py`, `_turn_lock_for`). Two processes could answer the same User at once.
- The per-User message queue (from issue 01) and the grouping wait (`Timer` port, `adapters/timer.py`) are held in memory.
- Sticker adding mode is held in memory (`core/sticker_adding.py`).
- Typing locks and waits are held in memory (`core/typing_keeper.py`).
- The tick (Check-ins, ended Conversations, Portraits) runs in every process (`adapters/scheduler.py`). The Due Time check on save stops double Check-ins, but both processes would make the same model calls (double cost). See `.scratch/check-in-job/` issue 06.

## Possible directions (not decided)

DB-backed locks (e.g. Postgres advisory locks), a database adapter for the per-User queue port (ADR-0032), one scheduler leader or DB-claimed tick items.

## Next

Blocked by: 01. **Run `/grill-with-docs` again before any work on this.** It's a hard-to-reverse choice and needs an ADR (it touches ADR-0003, ADR-0005 and ADR-0032).

Split from issue 01 on 18 Nov 2026. First raised during the architecture review grilling, 14 Nov 2026.
