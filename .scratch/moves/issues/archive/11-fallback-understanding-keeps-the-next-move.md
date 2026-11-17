# 11 — A fallback Understanding doesn't lose the next Move

Status: completed
Lane: A

## Parent

`.scratch/moves/PRD.md` (follow-up to `.scratch/moves/issues/archive/06-unmade-next-move-becomes-a-curiosity.md`)

## What to build

When the Understanding model call fails or can't be read, the reply uses the fallback Understanding, which holds no next Move. If that happens on the last Message, the next Move held before it is lost at Conversation end, so the follow-up never becomes a Curiosity.

- Stored Understandings record whether they were the fallback.
- At Conversation end, Curiosity keeping is shown the next Move of the newest Understanding that wasn't the fallback.
- ADR-0016 says a fallback Understanding neither follows nor drops a next Move.

## Acceptance criteria

- [x] A Conversation whose last Understanding is the fallback still passes the earlier unmade next Move to Curiosity keeping.
- [x] A next Move made or dropped by a real Understanding is still not passed, even if a fallback follows it.
- [x] Understandings store whether they were the fallback (migration; existing rows read as not fallback).
- [x] Conversation-end-seam tests; backend checks pass.
- [x] `/run`: a Conversation whose last Understanding is the fallback produces a Curiosity from the earlier next Move.

## Blocked by

- `.scratch/moves/issues/archive/06-unmade-next-move-becomes-a-curiosity.md` (done)

## Comments

### 2026-11-17 — done (agent, branch `moves-11-fallback-keeps-next-move`)

Found during issue 06's spec review. When the Understanding model fails or can't be read, the reply uses the fallback Understanding, which holds no next Move. If that happened on the last Message, the earlier held next Move was lost at Conversation end.

What changed:
- `Understanding.is_fallback`, stored in the new `understandings.is_fallback` column (migration `0056_fallback_understanding`, on 0055; NOT NULL, default false, so existing rows read as not fallback). It is set when the Understanding model gave no usable form.
- `describe_unmade_next_move` (in `core/curiosities.py`) skips fallback Understandings, so Curiosity keeping is shown the next Move of the newest Understanding the model made.
- ADR-0016 (Consequences) now says a fallback Understanding neither makes nor drops a next Move, so a failure on the last Message doesn't lose the follow-up. CONTEXT.md (Move) says the same in domain words.

Evidence per acceptance criterion:
- A fallback last Understanding still passes the earlier next Move: `tests/test_unmade_next_move.py::test_a_fallback_last_understanding_still_passes_the_earlier_next_move` (the model raises on the last Understanding).
- A next Move made or dropped by a real Understanding is not passed, even with a fallback after it: `test_a_next_move_made_before_a_fallback_is_not_passed` and `test_a_next_move_dropped_before_a_fallback_is_not_passed` (an unreadable answer).
- Understandings store whether they were the fallback: `test_understandings_store_whether_they_were_the_fallback` (`[False, True]`), plus `tests/test_moves_migration.py::test_the_fallback_migration_adds_a_column_that_defaults_to_not_fallback` (NOT NULL, default false).
- Conversation-end-seam tests, backend checks: the tests above. On the final code: `ruff check`, `ruff format --check`, `mypy` clean (179 files); `pytest` 1250 passed. No web changes.
- `/run` (worktree stack 3020/8020/5452; migrations ran to 0056 on the stack). The run was inside the backend container: real repositories, DeepSeek chat model, Tavily web search and embedder. Only the chat channel, timer and scheduler were fakes (Telegram can't reach a made-up chat), and the real clock was moved on past the quiet gap. The real model was made to raise on the 3rd Message's Understanding call only. A plain User sent "going around in circles on where to host my app", then "small next.js app, budget SGD 15-20 a month, needs managed postgres", then "ok thanks, let me look at those".
  - Understandings: `Advice / Research, next Suggest, is_fallback false` → `Advice / Research + Suggest, next Plan steps ("once they pick a host, so setup and deploy doesn't become the next loop"), is_fallback false` → `Ask more, no Moves, is_fallback true`.
  - Curiosity keeping was shown "A next Move Zeph had in mind but never made: Plan steps, once they pick a host, so setup and deploy doesn't become the next loop."
  - Curiosity saved: "Which host did you end up going with — Render, or did you try the Vercel plus Neon combo? And how did setup go?", not before 2026-11-20, sensitivity low, waiting.

Code review (standards and spec): no hard violations, nothing wrong. Fixed: added the made-then-fallback test; the migration test's name now says it checks the column default; the `is_fallback` docstring says it is this Understanding. Kept: the next Understanding is still shown a fallback as an earlier Understanding with no next Move. The real earlier next Move is listed above it, and the issue only covers Conversation end.

Caveats:
- Shared files touched: a new migration (0056, on 0055), `tables.py`, the Postgres repository. Lane B's issue 08 was in progress at the same time; if it adds a migration, it must point at 0056.

## Completion

- Completed: 2026-11-17
- Commit: `b8b043d` — Moves issue 11: a fallback Understanding doesn't lose the next Move — Understandings record whether they were the fallback (migration 0056), and Curiosity keeping is shown the next Move of the newest Understanding the model made; ADR-0016 and CONTEXT.md say a fallback neither makes nor drops one
- Commit: `0306536` — Moves issue 11: review fixes — test for a next Move made before a fallback, migration test name says it checks the column default, is_fallback docstring says it's this Understanding
