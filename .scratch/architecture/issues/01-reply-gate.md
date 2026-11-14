# 01 — Move the house rules of a message into a core ReplyGate

Status: ready-for-agent

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

- [ ] `ReplyGate.check` holds the house rules and their order in plain Python, in core; the graph has no `after_safeguard` / `after_data_deletion` / `after_message_limit` logic left
- [ ] Unit tests for `ReplyGate.check` with fakes, one per path: crisis (Crisis Reply sent, deletion cancelled, nothing counted), confirmed deletion, pending deletion plus a normal message (`data_deletion_cancelled=True`), over the limit (Limit Reply sent), normal message
- [ ] Existing end-to-end tests pass unchanged
- [ ] `pytest`, `ruff`, `ruff format --check` and `mypy` pass
- [ ] `/run` in a worktree: a normal message, a crisis message and an over-limit message posted to the webhook each get the right reply

## Blocked by

None.
