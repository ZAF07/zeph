# 09 — Life Threads on the Memories page

Status: in-progress

## Parent

`.scratch/understanding/PRD.md`

## What to build

Users see "What's going on in your life" on the Memories page: each Life Thread's story, open or settled, and when it was last updated. They can delete one, on the Dashboard or by saying "forget the thing about my sister" in chat (the existing "forget a Memory Item" Chat Setting Change extended to Threads, with Settings in Chat rules as today). Deleting removes it from replies at once. No editing.

## Acceptance criteria

- [ ] Dashboard API: list and delete the User's own Threads
- [ ] Memories page section following `docs/design/zeph-product.html` where it fits; Vitest + RTL tests
- [ ] "Forget that" in chat deletes a Thread and the Dashboard marks it "Changed in chat" where that applies
- [ ] A deleted Thread is never reminded or raised again
- [ ] Shown whether User Memory is on or off
- [ ] Checks pass (backend and `pnpm`)
- [ ] `/run-dashboard`: see and delete a Thread; `/run`: forget one in chat

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
