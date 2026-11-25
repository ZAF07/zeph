# 07 — Thinking switch only when the model can think

Status: ready-for-agent
Blocked by: 04

## Parent

`.scratch/openrouter/PRD.md` (user story 5). Asked for by the operator on 2026-11-24, during issue 04.

## What to build

In Prompts and models, the model and the thinking switch stay two separate choices for each core service. An Admin picks any model in the list (DeepSeek flash or pro, a Claude model, others later) and, apart from that, sets thinking on or off. The thinking switch can only be used when the chosen model can think. For a model that can't, the switch is shown off and can't be turned on, and the call is made with thinking off.

Every model in the list today (DeepSeek flash and pro, Claude) can think, so nothing is wrong until a model that can't is added.

## Open questions

- Where "can this model think" comes from: kept by Admins beside the model list, or read from OpenRouter's model list (`supported_parameters` holds `reasoning`).
- What happens to a service whose thinking is on when its model is changed to one that can't think: thinking is saved as off, or kept and ignored.

## Acceptance criteria

- [ ] An Admin can't turn thinking on for a model that can't think (Dashboard and API, tests)
- [ ] A call for a model that can't think is made with thinking off (test)
- [ ] Models that can think behave as today
- [ ] `/run`: the switch is usable for a model that can think and not for one that can't
- [ ] The language's checks pass

## Blocked by

- 04

## Comments

- 2026-11-25, operator's answers to the open questions:
  - "Can this model think" comes from a Platform Setting list of models that can't think (`models_that_cannot_think`), kept beside `available_models` and filled by the seed or a migration. Empty today. Not read from OpenRouter.
  - A service with thinking on whose model is changed to one that can't think gets its thinking saved as off.
- 2026-11-25, in progress on branch `openrouter-07-thinking-switch` (worktree `ai-chat-companion-openrouter-07`).
