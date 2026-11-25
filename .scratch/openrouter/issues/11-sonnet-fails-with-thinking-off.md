# 11 — Sonnet 5.5 fails with thinking off

Status: needs-triage
Type: bug

## Parent

`.scratch/openrouter/PRD.md`. Found on 2026-11-25, during the `/run` of issue 09.

## What happens

With a core service on `anthropic/claude-sonnet-5.5` and its thinking switch off, every call fails. OpenRouter answers 400: "Reasoning is mandatory for this endpoint and cannot be disabled." For the Reply (thinking is off by default) the User gets the "my thoughts got tangled" text instead of a reply.

With thinking on, the same call works.

## How to see it

Set `response_model` to `anthropic/claude-sonnet-5.5`, leave `response_thinking` off, and send a message. Or send one request with `reasoning: {enabled: false}` to that model.

## Likely cause

Same as Opus 5.5 and Fable 5.2 in issue 08: the model always thinks and refuses to be told not to. The adapter leaves the `reasoning` field out only for the names in `MODELS_THAT_ALWAYS_THINK` (`adapters/openrouter/chat_model.py`), and Sonnet 5.5 is not in it. Not confirmed by a fix yet.

## Acceptance criteria

- [ ] A test that is red before the fix: a Sonnet 5.5 call with thinking off sends no `reasoning: {enabled: false}`
- [ ] `/run`: the Reply on Sonnet 5.5 with thinking off gets a reply
- [ ] Check Haiku 5.5 with thinking off still works (it did in the issue 09 `/run`)
- [ ] ADR-0028 and the deployment guide name Sonnet with Opus and Fable
- [ ] The language's checks pass

## Comments
