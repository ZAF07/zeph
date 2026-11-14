# 03 — Load a User snapshot once per reply and per Check-in tick

Status: completed

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

- [x] `UserSnapshot` and a loader with `load` and `load_many`
- [x] Reply steps and Check-in sending read the snapshot; no step reloads the User or Feature switches mid-reply or mid-tick
- [x] Test showing the query count for a reply and for a tick with many due Users stays flat
- [x] No change in behaviour; existing tests pass; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [x] `/run`: a reply and a Check-in tick work as before

## Blocked by

- `.scratch/architecture/issues/01-reply-gate.md`

## Comments

### 14 Nov 2026 — plan (branch `arch-03-user-snapshot`)

- `core/user_snapshot.py`: `UserSnapshot` (User, local time, day, Feature statuses; `works`/`available`) and `UserSnapshotLoader.load` / `load_many`.
- `features.py` keeps the rules as a pure `feature_statuses(...)`; `FeatureService` and the loader both use it.
- New repo reads: `users.get_many`, `feature_switches.list_for_users` (one `IN (...)` query each).
- Reply: `IncomingMessageHandler._answer` loads the snapshot inside the User's turn lock and passes it to the engine (LangGraph run `context`, never checkpointed). ReplyGate, Safeguard, data deletion check, usage, memory/Knowledge recall, composer and its tools read it. `UsageRecordingChatModel.generate` takes the snapshot so token days use it.
- Check-in tick: `send_due` does one `load_many` for all due Users.
- Post-conversation does one `load` per Conversation (it uses the chat model, which now needs a snapshot).
- Left as is on purpose: settings tools and data deletion re-read the User right before they write, so two changes in one reply build on each other.

### 14 Nov 2026 — done (pending merge)

- Built test-first: `tests/test_user_snapshot.py` was red before the change (one reply read `users` 16 times and each switch table 8 times), then green.
- `UserSnapshot` lives in `core/models.py` (next to `User` and `FeatureStatus`, so `ports.py` can name it without a circular import). `UserSnapshotLoader` (`core/user_snapshot.py`) has `load`, `find` and `load_many`.
- `features.py` keeps the rules as pure `feature_statuses` and `switches_for_everyone`; `FeatureService` uses them too. A test checks snapshot statuses equal `FeatureService.statuses_for`.
- Reply: loaded once inside the User's turn lock (`IncomingMessageHandler._answer`), passed to `ConversationEngine.handle` and on as the LangGraph run `context` (never checkpointed). `WebSearchTools`, `StickerTools`, `SettingsTools`, `MemoryRetrieval`, `KnowledgeRetrieval`, `PhotoService`, `PersonalStickerKeeper` no longer take `FeatureService`. `timing.user_today` and `FeatureService.unavailable_for` are gone; `local_now` moved to `timing.py`.
- Check-in tick: one `load_many` for all due Users.
- Still re-read on purpose: settings tools and Delete My Data read the User right before they write. The Delete My Data check now reads the snapshot first, so a normal message no longer reads the User for it. The Admin "add this" sticker reply (`StickerAdding._is_admin`) runs before a reply starts and still reads the User.
- Small behaviour edge, in line with "consistent within a reply": the User's day is fixed when the reply or tick starts, so tokens from a reply that crosses midnight go on the day it started.
- Code review (Standards and Spec in parallel). Fixed: snapshot parameters renamed `user` → `snapshot` (no more `user.user.id`), unused `UserSnapshot.available` removed, `find` added for post-conversation, `local_now(time_zone, now)` now matches `users_today`. Not changed: `CheckInService.kinds_for(user)` still asks `FeatureService` (Dashboard only); `UserNotFoundError` stays in `admin_users`; the test reuses helpers from `test_check_in_sending` like other tests do.
- `/run` (worktree stack, ports 8130/5562, real DeepSeek): the production app (`build_production_app`) with only the chat channel swapped for one that records (Telegram can't reach a fake chat) and the scheduler run by hand. For a seeded connected User in Singapore:
  - Message "hey Zeph, long day at work today, my manager moved every deadline up" got a composed reply ("Hey. That sounds exhausting — having the ground shift under you like that." / "Are you carrying the whole lot home with you tonight…"). Reads during the reply: users 1, feature_switches 1, user_feature_switches 1.
  - Conversation shifted 3 hours back and Check-in made due, then one tick: post-conversation saved the summary ("They had a long day at work after their manager moved every deadline up…") and a Check-in was sent ("How's the weekend treating you after that deadline pile-up?…"), saved as `sent`. Reads during the tick: users 3, feature_switches 2, user_feature_switches 2 (post-conversation's snapshot 1/1/1, plus the due list and one `load_many` for Check-ins 2/1/1).

## Completion

- Completed: 2026-11-14
- Evidence per criterion:
  - `UserSnapshot` (`src/companion/core/models.py`) and `UserSnapshotLoader` with `load`, `find`, `load_many` (`src/companion/core/user_snapshot.py`); `test_snapshots_hold_the_same_feature_statuses_as_the_feature_service`.
  - Reply steps and Check-in sending read the snapshot: only Dashboard, onboarding, admin and read-before-write paths still call `users.get` / `works_for` in `src/companion/core`.
  - Query counts: `test_a_reply_reads_the_user_and_their_switches_once` (1/1/1) and `test_a_check_in_tick_reads_users_and_switches_the_same_for_many_due_users` (1 vs 5 due Users equal).
  - `pytest` 619 passed after rebasing onto issue 10 (613 before; 9 deselected evals), `ruff check` and `ruff format --check` clean, `mypy src` no issues in 98 files.
  - `/run`: reply and tick in the real app, see Comments.
- Rebased onto issue 10 (Check-in Kinds ignore the User Memory switch). Conflicts in `check_ins.py` and `features.py` kept issue 10's rules (every Kind for every User; Shared Photos depend only on Photo Viewing; `name_in_reply_note`) with the snapshot reads. `/run` redone after the rebase for a new seeded User: reply composed and sent with reads 1/1/1; tick saved the summary and sent a Check-in ("How's the weekend treating you after that deadline mess on Friday?…"), reads 3/2/2.
- Commits: 82bc8ce "Load a User snapshot once per reply and per Check-in tick", 1b383c1 "Review fixes: name snapshot parameters snapshot, add find", archive 5105636 "Architecture issue 03 done: archive issue with test, run and review evidence" (merged from `arch-03-user-snapshot` in b8a0853 "Merge architecture issue 03: load a User snapshot once per reply and per Check-in tick")
