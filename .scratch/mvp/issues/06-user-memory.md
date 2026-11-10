# 06 — User Memory

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

The Companion remembers Users across Conversations. Introduces the scheduler port (in-process loop) and seam 2 (scheduler tick with fake clock).

On each scheduler tick, Conversations past the quiet gap are ended and processed: one LLM call produces a Conversation Summary (topics and how the User seemed) and add/update/remove operations on the User's Memory Items, each in an active Memory Category. Memory Categories are seeded (Life details, Relationships, Goals, Values & beliefs, Challenges, Preferences — the last three "always include").

When composing a reply, memory retrieval picks relevant Memory Categories for the message with a cheap LLM call, then loads Memory Items from those plus all "always include" categories, plus the last few Conversation Summaries.

On the Dashboard, Users see their Memory Items grouped by Memory Category and can delete any of them. With User Memory off, no Summaries or Memory Items are saved, and the Companion still chats.

## Acceptance criteria

- [ ] A scheduler tick ends Conversations past the quiet gap and runs post-conversation processing once per Conversation
- [ ] Post-conversation processing saves a Conversation Summary and applies add/update/remove operations to Memory Items (no duplicates for a changed fact)
- [ ] Memory Categories are seeded from data files, not code
- [ ] Replies include Memory Items from the picked categories plus "always include" categories, and recent Conversation Summaries
- [ ] Users can view Memory Items by Memory Category on the Dashboard and delete any single one
- [ ] With User Memory off, post-conversation processing saves nothing and chat still works; existing items remain until deleted
- [ ] Seam 2 tests with a fake clock cover: Conversation ends after quiet gap, Summary and Memory Items saved, update replaces old fact, User Memory off saves nothing
- [ ] Seam 1 tests cover retrieval (picked + always-include categories reach the prompt) and the Memory Items API (list, delete)
- [ ] Seam 3 tests cover the Memory page
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/02-chat-with-the-companion.md`
- `.scratch/mvp/issues/03-onboarding.md`
