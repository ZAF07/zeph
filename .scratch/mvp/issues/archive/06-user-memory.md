# 06 — User Memory

Status: completed

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

- [x] A scheduler tick ends Conversations past the quiet gap and runs post-conversation processing once per Conversation
- [x] Post-conversation processing saves a Conversation Summary and applies add/update/remove operations to Memory Items (no duplicates for a changed fact)
- [x] Memory Categories are seeded from data files, not code
- [x] Replies include Memory Items from the picked categories plus "always include" categories, and recent Conversation Summaries
- [x] Users can view Memory Items by Memory Category on the Dashboard, with source date, and delete any single one or all of them
- [x] Users can view their Conversation Summaries (summary and mood, by date) and delete any single one
- [x] With User Memory on, onboarding name and "What brings you here?" answers become Memory Items
- [x] With User Memory off, post-conversation processing saves nothing and chat still works; existing items remain until deleted
- [x] Seam 2 tests with a fake clock cover: Conversation ends after quiet gap, Summary and Memory Items saved, update replaces old fact, User Memory off saves nothing
- [x] Seam 1 tests cover retrieval (picked + always-include categories reach the prompt), the Memory Items API (list, delete, delete all) and the Conversation Summaries API (list, delete)
- [x] Seam 3 tests cover the Memory page
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/02-chat-with-the-companion.md`
- `.scratch/mvp/issues/03-onboarding.md`

## Comments

**2026-11-11 — implemented on branch `feat/06-user-memory`.**

Decisions:
- Scheduler port (`core/ports.py`) with an in-process adapter (`adapters/scheduler.py`, a thread that ticks every 60s, chosen by `SCHEDULER_ADAPTER=in_process`). The app starts it in the FastAPI lifespan and stops it on shutdown. Seam 2 tests use `FakeScheduler`, which keeps the tick so tests run it by hand with the fake clock.
- `ScheduledWork.tick()`: ends every open Conversation whose last message is at least the quiet gap old (`conversations.ended_at`), then processes each ended Conversation not yet processed. A message after a Conversation ended always starts a new one.
- "Once per Conversation": the Summary, every Memory Item change and `processed_at` are saved in one transaction, and `conversation_summaries.conversation_id` is unique. A failing model call leaves the Conversation unprocessed, so the next tick tries again. An unreadable answer is asked again once; if it is still unreadable, the Conversation is marked processed with nothing saved, so it is never retried forever.
- Post-conversation processing: one model call returns JSON with `summary`, `mood` and `memory_operations` (add / update / remove). Existing items are shown to the model numbered `[n] (Category) text`. Operations are checked before saving: unknown or archived categories, unknown items, empty text, repeats of a fact already remembered, and a second operation on the same item are all skipped. An update replaces the old fact (no duplicates) and becomes a "conversation" item, even if it started from onboarding. Memory Items keep their saved order (`position`), so the numbers are stable.
- User Memory off: processing saves nothing (the Conversation is just marked processed). Memory retrieval is skipped, so replies use no memory, as the design's paused notice says ("won't use what's below"). Existing items stay until deleted.
- Memory retrieval is a graph step `recall_memory` between the Safeguard and composing. The cheap picking call only offers active, non-"always include" categories that hold items for this User, and is skipped when there are none. A failed call still leaves the "always include" items. Archived categories are left out of retrieval. The newest `recent_conversation_summaries` (seed 3) Summaries are added, with day and mood. The intro line is the `reply_memory_intro` setting.
- Memory Categories are seeded from `seed/memory_categories.yaml` on first run only (empty table). New settings: `memory_processing_prompt/model`, `memory_retrieval_prompt/model`, `recent_conversation_summaries`, `reply_memory_intro`, and `onboarding_name_memory_category` / `onboarding_reasons_memory_category`. "Post-conversation processing" and "Memory retrieval" are on Prompts & models.
- Onboarding with User Memory on: "Goes by {name}" goes in Life details, and "Came to Zeph for: …" plus the free-text note go in Goals (`source=onboarding`). Answering onboarding again replaces earlier onboarding items, so there are no duplicates.
- Dashboard API: `GET/DELETE /api/memory-items`, `DELETE /api/memory-items/{id}`, `GET /api/conversation-summaries`, `DELETE /api/conversation-summaries/{id}`. Another User's ID gives 404. Items are grouped by category in category order; archived categories still show their items.
- Memories page (`/memories`, linked in the sidebar): two tabs, Memory on/paused switch with the paused notice and dimmed items, "From a conversation · 2 Oct" or "From onboarding · …" (the item's last-updated day, in the User's time zone), delete per item, "Delete all memories" with a confirm step, and Summaries by date with "You seemed {mood}" and delete. Left out on purpose: everything tagged Later (Add a memory, Edit, Never remember) and the "Changed in chat" tag (issue 17).

Caveats / follow-ups:
- **First deploy processes old Conversations**: existing Conversations have no `ended_at`, so the first tick ends and processes every one already past the quiet gap (one model call each). In dev this was the owner's single Conversation (1 Summary, 6 Memory Items). They are visible on the Memories page and can be deleted there.
- Small race, not fixed: if a tick ends a Conversation in the instant between a new message choosing it and saving into it (only possible right at the quiet-gap boundary), that one message may miss its Conversation's Summary.
- "You can also tell Zeph 'forget that'" (design and seeded explanation) works today only through post-conversation processing, after the quiet gap. Instant forgetting arrives with settings via chat (issue 17).
- Issue 07 should decide whether archived "always include" categories still reach replies (currently they don't) and add admin category management.
- The "Open Telegram" empty-state link is the bare `https://t.me/`, as in the design. The Dashboard doesn't know the bot username yet.
- Dev database: the unedited `memory_processing_prompt` was updated by hand to the final seed text, since seeding never overwrites.
- Review judgement calls not acted on: onboarding item wording and transcript framing stay in code; duplicated delete/empty-state markup between the two web lists; the active-category filter is repeated in three services; `plan_memory_changes` handles three actions in one loop.

