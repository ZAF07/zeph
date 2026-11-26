# User Memory: what Zeph keeps and when it uses it

What Zeph keeps about a User, which step writes it, which step reads it, and how the User sees and deletes it. Terms in **bold** are defined in `CONTEXT.md`. For the full reply path, see `docs/message-pipeline/README.md`.

One home for each thing learned: **a fact is a Memory Item, a story is a Life Thread, and what keeps showing up across stories is a Pattern.**

## The kinds of User Memory

All of these are written when a Conversation ends (after the quiet gap, `conversation_quiet_gap_minutes`, 15 to start). Numbers are starting values of Platform Settings unless marked "in code".

| Kind | What it is (example) | Written by | Read by | Table | Code |
|---|---|---|---|---|---|
| **Memory Item** | One fact in one **Memory Category** ("Goes by Sam", a goal) | Step a, one model call. Also onboarding answers (`remember_onboarding`) | Every reply: items in "always include" categories, plus categories the Reply Plan picks by name | `memory_items` | `core/post_conversation.py` (`DayMemoryWriter`), `core/user_memory.py` |
| **Day Summary** | One per User per day: what was said, the mood arc, what Zeph offered and how it landed | Step a, rewritten from all of that day's messages | Newest 3 go into every reply; older ones found by meaning | `day_summaries` | `core/post_conversation.py`, `core/memory_retrieval.py` |
| **Shared Photo** | A photo that matters, with a description and why it matters ("Miso is their cat") | Step a, only while Photo Viewing works | All of them go into the reply when the Reply Plan picks the "Shared Photos" group | `shared_photos` | `core/photos.py` |
| **Life Thread** | An ongoing story ("job hunt", "falling-out with sister"), open or settled | Step b, one model call | Recall, before every reply (`ThreadReminder`) | `life_threads` | `core/life_threads.py` |
| **Observation** | A quote kept as evidence for or against a Pattern | Step b2 (tagging) | Scoring and the ready gate | `observations` | `core/observations.py` |
| **Pattern** | What keeps showing up across stories | Steps b3 to c | Recall and the Reply Plan | `patterns` | `core/patterns.py`, `core/pattern_scoring.py` |
| **Move Outcome** | How one Move went, in which situation and mood ("suggested a walk; it helped") | Step e, one model call | Before every reply, by meaning (`MoveOutcomeFinder`) | `move_outcomes` | `core/move_outcomes.py` |
| **User Portrait** | A short picture of who they are, now | Step f, last, one model call | The Understanding and every reply ("Who they are") | `user_portraits` | `core/user_portrait.py` |

For Observations and Patterns (tagging, scoring, states, sharing), see `docs/pattern-pipeline/lifecycle.md` and `docs/pattern-pipeline/tagging.md`. Not repeated here.

**Memory Categories** are Admin-managed (admin page `memory-categories`, `core/memory_categories.py`). One can be archived, never deleted: its items stay for the User to see and delete, but get no new ones and no longer go into replies. A Required Memory Category (named by the onboarding and Home goals settings) can't be archived.

### Curiosities are not User Memory

**Curiosities** (things Zeph wants to ask later, guesses included) are internal (ADR 0017). Users don't see them. They are made at Conversation end (step d, table `curiosities`, `core/curiosities.py`), but they are not User Memory. Delete My Data removes them. Deleting the Memory Item or Life Thread one came from removes it too (cascading foreign keys `source_memory_item_id`, `source_life_thread_id`). So does deleting the kept quote, Pattern or Prediction it is about.

### Not User Memory either

- **Knowledge** is a shared library, never about one User.
- **Personal Stickers** are kept at every Conversation end while the Personal Stickers Feature works, whatever User Memory says, but are separate.
- **Understandings** and **Reply Plans** are removed with the messages they were made for.

## Conversation-end order

`PostConversationProcessor.process` in `core/post_conversation.py`. Each step uses what the earlier ones wrote.

| # | Step | Runs when |
|---|---|---|
| 0 | Personal Stickers (not User Memory) | Personal Stickers works, whatever User Memory says |
| a | Day Summary, Memory Item changes, Shared Photos (one call) | User Memory works |
| b | Life Threads | User Memory works |
| b2 | Tag Observations | Also Pattern noticing works and the User pressed "Got it" |
| b3, b4 | Settle reactions and Predictions, score Patterns, ready gate | Also Pattern noticing works |
| c | Unmatched Patterns | User Memory works |
| c2 | Familiarity | **Always** |
| d | Curiosities, then Agenda, starter Thought Experiments, Prediction follow-ups | Also Curiosities works (each has its own extra gates) |
| e | Move Outcomes | User Memory works |
| f | User Portrait | User Memory works |

