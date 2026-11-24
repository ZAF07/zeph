# 03 — Tool calls through OpenRouter

Status: ready-for-agent
Blocked by: 02

## Parent

`.scratch/openrouter/PRD.md` (user stories 16, 24).

## What to build

The OpenRouter adapter runs tool calls the way the DeepSeek adapter does today. Tools go out in the OpenAI function format. The loop allows at most 4 rounds, and a call with arguments that aren't valid JSON goes back as an error the model can retry. A final call then goes out with tools turned off. Tokens are summed across rounds, and every tool call is recorded. When a Claude model thinks while calling tools, the assistant message sent back each round keeps the reasoning details OpenRouter returned, because Anthropic needs them for the next round. Reuse the existing tool loop rather than copying it, if that stays simple.

## Acceptance criteria

- [ ] Adapter tests: tools sent in function format; tool results sent back; broken JSON goes back as an error; last round forced to no tools; tokens summed; reasoning details kept on the assistant message for the next round
- [ ] Contract test (remind the operator first): a tool call round-trip through OpenRouter
- [ ] `/run`: a message that triggers a tool (e.g. a web search or Settings in Chat) gets a proper reply, and the Model Call Log shows the tool call
- [ ] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 02

## Comments
