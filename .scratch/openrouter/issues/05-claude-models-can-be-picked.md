# 05 — Claude models can be picked

Status: ready-for-agent
Blocked by: 02

## Parent

`.scratch/openrouter/PRD.md` (user story 1).

## What to build

Admins can pick a Claude model for any core service in Prompts and models. A migration adds at least one Claude model (OpenRouter name) to the saved `available_models`, and its Model Price (SGD per million tokens) to `model_prices`. The seed only adds missing keys, so the seed file alone won't reach existing installs. The seed file gets the same additions. Every service stays on DeepSeek after this work.

## Acceptance criteria

- [ ] Migration adds the Claude model to `available_models` and `model_prices`, keeping everything else (migration test)
- [ ] Seed file matches
- [ ] Contract test (remind the operator first): a Claude reply with thinking on returns reasoning text
- [ ] `/run`: an Admin sets one core service to the Claude model, a message is sent, the reply arrives, and the Model Call Log and OpenRouter activity page show the Claude model; then set it back
- [ ] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 02

## Comments
