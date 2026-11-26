# Privacy and User data: the rules

Zeph has real Users in production. These are the rules you must not break, and where code keeps them. Terms are as in `CONTEXT.md`.

## What counts as a User's data

Anything that came from a User, or that Zeph wrote about them:

| Data | Table(s) |
|---|---|
| Messages (text, photos, stickers, replied-to text) | `conversation_messages`, under `conversations` |
| User Memory: Memory Items, Day Summaries, Shared Photos | `memory_items`, `day_summaries`, `shared_photos` |
| User Memory: Life Threads, Patterns, Observations (the User's quotes), Move Outcomes, User Portrait | `life_threads`, `patterns`, `observations`, `move_outcomes`, `user_portraits` |
| What Zeph keeps that the User doesn't see: Understandings, Reply Plans, Curiosities, Explorations, Predictions | `understandings`, `reply_plans`, `curiosities`, `explorations`, `predictions` |
| Model Call Log entries (content, for Admins' own chats) | `model_calls` |
| Personal Stickers, Check-in history, Telegram Connection | `personal_stickers`, `check_ins`, `telegram_connections` |
| Profile and settings (name, onboarding answers, switches) | `users` |

Treat all of it as private. Admins never see a User's words.

## Delete My Data and Account Deletion

Code: `src/companion/core/user_data.py`.

| | Delete My Data | Account Deletion |
|---|---|---|
| Where | Dashboard (`DELETE /api/me/data`) or chat (`ChatDataDeletion`, confirmed by the confirmation word sent alone) | Dashboard only (`DELETE /api/me`) |
| Function | `delete_user_data` (from `UserDataService.delete_data` or `ChatDataDeletion.settle`) | `UserDataService.delete_account` → `_delete_user` |
| Removes | Conversations and messages, Model Call Log, Memory Items, Day Summaries, Shared Photos, Life Threads, Observations, deleted-quote records, Pattern exclusion flags, Patterns (hidden too), the Pattern log, "never again" marks, Move Outcomes, Curiosities, Explorations and their tries, User Portrait, Personal Stickers, Check-ins, Connection Tokens, Telegram Connection | All of that, plus Usage, Safeguard Events, the Admins' Feature Switches for them, the `users` row and the auth account |
| Keeps | The `users` row (profile, settings), Usage, Safeguard Events, Feature Switches. Familiarity goes back to new. | Nothing |

How it works:

- `delete_user_data` calls `delete_for_user(user_id)` on each repository, in one transaction.
- Each `delete_for_user` is on a port in `src/companion/core/ports.py` and built in `src/companion/adapters/postgres/repositories.py`.
- Tables with no `delete_for_user` of their own go through `ON DELETE CASCADE` foreign keys. Understandings, Reply Plans, `patterns_in_mind` and `life_threads_in_mind` go with their Conversation. Predictions, `pattern_reactions` and `pattern_evidence` go with their Pattern.
- In chat, the "deleted" reply is sent but not saved, so nothing of theirs is left.
- If the auth provider fails, the account stays on `pending_auth_account_deletions`. `ScheduledWork.tick` calls `delete_pending_auth_accounts` to try again. The User's data is gone either way.
- The last Admin can't delete their account (`refuse_if_last_admin`).

### Adding a table that holds a User's data

Every new table with a User's data **must** be removed by these. Do this:

1. Give it a `user_id` column: `ForeignKey("users.id", ondelete="CASCADE")`, in the migration and in `src/companion/adapters/postgres/tables.py`.
2. Add `delete_for_user` to its port in `ports.py` and to its Postgres repository.
3. Call it in `delete_user_data`. If Delete My Data should keep it (rare: today only Usage, Safeguard Events and Feature Switches), call it in `_delete_user` instead.
4. In `tests/test_data_deletion.py`, add a row for it in `set_up_user_with_every_kind_of_data`. If Delete My Data keeps it, add it to `TABLES_KEPT_BY_DELETE_MY_DATA`.

The test finds every table with a `user_id` column by itself (`tables_with_a_user_id_column`). It fails if any such table has no test data, or still has rows after Delete My Data. A table with no `user_id` column is not checked, so it relies on its cascade alone. Give it a `user_id` column.

The cascade on `users.id` alone is not enough: Delete My Data keeps the `users` row, so nothing cascades.

## User Memory on or off

User Memory works only when the User's own switch (`user_memory_enabled`) and the Admins' Feature switch are both on. Code asks `snapshot.works(Feature.USER_MEMORY)`.

| When off | |
|---|---|
| Stops | Conversation-end learning in `PostConversationProcessor.process` (`src/companion/core/post_conversation.py`): Day Summaries, Life Threads, Observations, Patterns, Curiosities, Move Outcomes, the User Portrait. Personal Stickers (their own Feature) and Familiarity are still kept. Onboarding answers aren't saved as Memory Items (`remember_onboarding` in `src/companion/core/user_memory.py`). |
| Goes on | Zeph still uses what it already has. Nothing is deleted. The User can still see and delete their memories. A deleted memory still rewrites the Portrait without it. |

Observations also need Pattern noticing on and the User's "Got it" on the notice (`may_keep_observations` in `src/companion/core/observations.py`, which checks `pattern_noticing_told_at`).

## Message Retention

- Setting: `message_retention_days` (Platform Setting, 1 to 365, seed 30 in `src/companion/seed/platform_settings.yaml`).
- Code: `MessageRetention.delete_expired` in `src/companion/core/message_retention.py`, run on every `ScheduledWork.tick`.

| Deletes | Keeps |
|---|---|
| Messages sent before the cutoff (`delete_messages_sent_before`) | Conversations (the rows) |
| Model Call Log entries started before the cutoff | Day Summaries, Memory Items, Life Threads, Shared Photos, Observations (with quotes), Patterns, Personal Stickers |
| Understandings and Reply Plans (cascade from their message) | |

Why quotes outlive it: ADR 0027. An Observation keeps its own short quote, never the whole message. Rule of thumb for a new table that copies a User's words: delete it with messages (FK to `conversation_messages` with `ON DELETE CASCADE`), or, like quotes, let the User see and delete it, and tell them.

## What Admins can and can't see

Admins see counts and shapes, never words.

| Admin view | Holds |
|---|---|
| Users list (`UserOverview` in `src/companion/core/models.py`) | Name, email, role, sign-up date, Familiarity. Counts: Conversations, messages, Life Threads, Move Outcomes, kept quotes, Patterns per state; whether they have a Portrait or Telegram |
| Usage | Counts only |
| Check-in Log | Decisions, never message text |
| Safeguard Events | Who, when, risk type, Helpline country, never message text |
| Model Call Log | See below |

### The Model Call Log rule (ADR 0010)

Code: `ModelCallLog` in `src/companion/core/model_call_log.py`.

- Every call keeps: step, model, thinking, tokens, time, the error's type name (never its message), and tool names.
- Some steps also keep a shape, never words: `record_understanding_shape`, `record_reply_plan_shape`, `record_check_in_shape`, `record_tagging_shape`.
- Full content (instructions, history, tools, tool calls, answer, reasoning) is saved only when `_keeps_content` says so: the User is an Admin, or `content_for_everyone` is on (Eval runs only).
- The rule is by who the User is, not by step. Every step of a plain User's call saves no content.
- `MODEL_CALL_DEVELOPER_LOGS=true` writes full content to the developer logs, for local and worktree runs. It is off by default and must stay off in production.

To debug a real User's bad reply, reproduce it in an Admin's own chat or an Eval. Don't read theirs. Tests: `tests/test_model_call_log.py`.

## Users are told plainly

Users are told what is kept, in Copy (`src/companion/seed/copy.yaml`):

| Copy key | Says |
|---|---|
| `shared.pattern_noticing.*` | "Zeph now keeps some of your words." Quotes stay after messages are deleted. Nothing is kept until they press Got it. |
| `account.delete_data.retention_one` / `_many` | Messages are otherwise kept for {count} days. |
| `account.delete_data.kept_quotes` | Quotes Zeph keeps as evidence stay until you delete them. |
| `account.delete_data.description` | What Delete My Data removes, private notes too. |
| `shared.memory_off.*` | With memory off nothing is deleted, Zeph won't learn anything new, and Delete My Data removes everything. |

If you change what is kept, change what Users are told.

## Safeguards

The Safeguard (`src/companion/core/safeguard.py`) checks every message for crisis, read with the Conversation before it. On a crisis, `respond_to_crisis` sends the Crisis Reply with Helplines (`src/companion/core/helplines.py`) and records a **Safeguard Event**: who, when, risk type, which country's Helplines. It never holds the message text. Delete My Data keeps it; Account Deletion removes it. The ready gate uses it: no Pattern is ready after a recent Safeguard Event.

## Worktrees and test data

- `make db-copy` copies the main stack's database into a worktree's, then deletes every `telegram_connections` row, so its Check-ins never reach real Users.
- Never paste a real User's words into eval cases, tests or seeds. Write a made-up version with made-up names (`docs/pattern-evals/adding-tagging-cases.md`).

## Before you merge a change that touches User data

- [ ] A new table with User data has a `user_id` column with `ON DELETE CASCADE`.
- [ ] Its `delete_for_user` is called from `delete_user_data` (or `_delete_user`).
- [ ] `tests/test_data_deletion.py` has a row for it and passes.
- [ ] You decided if Message Retention deletes it. Rule of thumb: if it keeps the User's words past retention, the User can see and delete it and is told.
- [ ] If it is User Memory, it isn't learned while User Memory doesn't work for the User.
- [ ] Admin views show counts or shapes, never words. No new Model Call Log field holds words.
- [ ] Rule of thumb: errors and logs don't print a User's words.
- [ ] User-facing Copy still says plainly what is kept.
- [ ] Test and eval data is made up.
