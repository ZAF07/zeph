# 03 — Load a User snapshot once per reply and per Check-in tick

Status: ready-for-agent

## Parent

Architecture review, 14 Nov 2026, point 2. Decided in a `/grill-with-docs` session.

## Why

Read once, use many. Each Feature check (`FeatureService.works_for`, about 20 call sites) reloads the User, the Admin switch for all Users and the per-User switches; one reply does about 25 small reads. The User's day is worked out in 4 places, each reloading the User. Reading once also keeps a reply consistent if a switch changes mid-reply. It must scale to many Users at once.

## What to build

A `UserSnapshot` value: the User, their local time, their day, and every Feature's status (works / available / why not).

- Loader with `load(user_id)` and `load_many(user_ids)`.
  - A reply: one `load` when it starts (by the caller of `ReplyGate`), about 3 queries.
  - A Check-in tick: one `load_many` for all due Users; the Admin switch for all Users is read once per tick, per-User switches in one `IN (...)` query. About 3 queries per tick, whatever the number of Users.
- `features.py` still holds the rules (e.g. Personal Stickers needs Stickers); the snapshot only stores the results.
- Steps take the snapshot instead of loading the User or calling `works_for` themselves. `user_today` / `local_now` read it.
- Not in the snapshot: memories, Conversations, platform settings.

## Decisions

- Reason: correctness and consistency first; fewer queries is a bonus that matters at scale.
- Bulk loading from the start, because Check-in ticks must scale.
- Do after issue 01 (`ReplyGate`), since both touch the same steps. Issue 04 (Check-in decision) builds on this.

## Acceptance criteria

- [ ] `UserSnapshot` and a loader with `load` and `load_many`
- [ ] Reply steps and Check-in sending read the snapshot; no step reloads the User or Feature switches mid-reply or mid-tick
- [ ] Test showing the query count for a reply and for a tick with many due Users stays flat
- [ ] No change in behaviour; existing tests pass; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [ ] `/run`: a reply and a Check-in tick work as before

## Blocked by

- `.scratch/architecture/issues/01-reply-gate.md`
