# 02 — Replies go through OpenRouter

Status: ready-for-agent
Blocked by: 01

## Parent

`.scratch/openrouter/PRD.md` (user stories 3, 4, 5, 6, 7, 8, 17, 18, 21, 22, 23, 25, 26, 27).

## What to build

A new OpenRouter adapter behind the `ChatModel` port, built on plain `httpx` (not LangChain) against OpenRouter's Chat Completions API, taking an optional HTTP client like the Tavily adapter. It sends the model name exactly as read from Platform Settings, maps the `thinking` flag to `reasoning: {enabled: true|false}`, and returns the reply text, tokens in and out, and the reasoning text from the reply's `reasoning` field. Tools are not part of this slice. When a call asks for tools, the adapter refuses clearly until 03 lands. `OPENROUTER_API_KEY` is read through config, and `CHAT_MODEL_ADAPTER` gains `openrouter`. The default stays `deepseek` until 04, so shipping this slice never breaks tool or photo replies for real Users. A missing key fails at startup. Add an ADR "Model calls go through OpenRouter, direct DeepSeek kept as backup" (updating ADR 0003's adapter list), and fix the Model Price entry in `CONTEXT.md`. Record the manual OpenRouter step: set "Shared capacity fallback" to "Never use any other provider or key for this key's models" on each BYOK key.

## Acceptance criteria

- [ ] Adapter tests with `httpx.MockTransport`: model name sent as given; thinking on/off maps to `reasoning`; reasoning text returned; tokens recorded; an HTTP error is handled as today
- [ ] `openrouter` builds the OpenRouter adapter, `deepseek` still builds the direct one and stays the default; a missing key fails at startup (tests)
- [ ] Contract tests (remind the operator first; costs money): a DeepSeek reply; a reply with thinking on that returns reasoning text
- [ ] ADR added; `CONTEXT.md` Model Price entry updated; manual BYOK fallback step written down
- [ ] `/run` with `CHAT_MODEL_ADAPTER=openrouter`: an Admin changes a core service's model in Prompts and models, a message is sent, and both the Model Call Log and the OpenRouter activity page show the new model
- [ ] `/run`: with thinking on, the reasoning shows in the Model Call Log
- [ ] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 01

## Comments

- 2026-11-24, in progress (branch `openrouter-02-replies`). Built: `src/companion/adapters/openrouter/chat_model.py` (plain `httpx`, model name as given, `reasoning: {enabled}`, reasoning text from `message.reasoning`, tokens from `usage`; HTTP error status raises `httpx.HTTPStatusError`, an error body with a 200 raises `OpenRouterReplyError`, both caught by core as today; any tools raise `ToolsNotSupportedError` before sending). `CHAT_MODEL_ADAPTER=openrouter` builds it; a missing `OPENROUTER_API_KEY` fails in `build_chat_model`, which runs at app start. ADR 0028, ADR 0003 list, `CONTEXT.md` Model Price, BYOK step in `docs/DEPLOYMENT_GUIDE.md`. Two contract tests added.
  - Decisions: photos stay on direct DeepSeek under `openrouter` until 04, so the stack still starts. Under `openrouter` the reply and Reply Plan steps nearly always offer tools, so until 03 they fall back as on any model error; `/run` uses a tool-free service (Safeguard or Understanding) to show the model change.
  - Code review: standards clean; fixes made for reasoning type, ADR 0003 list, 200-with-error body.
  - Waiting on: `OPENROUTER_API_KEY` in `.env` and the operator's OK to run the paid contract tests and `/run`.
