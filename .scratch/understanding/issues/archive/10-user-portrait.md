# 10 — User Portrait

Status: completed

## Parent

`.scratch/understanding/PRD.md`

## What to build

The Companion has a sense of who the User is as a whole (`CONTEXT.md` "User Portrait").

- **Summaries grow:** each Conversation Summary also records a mood arc (from the Conversation's Understandings) and what the Companion offered and how it landed.
- **Portrait written at Conversation end** from Memory Items, Life Threads and Summaries: who they are, what's going on now, recurring themes, what helps and what doesn't, where they stand on their Goals. Prompt and model are Admin settings. Not while User Memory doesn't work for the User.
- **Used every time:** the Understanding call and the reply call both get it, and the Understanding fallback includes it.
- **Memories page:** "What I know about you" shows it; the User can delete it (cleared; rebuilt only at a later Conversation end with User Memory working). No editing.
- **Deleting really forgets:** deleting a Memory Item or Life Thread rewrites the Portrait without it, in the background, right away.
- Admins see only whether a User has one. Delete My Data and Account Deletion remove it.

## Acceptance criteria

- [x] Summaries include a mood arc and what was offered and how it landed
- [x] Conversation end writes or rewrites the Portrait; it reaches the next Understanding and reply
- [x] Deleting a Memory Item or Thread triggers a rewrite without it (scripted check that the deleted item isn't in the rewrite input)
- [x] Deleting the Portrait clears it; it isn't rebuilt while User Memory is off
- [x] Memories page section and delete; Vitest + RTL tests
- [x] Delete My Data and Account Deletion remove it
- [x] Checks pass (backend and `pnpm`)
- [x] `/run`: after a Conversation ends, the Portrait appears on the Memories page and shapes the next reply (Admin trace)

## Blocked by

- `.scratch/understanding/issues/09-threads-on-memories-page.md`

## Comments

**Plan (14 Nov 2026, branch `understanding-10-user-portrait`, worktree `ai-chat-companion-understanding-10`):**

- Summaries: the Conversation-end call is shown the Conversation's Understandings (time, mood, intensity) and writes `mood` as an arc plus a new `offered` field (what Zeph offered and how it landed). New column `conversation_summaries.offered`. Replies, the Understanding and the Dashboard show it.
- New `user_portraits` table (one row per User): text, when its inputs were read, when a rewrite was asked for.
- `PortraitWriter` (own Admin prompt and model, step `portrait`): writes the Portrait from Memory Items, Life Threads and the newest Summaries only, never from the old Portrait, so a deleted thing can't survive a rewrite. Runs at Conversation end after Life Thread keeping, only while User Memory works.
- Used every time: the Portrait joins `SavedMemory`, so the Understanding sees it and the reply's memory section starts with it, also when the Understanding fails.
- Deleting a Memory Item or Thread (Dashboard or chat) asks for a rewrite in the database; the next scheduler tick (every minute) rewrites it. Survives restarts and merges several deletes into one rewrite.
- Deleting the Portrait clears it (row kept, text emptied, time noted), so a Conversation-end write already under way can't bring it back. A save only lands if its inputs were read after the last save or clear.
- Dashboard API `GET/DELETE /api/user-portrait`; Memories page "About you" tab ("What I know about you"); Admin Users page shows only whether a User has one. Delete My Data and Account Deletion remove it.

- Decisions:
  - The Portrait is written only from Memory Items, Life Threads and the 10 newest Summaries, never from the old Portrait, so a rewrite can't carry a deleted thing forward.
  - Deletion rewrites are queued in the database (`user_portraits.rewrite_requested_at`) and done by the next scheduler tick (every 60 s), not in the request. They run whatever User Memory says, because they only forget. A User with no Portrait gets none.
  - A deletion rewrite that fails or comes back empty clears the Portrait instead of retrying, so the deleted thing is never used again (review finding).
  - Deleting a Conversation Summary or "delete all memories" also asks for a rewrite. Not named in the issue, but it is the same "deleting really forgets" rule.
  - Race safety: a save only lands if its inputs were read at or after the last save or clear (`written_at`). A clear keeps the row with no text and the clear time. A rewrite request survives a save that read its inputs before the request.
  - Summaries: `mood` is now an arc, worked out from each Understanding's mood (time, mood, intensity) plus the Conversation. A new `offered` field holds what Zeph offered and how it landed; it is shown in replies, in the Understanding and on the Dashboard.
  - New Model Call Log step `portrait` and trace kind `portrait_rewrite`. Core Service "User Portrait" (prompt and model on Prompts and Models).
  - Memories page: an "About you" tab headed "What I know about you". The design file has no Portrait section, so it is styled like the Threads tab. No editing.
  - Migration 0032 (renumbered after issue 07 took 0031) adds `user_portraits` and `conversation_summaries.offered`, and reloads the `memory_processing_prompt` and `understanding_prompt` seeds.
- Known limits (not fixed here):
  - A deleted Memory Item can still show up in the rewritten Portrait if the same fact is also in a Life Thread or Summary. This happened in the /run: "nurse" stayed after deleting "They work as a nurse on night shifts." The rewrite input really was without the item. Deleting the Thread or Summary too removes it.
  - Delete My Data while a Conversation-end write is running can leave a fresh Portrait behind. The same race already exists for Summaries, Memory Items and Life Threads, so it should be its own issue.

## Evidence

- **Summaries record a mood arc and what was offered:** `tests/test_user_portrait.py::test_the_summary_records_the_mood_arc_and_what_was_offered`. The processing call sees "anxious (high)" and "calmer (low)", the API returns `offered`, and the next reply gets it. Dashboard: `Memories.test.tsx` "lists Conversation Summaries…" shows the offered line. /run: summary mood "drained and guilty at first, a little lighter by the end"; offered "Offered space to vent without pep talks; they opened up and said the river walk helped a bit."
- **Conversation end writes or rewrites the Portrait; it reaches the next Understanding and reply:** `test_a_conversation_end_writes_the_portrait_from_memory_threads_and_summaries`, `test_the_next_conversation_end_rewrites_the_portrait` (the old Portrait is not in the input), `test_the_portrait_reaches_the_next_understanding_and_reply`, `test_a_failed_understanding_still_gives_the_reply_the_portrait`, `test_a_failing_portrait_writer_keeps_the_summary_and_the_old_portrait`.
- **Deleting a Memory Item or Thread rewrites without it (scripted check of the input):** `test_deleting_a_memory_item_rewrites_the_portrait_without_it` (the deleted fact and the old Portrait are absent from the rewrite input, the kept fact is present), `test_deleting_a_life_thread_rewrites_the_portrait_without_it`, `test_forgetting_in_chat_rewrites_the_portrait_without_it`, `test_deleting_with_user_memory_off_still_rewrites_the_portrait_without_it`, `test_a_memory_item_deleted_while_the_portrait_is_written_is_rewritten_out`, `test_a_failed_rewrite_after_a_deletion_clears_the_portrait`. Mutation check: with the rewrite request removed, 4 of these fail.
- **Deleting the Portrait clears it; not rebuilt while User Memory is off:** `test_deleting_the_portrait_clears_it_until_a_later_conversation_end_with_memory_on` (204, then 404; the reply no longer gets it; still none after a Conversation end with Memory off; rebuilt after one with Memory on), `test_deleting_a_memory_item_with_no_portrait_writes_none`, `test_a_portrait_deleted_while_one_is_being_written_stays_deleted` (mutation check: with the save guard removed it fails), `test_with_user_memory_off_no_portrait_is_written_but_the_saved_one_is_used`, `test_a_user_sees_only_their_own_portrait`.
- **Memories page section and delete; Vitest + RTL:** `web/src/components/UserPortraitSection.tsx`; `Memories.test.tsx` covers showing it with "Updated 13 Nov" and no textbox, deleting it, keeping it with an alert when delete fails, the empty state, and still deleting with User Memory off. Admin: `AdminUsers.test.tsx` shows the Portrait column Yes/No; `test_admins_see_only_whether_a_user_has_a_portrait` (no text in the response).
- **Delete My Data and Account Deletion remove it:** `tests/test_data_deletion.py`. The setup User now has a Portrait, so `user_portraits` is among the per-User tables that must hold data before and none after; `GET /api/user-portrait` returns null after Delete My Data.
- **Checks (rebased on main with issue 07):** `pytest` 863 passed, 9 deselected; `ruff check`, `ruff format --check`, `mypy src` clean; `pnpm lint`, `format:check`, `typecheck` clean; `pnpm test` 368 passed.
- **/run (worktree, real DeepSeek and database):** signed in as an Admin with `run-dashboard`. Conversations ran in a one-off backend container with only the chat channel recorded (worktree Telegram can't send to a fake chat), with the clock moved back 3 days for Conversation 1.
  - Conversation 1: "I'm a nurse and the night shifts are wrecking me", "snapping at my partner Alex", "pep talks don't help, I just need to vent", "a walk by the river… helped a bit". At its end the real writer got the Memory Items, the Life Thread and the Summary, and wrote a Portrait ("They're a nurse working night shifts… Pep talks don't land with them; what does help is… a walk by the river…").
  - Conversation 2, "another night shift tonight, dreading it": the Admin's full-content trace shows the Understanding got "Their User Portrait: …" and the reply got "Who they are: …". Zeph answered "That's the worst part, isn't it — the dread before it even starts… Is it the shift itself you're dreading, or the state you'll come home in?" (no pep talk).
  - Browser: the "About you" tab showed the Portrait with "Updated 11 Nov" and no page errors, at 1280 px and at 390 px (scroll width 390). Deleting "They work as a nurse on night shifts." on the Memories tab set a rewrite request. The running backend's next tick rewrote it (trace kind `portrait_rewrite`, step `portrait`), and the rewrite input had no such Memory Item; see the known limit above. Deleting the Portrait in the browser showed "Nothing here yet" after a reload; the database row had no text and the clear time.
- **/code-review:**
  - Standards: no hard violations. Fixed: shared `format_items_by_category` replaces the duplicated loop; `moods` is now required; the TSDoc names the "About you" tab; three docstrings re-wrapped. Kept: `clear()` used to drop a request for a User with no Portrait, because it also stops an older write from landing; `""` for "no Portrait" in `SavedMemory`, matching how other text fields work; `format_time` sits beside `format_day`; the API names the time `updated_at`, like Life Threads.
  - Spec: fixed the race where a clear between the "has a Portrait" check and the rewrite's read time could be overwritten (the time is now taken first), and the endless retry of a failing rewrite (it clears instead). Kept as recorded decisions: deleting a Summary or deleting all items also rewrites; rewrites run with User Memory off; Delete My Data racing a Conversation-end write (see known limits).

## Completion

- Completed: 2026-11-14
- Commits: <filled in after merge>