Why the order matters:

- Life Threads (b) return the Threads the Conversation touched. Tagging (b2) and Patterns (c) need them, so an Observation can link to its Thread.
- Scoring (b3) needs the Observations from b2. The ready gate needs the scores.
- The Portrait (f) is written last, from everything above.

Failures: if step a's model call raises, the Conversation stays unprocessed and the next tick tries again. An unreadable answer is asked once more, then nothing is saved and it is marked processed. Every later step logs its own failure and is not tried again, so nothing is added twice.

## Recall: how memory is found for a reply

Plain code, no model call. Runs in `ReplyService` (`core/reply_service.py`): saved memory is read before the Understanding; Threads, Patterns, Curiosities and Move Outcomes are found between the Understanding and the Reply Plan; the memory section, with older Day Summaries, is written after the Reply Plan.

**Embeddings.** `FastEmbedEmbedder` (`adapters/fastembed/embedder.py`) runs `BAAI/bge-small-en-v1.5` locally, 384 numbers per text. Stored in pgvector columns in Postgres (`EMBEDDING_SIZE` in `adapters/postgres/tables.py`). Search is cosine closeness; a "percent" setting is the bar. Queries live in `adapters/postgres/repositories.py`. The `adapters/pgvector` folder holds only the Knowledge store.

What has an embedding: Day Summaries, Life Threads, Move Outcomes, unmatched Patterns. Memory Items don't: they are picked by category. If embedding fails, the item is still saved, just not found by meaning.

| What | How it is found | Settings (start) |
|---|---|---|
| User Portrait | Always | — |
| Memory Items | "Always include" categories, plus those the Reply Plan names | — |
| Newest Day Summaries | Always | `recent_conversation_summaries` (3) |
| Older Day Summaries | By meaning, on the Understanding's `look_up_past` phrases; the User's own only | `older_summaries_per_reply` (3), `older_summaries_closeness_percent` (68) |
| Life Threads | By a person or thing named, or by meaning, on what the User means plus latest texts. Open first. Stay in mind for the Conversation (`life_threads_in_mind`) | `life_threads_texts_to_search` (8), `life_threads_closeness_percent` (62), `life_threads_per_reply` (10) |
| Unmatched Patterns | Through a linked Thread in mind, or by meaning. Stay in mind (`patterns_in_mind`) | `pattern_closeness_percent` (52), at most 10 (`MOST_PATTERNS_IN_MIND`, in code) |
| Move Outcomes | By meaning, on the latest 3 texts (in code) | `move_outcomes_per_understanding` (3), `move_outcomes_closeness_percent` (65) |
| Due Curiosities | Waiting ones whose "not before" day has come (`CuriosityRaiser.due`) | see `curiosities.py` |
| Shared Photos | All of them, when the Reply Plan picks the group; Photo Viewing must work | — |

Patterns of Pattern Types reach the Reply Plan through `PatternSharing` (one ready to offer, ones already told, ones contested), not through Recall. See `docs/pattern-pipeline/lifecycle.md`.

The Reply Plan picks what the reply uses. `MemoryRetrieval.recall` (`core/memory_retrieval.py`) then writes the memory section for the reply.

**Knowledge is not User Memory.** `KnowledgeRetrieval` (`core/knowledge_retrieval.py`) searches only the documents the Reply Plan chose, through `PgvectorKnowledgeVectorStore`: `knowledge_chunks_per_reply` (3), `knowledge_closeness_percent` (60).

**Past days word for word.** The Reply Plan can call the `past_day` tool (`core/past_day.py`) to read one day's raw messages. It finds none past `message_retention_days`, and then answers from the Day Summary.

## When User Memory is off

Off means **Zeph stops learning but keeps using what it has.** It is a Feature: the User's switch and the Admin's both count, and either one off has the same effect.

Stops:

- Every Conversation-end step except Personal Stickers and Familiarity. No new Memory Items, Day Summaries, Shared Photos, Threads, Observations, Patterns, Curiosities, Move Outcomes or Portrait.
- Onboarding answers are not saved as Memory Items.

Still runs:

- Recall reads everything already saved (`MemoryRetrieval.read`, `ThreadReminder`, `MoveOutcomeFinder`). Waiting Curiosities are still offered.
- Familiarity is still worked out at Conversation end.
- The User can still see and delete everything on the Dashboard.
- A Portrait rewrite after a deletion still runs, since it only forgets.

## The Memories page

`web/src/app/(dashboard)/(user)/memories/page.tsx`, built from `web/src/components/Memories.tsx`. Tabs are in `memoriesTabs` (`web/src/lib/memories.ts`); `?tab=` picks one. Labels are Copy slots `memories.tabs.<tab>`, starting words below.

