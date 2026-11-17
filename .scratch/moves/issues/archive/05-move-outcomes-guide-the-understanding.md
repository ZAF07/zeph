# 05 — Move Outcomes guide the Understanding

Status: completed
Lane: B

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane A is changing some of the same files (the seed settings file, the Understanding module). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

Zeph picks help that has worked for this User in moments like this one.

- Before each Understanding, find the User's own Move Outcomes closest in meaning to the incoming Message (with the Conversation so far), compared against each Move Outcome's situation and feeling through the existing Embedder port.
- Admins set how many reach the Understanding (starting at 3) and the closeness bar, as new Platform Settings on the settings page.
- The Understanding is shown them with their dates; the seed Understanding prompt says that a Move that helped before may not help now, depending on how the User feels.
- Move Outcomes are used while User Memory is off (that only stops learning).
- Look-ups are per User and indexed, for many Users at once.

## Acceptance criteria

- [x] Only the User's own Move Outcomes, close enough and up to the Admin-set count, reach the Understanding.
- [x] They still reach it with User Memory off.
- [x] Admins change the count and closeness bar on the Dashboard.
- [x] Webhook-seam tests with the fake embedder (prior art: the Life Thread and older Summaries tests); backend and web checks pass.
- [x] `/run`: a User with a "Push backfired when exhausted" outcome who says they're exhausted gets an Understanding that sees it.

## Blocked by

- `.scratch/moves/issues/04-move-outcomes-kept-and-shown.md`

## Comments

What changed:
- Two new Platform Settings: `move_outcomes_per_understanding` (seeded 3, 0–10) and `move_outcomes_closeness_percent` (seeded 65, 0–100), editable on the Platform Settings page under Memory ("Most Move Outcomes per Understanding", "Move Outcome closeness bar"). New keys load from the seed on their own.
- `MoveOutcomeRepository.find_by_meaning` (port + Postgres): only the User's own rows (by the `user_id` index), with an embedding, cosine closeness past the bar, closest first, up to the limit.
- `core/move_outcomes.py`: `MoveOutcomeFinder.find` embeds the User's last few texts in the Conversation and searches. No User Memory check (off only stops learning). A failed search logs and returns none, so the reply still goes.
- `ReplyService` finds them before the Understanding; `UnderstandingService.understand` shows them as "How Moves went for them before in moments like this, closest first:" with their days (`describe_move_outcome`), or "None found."
- Seed Understanding prompt: names Move Outcomes in what it is given, and under `lead_move` says to lean towards what helped in a similar situation and mood, but that a Move that helped before may not help now; go by how they feel today. Migration `0053` (revises 0052) deletes `understanding_prompt` so the new wording loads on next start.
- `life_threads.recent_incoming_texts` is shared by Life Threads and Move Outcomes (constant renamed `RECENT_TEXTS_TO_SEARCH`).
- `CONTEXT.md` Move Outcome term says how they reach the Understanding.

Decisions made while building:
- "The incoming Message with the Conversation so far" is read as the User's last 3 texts in the Conversation, the same window Life Threads use. Zeph's own replies are left out so the search matches the User's situation and mood, not Zeph's words.
- "Indexed": the search stays inside one User's rows through the `user_id` index and compares them exactly. No vector (HNSW) index: with a per-User filter it would lose matches, and one User has few outcomes.
- Closeness bar 65: measured with the real bge-small embedder: same situation and mood scored 75–84, unrelated texts up to 62.

Evidence per acceptance criterion:
- Only the User's own, close enough, up to the count: `tests/test_move_outcome_recall.py::test_close_outcomes_reach_the_understanding_with_their_dates` (date and why shown, far one left out), `test_only_the_users_own_outcomes_reach_the_understanding` (another User's kept outcome never shown, even with the bar at 0), `test_the_admin_sets_how_many_reach_it_and_how_close_they_must_be` (1 → closest only, 0 → none, bar 100 → none).
- Still reach it with User Memory off: `test_outcomes_still_reach_the_understanding_with_user_memory_off`.
- Admins change the count and bar on the Dashboard: `web/src/components/PlatformSettingsForm.test.tsx` "shows and saves the Move Outcome number and closeness bar"; the backend tests change both through `PATCH /api/admin/settings`. Not clicked in a browser in this run.
- Webhook-seam tests with the fake embedder, plus `test_the_reply_still_goes_when_outcomes_cannot_be_searched`. Checks: backend `ruff check`, `ruff format --check`, `mypy` clean, `pytest` 1232 passed; web `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 68 files / 479 passed.
- `/run` (worktree stack 3020/8020/5452, real DeepSeek model and fastembed embedder; the app run inside the backend container with only the chat channel recording, a manual scheduler and an at-once timer): alembic at 0053, both settings seeded (3, 65), the stored Understanding prompt has the new wording. A User with two outcomes, "Push (lead) didn't help, exhausted late at night with a pile of tasks" and "Research helped, app hosting", sent "I'm so exhausted. still have a pile of tasks to get through tonight". The Understanding was given only the Push outcome with its day ("7 Nov 2026: Push (lead) didn't help. … Felt: exhausted, drained. …"); the hosting one stayed below the bar. It answered Need Be heard, no Move, nuance "acknowledge the pile without turning it into a plan or pushing them to power through"; the reply was "That sounds rough. Already running on empty and there's still a whole pile waiting for you. / Want to tell me what's on the list?"

Code review (standards and spec): no hard violations, nothing wrong. Fixed: the copied "last few texts" lines are one shared helper, its constant has a neutral name, two docstrings rewrapped. Kept: the Understanding's long parameter list (an existing trend; worth a separate cleanup).

Caveats:
- Migration 0053 revises 0052. Lane A (issue 03) may add its own migration and also edits the seed Understanding prompt and `understanding.py`; whichever merges second points at the other and keeps both prompt changes.
- Migration 0053 replaces any Dashboard edit to the Understanding prompt with the seed wording (fine while the owner is the only User).
- Shared files touched: the seed settings file, `core/ports.py`, `adapters/postgres/repositories.py`, `app.py`, a new migration.

## Completion

- Completed: 2026-11-17
- Commit: `f8f1f90` — Move Outcomes guide the Understanding: before each reply the User's own Move Outcomes closest to their last few texts are shown to the Understanding with their days, up to an Admin-set number and past an Admin-set closeness bar, even with User Memory off; the seed Understanding prompt says what helped before may not help now
- Commit: `928a2ff` — Moves issue 05: review fixes — Life Threads and Move Outcomes search with one shared recent_incoming_texts helper, its constant is named RECENT_TEXTS_TO_SEARCH, two docstrings rewrapped
- Commit: `edc5224` — Moves issue 05 done: archive issue with check and run evidence
- Merge: `753cdff` — Merge Moves issue 05: Move Outcomes guide the Understanding
