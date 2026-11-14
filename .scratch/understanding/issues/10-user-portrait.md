# 10 — User Portrait

Status: ready-for-agent

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
