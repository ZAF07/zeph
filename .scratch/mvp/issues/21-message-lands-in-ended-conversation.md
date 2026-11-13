# 21 — A message can land in a Conversation that was just ended

Status: needs-triage

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

- [ ] A message arriving at the quiet-gap boundary always ends up in a Conversation whose processing includes it
- [ ] A test covers the fixed behaviour
- [ ] `make check` passes (pytest, ruff, ruff format, mypy, plus the web checks)
