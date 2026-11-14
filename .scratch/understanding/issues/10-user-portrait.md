# 10 — User Portrait

Status: in-progress

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

- [ ] Summaries include a mood arc and what was offered and how it landed
- [ ] Conversation end writes or rewrites the Portrait; it reaches the next Understanding and reply
- [ ] Deleting a Memory Item or Thread triggers a rewrite without it (scripted check that the deleted item isn't in the rewrite input)
- [ ] Deleting the Portrait clears it; it isn't rebuilt while User Memory is off
- [ ] Memories page section and delete; Vitest + RTL tests
- [ ] Delete My Data and Account Deletion remove it
- [ ] Checks pass (backend and `pnpm`)
- [ ] `/run`: after a Conversation ends, the Portrait appears on the Memories page and shapes the next reply (Admin trace)

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
