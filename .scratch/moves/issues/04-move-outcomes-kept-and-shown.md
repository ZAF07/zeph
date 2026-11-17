# 04 — Move Outcomes kept and shown

Status: ready-for-agent
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

- [ ] A Conversation end with User Memory working keeps Move Outcomes for the Moves made; with User Memory off, none are kept.
- [ ] The Portrait is given Move Outcomes when rewritten.
- [ ] Users list and delete their Move Outcomes; deletion triggers the Portrait rewrite.
- [ ] Delete My Data and Account Deletion remove them; Message Retention leaves them.
- [ ] Admins see only a count.
- [ ] Tests at the Conversation-end seam (prior art: the Conversation-end and Life Thread tests), the HTTP seam (prior art: the User Memory API tests) and Vitest + RTL for "What helps you"; backend and web checks pass.
- [ ] `/run`: after a Conversation ends (shift timestamps, don't wait), "What helps you" shows its Move Outcomes and deleting one works.

## Blocked by

- `.scratch/moves/issues/01-moves-shape-replies.md`
