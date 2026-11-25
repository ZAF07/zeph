# 11 — Thinking switch locked on for a model that always thinks

Status: ready-for-agent
Type: bug

## Parent

`.scratch/openrouter/PRD.md` (user story 5). Found on 2026-11-25, during the `/run` of issue 09. Widened by the operator on 2026-11-25 to cover the Dashboard.

## What happens

With a core service on `anthropic/claude-sonnet-5.5` and its thinking switch off, every call fails. OpenRouter answers 400: "Reasoning is mandatory for this endpoint and cannot be disabled." For the Reply (thinking is off by default) the User gets the "my thoughts got tangled" text instead of a reply.

With thinking on, the same call works.

Opus 5.5 and Fable 5.2 always think too. Issue 08 made their calls work by leaving the off instruction out in the adapter, but the Dashboard still shows a free switch, and "off" quietly does nothing for them.

## How to see it

Set `response_model` to `anthropic/claude-sonnet-5.5`, leave `response_thinking` off, and send a message. Or send one request with `reasoning: {enabled: false}` to that model.

## Cause

The model always thinks and refuses to be told not to. The adapter leaves the `reasoning` field out only for the names in `MODELS_THAT_ALWAYS_THINK` (`adapters/openrouter/chat_model.py`), and Sonnet 5.5 is not in it. Issue 08 said Sonnet accepts thinking off, but Sonnet was never called with thinking off until the issue 09 `/run`.

## What to build

The same as issues 07 and 10 did for a model that can't think, in reverse (operator's decision, 2026-11-25):

- A Platform Setting list of models that always think, kept beside `models_that_cannot_think`. A migration and the seed fill it with Sonnet 5.5, Opus 5.5 and Fable 5.2.
- In Prompts and models, the thinking switch for such a model is shown on and can't be turned off. Holding the mouse over it shows a pop-up saying why, like the "can't think" one. A screen reader is told the same.
- A service whose thinking is off when its model is changed to one that always thinks gets thinking saved as on. The API refuses to turn it off.
- A call for such a model is never told thinking is off, whatever is saved.
- The page at rest looks the same as today, so the design reference does not change.

## Acceptance criteria

- [ ] A test that is red before the fix: a Sonnet 5.5 call with thinking off sends no `reasoning: {enabled: false}`
- [ ] An Admin can't turn thinking off for a model that always thinks (Dashboard and API, tests)
- [ ] Changing a service's model to one that always thinks saves its thinking as on (test)
- [ ] Holding the mouse over the locked-on switch shows a pop-up saying the model always thinks; a screen reader is told the same (test)
- [ ] A model that can think or not, and one that can't think, behave as today
- [ ] Migration and seed list Sonnet 5.5, Opus 5.5 and Fable 5.2 as models that always think (migration test)
- [ ] `/run`: the Reply on Sonnet 5.5 gets a reply; the switch is locked on with the pop-up in the browser at 1280 and 390; `AdminPrompts` still passes the pixel test
- [ ] Check Haiku 5.5 with thinking off still works (it did in the issue 09 `/run`)
- [ ] ADR-0028 and the deployment guide name Sonnet with Opus and Fable, and say the switch is locked on
- [ ] The language's checks pass

## Open question for the implementer

- The adapter holds its own list (`MODELS_THAT_ALWAYS_THINK`). Decide whether the new Platform Setting replaces it or the service simply always passes thinking on for these models, so there is one list, not two.

## Comments

- 2026-11-25, operator: do the same as for models that can't think, in reverse. The switch defaults to on, is locked, and a hover pop-up says why.
