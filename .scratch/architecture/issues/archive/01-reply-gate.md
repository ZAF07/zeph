# 01 — Move the house rules of a message into a core ReplyGate

Status: completed

## Parent

Architecture review, 14 Nov 2026, point 1 ("Move the turn policy into one core module"). Decided in a `/grill-with-docs` session.

## Why

The order "Safeguard first, a crisis isn't counted, a confirmed Delete My Data stops the reply, over the Daily Message Limit stops the reply" exists only as LangGraph edges in `src/companion/adapters/langgraph/conversation_engine.py` (`after_safeguard`, `after_data_deletion`, `after_message_limit`). ADR-0003 says business logic lives in core services, never in the graph. The code has drifted from it.

## What to build

A core module `src/companion/core/reply_gate.py` with `ReplyGate.check(message)`. It saves the incoming message, then applies the house rules in order:

1. Safeguard. On a crisis: send the Crisis Reply, then cancel any pending Delete My Data, and return `Stopped(CRISIS)`. The message isn't counted toward the Daily Message Limit.
2. Delete My Data. A confirming message returns `Stopped(DATA_DELETED)`; any other message cancels a pending request.
3. Daily Message Limit. Over the limit: send the Limit Reply and return `Stopped(OVER_LIMIT)`.
4. Otherwise return `ReplyNeeded(conversation_id, data_deletion_cancelled)`.

The LangGraph adapter keeps the reply step only: `check → (ReplyNeeded?) → recall memory → recall Knowledge → compose → deliver`. Its edge only looks at which result came back. On `Stopped(DATA_DELETED)` the engine still deletes the User's checkpoint thread. `TurnState`, renamed `ReplyState`, shrinks to the reply step's fields.

## Decisions

- Names: `ReplyGate`, `check`, `Stopped(reason)` with reason `CRISIS | DATA_DELETED | OVER_LIMIT`, and `ReplyNeeded`. "Turn" / "TurnService" / `turn` were rejected as not intuitive; the parameter is `message`.
- Renames in the same change: `ConversationTurn` → `MessageToAnswer` (so `ReplyGate.check(message: MessageToAnswer)`) and the graph's `TurnState` → `ReplyState`.
- Line between core and graph: core owns the house rules; the reply step (recall → compose → deliver) stays in the graph, because the planned Understanding feature (`.scratch/understanding/`) will reshape it.
- LangGraph stays for now. Whether to remove it is decided after Understanding is designed. Removing it today would cost nothing we use (checkpoints carry nothing between messages), but it might be the right tool for an Understanding reasoning loop.
- Pure refactor: no change in behaviour, including the Crisis Reply being sent before the deletion is cancelled, and failures throwing as they do today.
- No ADR (this brings the code back in line with ADR-0003) and no `CONTEXT.md` change (every rule already has a glossary term).

## Acceptance criteria

- [x] `ReplyGate.check` holds the house rules and their order in plain Python, in core; the graph has no `after_safeguard` / `after_data_deletion` / `after_message_limit` logic left
- [x] Unit tests for `ReplyGate.check` with fakes, one per path: crisis (Crisis Reply sent, deletion cancelled, nothing counted), confirmed deletion, pending deletion plus a normal message (`data_deletion_cancelled=True`), over the limit (Limit Reply sent), normal message
- [x] Existing end-to-end tests pass unchanged
- [x] `pytest`, `ruff`, `ruff format --check` and `mypy` pass
- [x] `/run` in a worktree: a normal message, a crisis message and an over-limit message posted to the webhook each get the right reply

## Blocked by

None.

## Comments

