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

- 2026-11-25, status (branch `openrouter-08-opus-and-fable`, commit ec20517, not merged): migration `0092_opus_and_fable_can_be_picked.py`, seed and tests are written, and the affected tests pass. Prices: opus 5.12 in / 25.6 out, fable 10.24 in / 51.2 out (USD 4/20 and 8/40 at 1.28). The operator asked for a quick check only, not a full `/run`.
- 2026-11-25, **blocker found by the quick check.** One real call to each model through `OpenRouterChatModel`:
  - thinking on: both reply, `is_byok: true`.
  - thinking off: both fail with 400 "Reasoning is mandatory for this endpoint and cannot be disabled." The adapter sends `reasoning: {enabled: false}`; `effort: "none"` fails the same way. Leaving the `reasoning` field out, or `effort: "low"`, works (the model then thinks a little when it needs to).
  - So a service with thinking off (Response composition, Photo viewing, Knowledge "when it helps", Personal Sticker keeping today) would fail on every call if an Admin picked Opus 5.5 or Fable 5.2 for it. Haiku 5.5 and Sonnet 5.5 accept thinking off.
  - Waiting on the operator: how thinking off should be handled for a model that must think (related to issue 07, which covers the opposite case). Not merged until decided.