Evidence:
- Seam 2 (`tests/test_post_conversation.py`, 8): ends after the quiet gap and is processed once; an update replaces the old fact; memory off saves nothing and chat still works; a message after the end starts a new Conversation; a failed call is retried on the next tick; an unreadable answer is asked again once; bad operations are skipped and remove works; an updated onboarding item survives redoing onboarding (red before the source fix).
- Seam 1: `tests/test_memory_retrieval.py` (5: picked plus always-include plus Summaries reach the prompt, only the newest 3 Summaries, memory off uses none, a failed pick keeps always-include, no picking call with nothing to pick); `tests/test_user_memory_api.py` (9: list by category, delete one, other User's item 404, delete all keeps Summaries, Summaries list and delete, auth, onboarding on and off, onboarding items reach the first reply); `tests/test_memory_categories_seed.py` (2); `tests/adapters/test_in_process_scheduler.py` (2).
- Seam 3: `web/src/components/Memories.test.tsx` (11) and `dates.test.ts`.
- `make check`: Python 128 passed; web 111 passed; ruff, ruff format, mypy, eslint, prettier, tsc clean.
- `/run` (Docker Compose, real Postgres, DeepSeek and Clerk): migration 0006 ran and seeded 7 categories. A driver used the real app with every production adapter except Telegram (printing channel) and the clock (moved past the quiet gap). Onboarding items reached the first reply ("Rina, right?"). One tick wrote the Summary and 3 items, and a second tick did nothing. "I quit teaching…" updated the item instead of adding one. A message about Jo picked Relationships, and the reply got those items plus Summaries. With memory off: no picking call, no memory in the reply, no new Summary. The API deletes worked and Summaries survived "delete all". Found and fixed in /run: the mood was repeated inside the summary text (prompt tightened). In the browser, as a temporary Clerk User: the Memories page grouped items with "From onboarding · 11 Nov"; delete one; switch to paused (notice, dimmed rows) and back; the Summaries tab with "Wed 11 Nov" and "You seemed …"; delete all, then still empty after a reload, with the Summary kept. Re-run after review fixes. The temporary User, checkpoints and the Clerk account were deleted.

## Completion

- Completed: 2026-11-11
- Commit: 7369f7b, review fixes 069b225 (merged from `feat/06-user-memory` in d7b4e45)