- Built test-first: `tests/test_reply_gate.py` was red (no `MessageToAnswer` / `reply_gate`) before `src/companion/core/reply_gate.py` existed, then 5/5 green.
- `ReplyGate` holds the house rules in core (`src/companion/core/reply_gate.py`). The graph is now `check → (stop_reason == ""?) → recall_memory → recall_knowledge → compose_reply → deliver_reply`. `after_check` only looks at `stop_reason`. `handle` deletes the checkpoint thread on `StopReason.DATA_DELETED`. `ReplyState` drops `risk_type`, `data_deletion_answer` and `within_message_limit`, and adds `stop_reason` and `data_deletion_cancelled`.
- `ConversationServices` now holds `reply_gate` instead of `safeguard`, `usage_limiter` and `data_deletion`. It moved to its own module, `src/companion/core/conversation_services.py`, because `reply_gate.py` imports `conversations.py` (it would have been a circular import). The only changes to existing tests are this import path and the `ConversationTurn → MessageToAnswer` / `turn → message` rename in `tests/conftest.py`, `evals/conftest.py` and `tests/fakes.py`. No test logic changed.
- Also renamed in `IncomingMessageHandler`: `_turn_for` → `_message_to_answer`, `_photo_turn` → `_photo_message_to_answer`, `build_turn` → `build_message`. The per-User `_turn_lock` names were left alone, because they are about message ordering, not the type.
- Checks: `ruff check` and `ruff format --check` pass, `mypy` reports "no issues found in 98 source files", and `pytest` has 602 passed (9 deselected evals).
- `/run` (worktree stack on ports 8100/5532, real DeepSeek, migrated and seeded DB). The real app (`build_production_app`) was driven by posting to `/telegram/webhook`, with only the chat channel swapped for one that records, because Telegram can't deliver to a fake chat. Run for a fresh connected User, before and after the review fixes:
  - Normal message ("hey, I just got back from a long walk by the river"): got a composed reply ("That sounds like a good reset. What's the river like this time of year…"). Message count 0 → 1.
  - Over the limit (count set to the limit of 200, then "what should I cook tonight?"): got the Admin-set Limit Reply ("I'm honestly wiped for today, my brain needs a rest. Talk tomorrow?…"). Count stayed 200.
  - Crisis ("I can't do this anymore, I want to end my life tonight"): got the Crisis Reply with SG Helplines (SOS 1767, IMH, 995). One `suicide_or_self_harm` Safeguard Event was recorded. Not counted (count stayed 200).
  - Seen along the way (existing behaviour, not changed here): a normal message straight after a crisis message also gets the Crisis Reply, because the Safeguard reads the whole Conversation.
- Code review (`/code-review`, Standards and Spec in parallel). Spec found no change in behaviour: same calls, same order, same values, same thread deletion, failures still raise. Fixed: full Google-style docstrings on the test fakes, `ConversationServices` moved out of `reply_gate.py`, the empty Safeguard text becomes None in one place only (the adapter), and the confirmed-deletion test checks the full call order. Not changed: the graph node keeps the name `check`, as this issue names it. `stop_reason` uses "" for "reply needed", because checkpoint state must stay plain data. `ReplyGate` takes the concrete core services, as the old graph did.
- Old checkpoint threads, checked after merge with a `make db-copy` of the main database into the worktree. The main User's thread (1,465 checkpoints) still had the `TurnState` keys (`risk_type: none`, `data_deletion_answer: nothing_asked`, `within_message_limit: true`). That User was reconnected with a fake Telegram id and sent a normal message through the real app (`/telegram/webhook`, real DeepSeek, recording chat channel). The reply came through normally and used their User Memory, with no "reply failed" message. The newest checkpoint then had `stop_reason: ""` and `data_deletion_cancelled: false`, and the old keys were gone. The copied database was deleted afterwards with `make worktree-teardown`.

## Completion

- Completed: 2026-11-14
- Commit: f1a1709 "Move the house rules of a message into a core ReplyGate", review fixes c550222 "Give ConversationServices its own module; full docstrings on ReplyGate test fakes", archive cf9c8aa "Architecture issue 01 done: archive issue with test, run and review evidence" (merged from `arch-01-reply-gate` in 0f11f29 "Merge architecture issue 01: the house rules of a message move out of the LangGraph edges into a core ReplyGate.check that returns Stopped(reason) or ReplyNeeded; the graph keeps only the reply step; ConversationTurn is renamed MessageToAnswer and TurnState ReplyState")
