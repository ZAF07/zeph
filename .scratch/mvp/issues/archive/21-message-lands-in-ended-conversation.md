# 21 — A message can land in a Conversation that was just ended

Status: completed

## Parent

`.scratch/mvp/PRD.md` (found while closing out `issues/archive/06-user-memory.md`)

## Symptom

Every 60 seconds the scheduler ends Conversations that have passed the quiet gap. Then it processes them: it writes the Summary and mood and updates the Memory Items.

When a User message arrives, the backend does two separate steps:

1. It looks up the User's open Conversation.
2. It saves the message into that Conversation.

Nothing stops the tick from running between those two steps. If it does, the message is saved into a Conversation that is already ended, and maybe already processed.

- **Expected:** the message joins an open Conversation, or starts a new one. Either way, its Conversation's Summary and Memory Items include it.
- **Actual:** the message is saved and the User still gets a reply. But that message (and the reply to it) may be left out of the Summary and Memory Items. Later messages start a new Conversation, because an ended Conversation is never reused.

There is no crash and no error log. The only effect is missing memory.

## Repro

Not deterministic. It can only happen when a message arrives right as its Conversation's quiet gap runs out, at the same moment as a scheduler tick. It has not been seen in the running app. Found by reading the code.

To force it in a test: have the tick end and process the Conversation after `_open_conversation_id` returns but before the message is saved.

## Suspected location

- `src/companion/core/conversations.py`: `record_incoming` calls `_open_conversation_id` and then `_save`, with no lock or check in between.
- `src/companion/adapters/postgres/repositories.py`: `end_quiet` (the tick's update).

## Acceptance criteria

- [x] A message arriving at the quiet-gap boundary always ends up in a Conversation whose processing includes it
- [x] A test covers the fixed behaviour
- [x] `make check` passes (pytest, ruff, ruff format, mypy, plus the web checks)

## Comments

### 2026-11-13 — fix (branch `mvp-21-message-lands-in-ended-conversation`)

- New port method `ConversationRepository.add_message_if_open`. The Postgres version first updates the Conversation's `last_message_at` only `WHERE ended_at IS NULL` (this locks the row), then inserts the message, in one transaction. If `end_quiet` runs at the same time, either it waits and then sees the fresh message (so it doesn't end the Conversation), or it ends it first and the message is refused.
- `ConversationService.record_incoming` uses it. If the message is refused, it looks again; the ended Conversation is no longer open, so a new one is started, and a brand-new Conversation can't already be ended.
- Replies, the Crisis Reply, the daily limit reply and the Check-in message still use `add_message`, unchanged.

### 2026-11-13 — evidence

- Checks (`make check`): ruff, ruff format, mypy pass; pytest 452 passed; web lint, prettier, typecheck pass; vitest 298 passed.
- Test `tests/test_post_conversation.py::test_a_message_caught_by_the_tick_joins_a_new_conversation`: the tick runs right after the open Conversation is looked up and before the message is saved. It fails without the fix (only one Conversation is processed; the message is in the already-processed one) and passes with it (the message and its reply are in the second Conversation's processing and Summary).
- `/run` (own stack `mvp21` on ports 5443/8011, no ngrok, so the main stack and the other agent's stack were left alone; real DeepSeek; real Telegram replies to the owner's chat):
  - Sent "long day at work today" to the webhook: Conversation A saved it and the reply.
  - In psql, ended A in a transaction and held it 20 s. Sent "my boss yelled at me in front of everyone" meanwhile. While held, the message was not saved and its `UPDATE conversations` waited on a lock (`pg_stat_activity`). On commit (10:41:43.554) the message was refused and started a new Conversation B at 10:41:43.564; both reply parts were saved in B.
  - The next tick processed A: Summary "They mentioned having a long day at work, and the companion asked what made it long." (no boss).
  - Moved B's times back 61 minutes; the tick ended and processed B: Summary "They shared that their boss yelled at them in front of everyone…", and the Memory Item "Their boss once yelled at them in front of everyone at work, which stung." came from B.
  - No errors in the backend logs. The `mvp21` stack and its database were removed.

### Review

- Standards: no hard breaks. Took the suggestions: use `.returning(...).first()` like the other bool-returning methods in the file; say in the docstring why the retry loop always ends; the test patch now ticks once with a flag instead of undoing itself.
- Spec: the first version made `add_message` refuse ended Conversations for every message, so a late reply would have been dropped silently. Fixed by keeping `add_message` as it was and adding `add_message_if_open` just for incoming messages.

### Decisions

- Only the incoming User message is checked. A reply goes to the Conversation its message joined a moment ago, which can't pass the quiet gap that fast; if it ever did, saving it there (as before) beats losing it from history.
- No retry limit on the loop: the second try always starts a new Conversation, which can't already be ended.

## Completion

- Completed: 2026-11-13
- Commit: 8a351c0 "Never save a User message into a Conversation that was just ended", archive and glossary d6200cb "MVP issue 21 done: archive issue with test, run and review evidence" (merged from `mvp-21-message-lands-in-ended-conversation` in a511f9c "Merge MVP issue 21: a User message arriving just as the scheduler ends its Conversation now starts a new Conversation…")
