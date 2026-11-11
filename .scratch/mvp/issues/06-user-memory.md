# 06 — User Memory

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

The Companion remembers Users across Conversations. Introduces the scheduler port (in-process loop) and seam 2 (scheduler tick with fake clock).

On each scheduler tick, Conversations past the quiet gap are ended and processed: one LLM call produces a Conversation Summary (topics and how the User seemed) and add/update/remove operations on the User's Memory Items, each in an active Memory Category. Memory Categories are seeded (Life details, Relationships, Goals, Values & beliefs, Challenges, Preferences, What helps — Values & beliefs, Challenges and Preferences are "always include").

When composing a reply, memory retrieval picks relevant Memory Categories for the message with a cheap LLM call, then loads Memory Items from those plus all "always include" categories, plus the last few Conversation Summaries.

On the Dashboard, the Memories page has two tabs. Memories: Memory Items grouped by Memory Category (names come from data), each showing "From a conversation" and its date, with delete per item, "Delete all memories" and the User Memory on/off switch with a notice when off. Conversation Summaries: a read-only list by date showing the summary and how the User seemed, each deletable. When User Memory is on, the name and "What brings you here?" answers from onboarding are added as Memory Items so the Companion knows them from the first Conversation. With User Memory off, no Summaries or Memory Items are saved, and the Companion still chats.

## Design

- `docs/design/zeph-product.html`: Memories (Memories and Conversation Summaries tabs)

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [ ] A scheduler tick ends Conversations past the quiet gap and runs post-conversation processing once per Conversation
- [ ] Post-conversation processing saves a Conversation Summary and applies add/update/remove operations to Memory Items (no duplicates for a changed fact)
- [ ] Memory Categories are seeded from data files, not code
- [ ] Replies include Memory Items from the picked categories plus "always include" categories, and recent Conversation Summaries
- [ ] Users can view Memory Items by Memory Category on the Dashboard, with source date, and delete any single one or all of them
- [ ] Users can view their Conversation Summaries (summary and mood, by date) and delete any single one
- [ ] With User Memory on, onboarding name and "What brings you here?" answers become Memory Items
- [ ] With User Memory off, post-conversation processing saves nothing and chat still works; existing items remain until deleted
- [ ] Seam 2 tests with a fake clock cover: Conversation ends after quiet gap, Summary and Memory Items saved, update replaces old fact, User Memory off saves nothing
- [ ] Seam 1 tests cover retrieval (picked + always-include categories reach the prompt), the Memory Items API (list, delete, delete all) and the Conversation Summaries API (list, delete)
- [ ] Seam 3 tests cover the Memory page
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/02-chat-with-the-companion.md`
- `.scratch/mvp/issues/03-onboarding.md`
