# 04 — Move Outcomes kept and shown

Status: completed
Lane: B

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane A is changing some of the same files (migrations, the seed settings file, the Understanding module, the Conversation-end work, the Dashboard). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

The Companion learns what helped, and the User sees it.

- Move Outcome is a new part of User Memory: Move name, lead or support, the situation, how the User felt, result (helped, didn't, mixed), why, when, and an embedding of situation plus feeling.
- A new Conversation-end step keeps Move Outcomes, alongside Life Threads and Curiosities. It reads the Conversation's messages and Understandings (which name the Moves) and runs only while User Memory works. It has its own model, thinking and prompt in Platform Settings (seeded defaults; editable on the Platform Settings page). The prompt says to write about the moment and what helped, never to judge the User. Its calls are logged under the Conversation-end group.
- The User Portrait is rewritten from Move Outcomes too (seed Portrait prompt updated).
- User API and Dashboard: the Memories page gains "What helps you", listing each Move Outcome (situation, how they felt, result, why, date) with delete. Deleting one rewrites the Portrait within a minute, like a deleted Memory Item.
- Delete My Data and Account Deletion remove Move Outcomes; Message Retention doesn't.
- The admin User view shows only how many Move Outcomes a User has.

## Acceptance criteria

- [x] A Conversation end with User Memory working keeps Move Outcomes for the Moves made; with User Memory off, none are kept.
- [x] The Portrait is given Move Outcomes when rewritten.
- [x] Users list and delete their Move Outcomes; deletion triggers the Portrait rewrite.
- [x] Delete My Data and Account Deletion remove them; Message Retention leaves them.
- [x] Admins see only a count.
- [x] Tests at the Conversation-end seam (prior art: the Conversation-end and Life Thread tests), the HTTP seam (prior art: the User Memory API tests) and Vitest + RTL for "What helps you"; backend and web checks pass.
- [x] `/run`: after a Conversation ends (shift timestamps, don't wait), "What helps you" shows its Move Outcomes and deleting one works.

## Blocked by

- `.scratch/moves/issues/01-moves-shape-replies.md`

## Comments

What changed:
- Move Outcome is a new User Memory record: `MoveOutcome` (Move name, `MoveRole` lead/support, situation, feeling, `MoveResult` helped/didnt_help/mixed, why, `made_at`), `move_outcomes` table (embedding of situation + feeling, indexed by `user_id`), `MoveOutcomeRepository` port + `PostgresMoveOutcomeRepository`.
- Migration `0051_move_outcomes` (revises 0050): the table, and deletes `portrait_prompt` so the updated seed wording loads on next start.
- `core/move_outcomes.py`: `MoveOutcomeKeeper` runs in the Conversation end after Life Threads and Curiosities and before the Portrait, only past the User Memory check. It lists the Moves the Conversation's Understandings made (each Move+role once, at its first time), shows them numbered with how each message was read and the transcript, and keeps one outcome per numbered Move. Unknown or repeated numbers, unknown results or empty fields are skipped; an unreadable answer is asked again once; no Moves means no model call; a failed embedding still keeps the outcome. Logged as step `move_outcomes` in the Conversation-end trace.
- Platform Settings: `move_outcome_keeping_model` / `_thinking` / `_prompt` (seeded; editable; "Move Outcome keeping" core service on Prompts & models). The prompt says to write about the moment and what helped, never judge the person.
- Portrait: `describe_user_memory` gets a "What has helped and what hasn't" section; seed Portrait prompt and its core-service text updated.
- User API: `GET /api/move-outcomes`, `DELETE /api/move-outcomes/{id}` (asks for the Portrait rewrite, like a deleted Memory Item). Delete My Data calls `move_outcomes.delete_for_user`; Account Deletion goes through the same call (and the user FK cascades). Admin Users rows gain `move_outcome_count`.
- Dashboard: "What helps you" tab on Memories (`MoveOutcomesList`: Move, result pill, situation, "You felt …", why, day, delete), "Move Outcomes" column on Admin Users, "Move Outcomes" Model Call Log step.

Decisions made while building:
- The model is shown numbered Moves made, not free names, so it can't invent a Move. Same Move in the same role across messages is shown once; `made_at` is when it was first made.
- No model call when no Move was made (saves cost).
- No `conversation_id` on Move Outcomes: they outlive Message Retention and Conversation deletion by design.
- No design exists for "What helps you"; it copies the "What's going on" tab's look.

Evidence per acceptance criterion:
- Kept with User Memory working, none with it off: `tests/test_move_outcomes.py::test_a_conversation_end_keeps_an_outcome_for_each_move_made`, `test_with_user_memory_off_no_outcomes_are_kept`, `test_with_user_memory_off_by_an_admin_no_outcomes_are_kept`, plus `test_the_same_move_made_twice_is_shown_once`, `test_odd_outcomes_are_skipped_and_the_good_one_kept`, `test_an_unreadable_answer_is_asked_again_once_then_nothing_is_kept`, `test_a_conversation_with_no_moves_asks_nothing`, `test_an_outcome_that_cannot_be_embedded_is_still_kept`, `test_a_failing_keeper_still_writes_the_portrait`.
- Portrait given Move Outcomes: `test_the_portrait_is_given_the_move_outcomes` (and the keeper runs before the Portrait).
- Users list and delete; deletion rewrites the Portrait: `test_deleting_an_outcome_rewrites_the_portrait_without_it`, `test_a_user_cannot_see_or_delete_another_users_outcome`, `test_move_outcome_routes_need_sign_in`.
- Delete My Data / Account Deletion remove them; Message Retention leaves them: `tests/test_data_deletion.py::test_delete_my_data_removes_every_kind_of_data_but_keeps_the_account` (now gives the User a Move Outcome; it checks every per-User table is emptied), `test_message_retention_leaves_move_outcomes`.
- Admins see only a count: `test_admins_see_only_how_many_outcomes_a_user_has` (no situation or why in the response), `tests/test_admin.py`, `web/src/components/AdminUsers.test.tsx`.
- Tests at the three seams; checks pass: backend `ruff check`, `ruff format --check`, `mypy` clean, `pytest` 1213 passed; web `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 67 files / 467 passed (`Memories.test.tsx`: lists, deletes, delete failure, empty state).
- `/run` (worktree stack 3010/8010/5442, real backend, real DeepSeek model and embedder): signed in as a Clerk test User, seeded with SQL an ended Conversation (internal-testing chat: stuck → named three must-work items and Friday, "feel lighter" → "wiped, too many steps") with Understandings making Push, Plan steps and Calm, last message 110 minutes ago. The next scheduler tick processed it: Model Call Log trace `conversation_end` with steps conversation_end, life_threads, curiosities, move_outcomes, portrait, no errors. Kept 2 outcomes, both embedded: Push helped ("Pinning down three must-work items and a date gave them a concrete finish line…") and Plan steps didn't help ("…too much to carry while they were already depleted…"); Calm left out (result unclear). No judging of the User. The Memories "What helps you" tab showed both, newest first; deleting Push removed it and it stayed gone after reload; a `portrait_rewrite` trace ran within a minute (Portrait `written_at` updated). Admin Users showed Move Outcomes = 1, no content. No page errors; 390px renders.

Code review (standards and spec): no hard violations, spec fully met. Fixed: rewrapped the fake chat model's docstring. Kept: the JSON-answer reader and ask-twice loop are now a third copy of the Life Thread and Curiosity ones, and `read_text` is borrowed from `life_threads.py`. Sharing them means changing those modules, so it's left for a separate cleanup.

Caveats:
- Migration 0051 revises 0050. Lane A (issue 02) may add its own migration; whichever merges second must point at the other so there's one head.
- Shared files touched: `tests/conftest.py`, `tests/fakes.py`, the seed settings file, `core/models.py`, `core/ports.py`, `adapters/postgres/repositories.py`, `tables.py`, a new migration.
- Migration 0051 replaces any Dashboard edit to the Portrait prompt with the new seed wording (fine while the owner is the only User).

## Completion

- Completed: 2026-11-17
