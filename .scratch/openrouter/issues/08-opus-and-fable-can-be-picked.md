# 08 — Opus 5.5 and Fable 5.2 can be picked

Status: ready-for-agent
Blocked by: 05

## Parent

`.scratch/openrouter/PRD.md` (user story 1). Asked for by the operator on 2026-11-25, after issue 05.

## What to build

Admins can also pick `anthropic/claude-opus-5.5` and `anthropic/claude-fable-5.2` for any core service in Prompts and models. A migration adds both to the saved `available_models`, and their Model Prices (SGD per million tokens) to `model_prices`, the same way issue 05 added haiku and sonnet. The seed file gets the same additions. Every service stays on DeepSeek after this work.

## Acceptance criteria

- [ ] Migration adds the two models to `available_models` and `model_prices`, keeping everything else (migration test)
- [ ] Seed file matches
- [ ] `/run`: an Admin sets one core service to each of the two models in turn, a message is sent, the reply arrives, and the Model Call Log and OpenRouter's record show that model, paid with our own key; then set it back
- [ ] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 05

## Comments
