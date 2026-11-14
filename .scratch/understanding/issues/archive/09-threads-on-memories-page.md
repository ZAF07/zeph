# 09 — Life Threads on the Memories page

Status: completed

## Parent

`.scratch/understanding/PRD.md`

## What to build

Users see "What's going on in your life" on the Memories page: each Life Thread's story, open or settled, and when it was last updated. They can delete one, on the Dashboard or by saying "forget the thing about my sister" in chat (the existing "forget a Memory Item" Chat Setting Change extended to Threads, with Settings in Chat rules as today). Deleting removes it from replies at once. No editing.

## Acceptance criteria

- [x] Dashboard API: list and delete the User's own Threads
- [x] Memories page section following `docs/design/zeph-product.html` where it fits; Vitest + RTL tests
- [x] "Forget that" in chat deletes a Thread and the Dashboard marks it "Changed in chat" where that applies
- [x] A deleted Thread is never reminded or raised again
- [x] Shown whether User Memory is on or off
- [x] Checks pass (backend and `pnpm`)
- [x] `/run-dashboard`: see and delete a Thread; `/run`: forget one in chat

## Blocked by

- `.scratch/understanding/issues/08-life-threads-and-being-reminded.md`

## Comments

**Plan (14 Nov 2026, branch `understanding-09-threads-memories-page`):**

- Backend: Life Thread repository gets `list_for_user` and `delete`; `UserMemoryService` gets `list_threads` / `delete_thread`; Dashboard API `GET /api/life-threads` (open first, then latest updated) and `DELETE /api/life-threads/{id}` (404 if not the User's).
- Conversation-end keeping only updates Threads it changed (never re-inserts), so a Thread deleted while keeping runs stays deleted.
- Chat: `list_memories` also lists the User's Threads, numbered after the Memory Items; `forget_memory` forgets either. No new tool.
- "Changed in chat": a forgotten Thread is gone, so there is nothing left to mark (same as forgetting a Memory Item today). No caption applies.
- Dashboard: a "What's going on" tab on the Memories page, styled like the Conversation Summaries list (the design file has no Threads section). Shown whether User Memory is on or off.
- No migration needed.

- Decisions:
  - The Threads are a "What's going on" tab (heading "What's going on in your life") between Memories and Conversation Summaries, styled like the Summaries cards, with an Open / Settled tag and "Updated <day>". The design file has no Threads section.
  - Chat: no new tool. `list_memories` lists Memory Items, then Threads ("A story in their life: <title>. <story>"), numbered on from the items; `forget_memory` forgets either.
  - "Changed in chat" does not apply: a forgotten Thread is gone, so nothing is left to mark (as with forgetting a Memory Item). CONTEXT.md now says so.
  - Conversation-end keeping used to save with insert-or-update, so a Thread deleted while keeping ran (a model call of a few seconds) would come back. `save_many` now takes `added` and `changed`: added ones are inserted, changed ones only update rows that still exist.
  - Portrait rewrite and Curiosity cascades on delete wait for issues 10 and 11 (not built yet).
  - No migration.

## Evidence

- **Dashboard API, list and delete own Threads:** `tests/test_life_threads_dashboard.py`: `test_a_user_sees_their_threads_open_first_with_story_and_when_updated` (open first, then latest updated; fields id, title, story, is_open, updated_at), `test_a_deleted_thread_is_gone_and_never_reminded_again` (204, then 404 the second time), `test_a_user_cannot_see_or_delete_another_users_thread` (404, the owner's Thread stays).
- **Memories page section, Vitest + RTL:** `web/src/components/LifeThreadsList.tsx`; `web/src/components/Memories.test.tsx`: shows story, Open/Settled and "Updated 12 Nov"; deletes; keeps it and shows an alert when delete fails; empty state; still shown and deletable with User Memory off.
- **"Forget that" in chat:** `test_forgetting_a_thread_in_chat` (listed with its story, forgotten by number, gone from the API and from the next Understanding). "Changed in chat": not applicable (see decisions).
- **Never reminded or raised again:** `test_a_deleted_thread_is_gone_and_never_reminded_again` (the next Understanding doesn't see it; Admin count goes to 0), `test_a_thread_deleted_while_conversation_end_keeps_it_stays_deleted` (deleted during the keeping call, which then tries to update it: still gone).
- **Shown whether User Memory is on or off:** `test_threads_are_shown_with_user_memory_off` and the matching Vitest test.
- **Checks:** `pytest` 834 passed, 9 deselected; `ruff check`, `ruff format --check`, `mypy src` clean; `pnpm lint`, `format:check`, `typecheck` clean; `pnpm test` 360 passed.
- **/run-dashboard (worktree, signed in as a plain User):** two Threads added with SQL. The "What's going on" tab showed "Falling-out with Mei · Open · Updated 12 Nov" above "Moving flat · Settled · Updated 5 Oct"; deleting the first removed it, and it stayed gone after a reload; no page errors. At 390px with Memory paused, the Thread still showed and the page had no sideways scroll (scroll width 390).
- **/run, forget in chat:** the real app ran in a one-off backend container with the real database and DeepSeek; only the chat channel was a recorder (worktree Telegram can't send to a fake chat). The User, linked with SQL, sent "please forget the thing about my sister". The Model Call Log shows the reply called `list_memories` then `forget_memory`; Zeph said "Done — that one's gone. I won't bring it up again."; only "Moving flat" was left in `life_threads`.
- **/code-review:**
  - Standards: no hard violations. Kept, as judgement calls: the two `isinstance` checks in `chat_settings.py` (only two kinds), the Threads list copying the Summaries list's pattern (matches surrounding code), `list_threads` passing through like `list_summaries`.
  - Spec: no defects. The `save_many` split is beyond the listed criteria but needed for "never raised again". "Changed in chat" settled as not applicable.

## Completion

- Completed: 2026-11-14
- Commits: <filled in after merge>
