# 02 — Replies run in a core ReplyService; LangGraph removed

Status: ready-for-agent

## Parent

`.scratch/understanding/PRD.md`

## What to build

Prefactor for Understanding (ADR-0009). Move the reply step (check → recall memory → recall Knowledge → compose → deliver) out of the LangGraph adapter into a core `ReplyService` in plain Python, with the same order and behaviour. Remove the conversation-engine port, the LangGraph adapter, the Postgres checkpointer and its tables, and the LangGraph/LangChain-graph dependencies no longer used. The ReplyGate keeps the house rules; on a confirmed Delete My Data nothing graph-related is left to delete.

Pure refactor: no change in what Users get, including failures raising as today.

## Acceptance criteria

- [ ] `ReplyService` in core runs the reply steps; nothing in core imports LangGraph
- [ ] The LangGraph adapter, the checkpointer and its tables are gone (migration drops them); unused dependencies removed
- [ ] Existing end-to-end tests pass with no logic changes (only wiring or fixture changes, e.g. no checkpointer fixture)
- [ ] `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [ ] `/run` in a worktree: a normal, a crisis and an over-limit message each get the right reply

## Blocked by

None - can start immediately.