| Tab (`?tab=`) | Shows | API (`adapters/http/dashboard_api.py`) |
|---|---|---|
| Memories (none) | Memory Items by category, archived ones too. Delete one or all | `GET`, `DELETE /api/memory-items`, `DELETE /api/memory-items/{id}` |
| About you (`about`) | User Portrait. Delete only, no edit | `GET`, `DELETE /api/user-portrait` |
| What's going on (`threads`) | Life Threads, open first. Delete only | `GET /api/life-threads`, `DELETE /api/life-threads/{id}` |
| Patterns (`patterns`) | Only Patterns Zeph told them | `GET /api/patterns`, `DELETE /api/patterns/{id}` |
| What helps you (`helps`) | Move Outcomes | `GET /api/move-outcomes`, `DELETE /api/move-outcomes/{id}` |
| Conversation Summaries (`summaries`) | Day Summaries | `GET /api/day-summaries`, `DELETE /api/day-summaries/{id}` |
| Photos (`photos`) | Shared Photos. The image is fetched from Telegram by `file_id`, never stored by us | `GET /api/shared-photos`, `GET .../{id}/image`, `DELETE .../{id}` |
| Things you said (`quotes`) | Kept quotes (Observations), no Pattern named | `GET /api/kept-quotes`, `DELETE /api/kept-quotes/{id}` |

In chat, the User can also forget one Memory Item or Life Thread (`list_memories`, `forget_memory` in `core/chat_settings.py`).

What a delete does (`UserMemoryService` in `core/user_memory.py`, `PhotoService.delete_shared` in `core/photos.py`):

- Deleting a Memory Item, Day Summary, Life Thread, Pattern or Move Outcome asks for a Portrait rewrite (`request_rewrite`). The scheduler tick (every 60 seconds, `SCHEDULER_INTERVAL_SECONDS` in `main.py`) runs `PortraitWriter.rewrite_requested`. If the rewrite fails or comes back empty, the Portrait is cleared instead.
- Deleting a Life Thread also removes its Observations and its evidence in Patterns, then scores Patterns again.
- Deleting a Pattern or a kept quote scores Patterns again. A record of each deleted quote is kept, without its words (`deleted_quotes`). Details in `docs/pattern-pipeline/lifecycle.md`.
- Deleting the Portrait clears it until a later Conversation end with User Memory working.

## How long it is kept

- **Until the User deletes it.** Nothing in User Memory has an end date.
- **Message Retention doesn't touch it.** `MessageRetention.delete_expired` (`core/message_retention.py`) deletes only messages and Model Call Log entries older than `message_retention_days` (30). Conversations stay, so Observations keep their quotes (ADR 0027).
- **Delete My Data removes all of it**, plus Curiosities, Explorations and hidden Patterns, and makes Familiarity new again (`delete_user_data` in `core/user_data.py`). The account stays. Account Deletion removes the same, plus the account.

## Where to look when changing each part

| To change | Look at |
|---|---|
| Order of Conversation-end steps | `PostConversationProcessor.process`, `core/post_conversation.py` |
| Day Summary, Memory Items, Shared Photos | `DayMemoryWriter`, `core/post_conversation.py`; prompt `memory_processing_prompt` |
| Life Threads | `LifeThreadKeeper`, `ThreadReminder`, `core/life_threads.py`; prompt `life_thread_keeping_prompt` |
| Observations and Patterns | `docs/pattern-pipeline/lifecycle.md` (table at the end) |
| Unmatched Patterns | `PatternKeeper`, `PatternReminder`, `core/patterns.py` |
| Move Outcomes | `MoveOutcomeKeeper`, `MoveOutcomeFinder`, `core/move_outcomes.py` |
| User Portrait | `PortraitWriter`, `core/user_portrait.py`; prompt `portrait_prompt` |
| Curiosities | `CuriosityKeeper`, `CuriosityRaiser`, `core/curiosities.py` |
| Memory section of the reply | `MemoryRetrieval`, `core/memory_retrieval.py` |
| Memory Categories | `MemoryCategoryService`, `core/memory_categories.py` |
| See and delete | `UserMemoryService`, `core/user_memory.py`; routes in `adapters/http/dashboard_api.py` |
| Embeddings and search | `adapters/fastembed/embedder.py`; vector queries in `adapters/postgres/repositories.py` |
| Retention and Delete My Data | `core/message_retention.py`, `core/user_data.py` |
| Settings' starting values | `src/companion/seed/platform_settings.yaml` |

A migration that reloads a seed prompt uses `reload_prompt_unless_edited`. See `src/companion/adapters/postgres/migrations/README.md`.
