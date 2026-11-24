# 06 — Prompt caching for Claude

Status: ready-for-agent
Blocked by: 05

## Parent

`.scratch/openrouter/PRD.md` (user stories 19, 20).

## What to build

Calls to Claude models through OpenRouter mark the system instructions with `cache_control`, so long repeated prompts are cached. DeepSeek models get no marker. The adapter reads the cached-token count from the reply's usage and logs it, so caching can be checked. Bug reports in other libraries show markers being dropped on the OpenAI-format path, so the contract test must prove real cache hits.

## Acceptance criteria

- [ ] Adapter tests: Claude models get `cache_control` on the system instructions; DeepSeek models don't; cached tokens are read from usage and logged
- [ ] Contract test (remind the operator first): two Claude calls with the same long instructions; the second shows cached tokens
- [ ] `/run`: with a core service on Claude, two messages in a row show cached tokens in the logs
- [ ] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 05

## Comments
