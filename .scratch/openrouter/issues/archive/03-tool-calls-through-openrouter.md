# 03 — Tool calls through OpenRouter

Status: completed
Blocked by: 02

## Parent

`.scratch/openrouter/PRD.md` (user stories 16, 24).

## What to build

The OpenRouter adapter runs tool calls the way the DeepSeek adapter does today. Tools go out in the OpenAI function format. The loop allows at most 4 rounds, and a call with arguments that aren't valid JSON goes back as an error the model can retry. A final call then goes out with tools turned off. Tokens are summed across rounds, and every tool call is recorded. When a Claude model thinks while calling tools, the assistant message sent back each round keeps the reasoning details OpenRouter returned, because Anthropic needs them for the next round. Reuse the existing tool loop rather than copying it, if that stays simple.

## Acceptance criteria

- [x] Adapter tests: tools sent in function format; tool results sent back; broken JSON goes back as an error; last round forced to no tools; tokens summed; reasoning details kept on the assistant message for the next round
- [x] Contract test (remind the operator first): a tool call round-trip through OpenRouter
- [x] `/run`: a message that triggers a tool (e.g. a web search or Settings in Chat) gets a proper reply, and the Model Call Log shows the tool call
- [x] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 02

## Comments

- 2026-11-24, done (branch `openrouter-03-tool-calls`). Evidence:
  - Built: `src/companion/adapters/openrouter/chat_model.py` runs tool calls: `build_request` sends tools in OpenAI function format (and still sends them, with `tool_choice: "none"`, on the last round, as Anthropic refuses tool history without tools); `answer_with_tools` (pure, the model call injected) allows 4 rounds, sends each result back as a `tool` message, turns broken JSON into an error the model can retry, adds up tokens and reasoning across rounds and records every call; `to_assistant_message` keeps `reasoning_details` as OpenRouter returned them. `ToolsNotSupportedError` removed.
  - Decision on reuse: the DeepSeek loop works on LangChain `AIMessage`/`ToolMessage` objects, OpenRouter on plain JSON, so sharing the loop itself would need a translation layer (not simple). Instead the pieces that don't depend on that are shared in `src/companion/adapters/chat_tools.py` (`MAX_TOOL_ROUNDS`, `to_tool_schema`, the two error texts), used by both adapters; the OpenRouter loop mirrors DeepSeek's shape (`answer_with_tools`).
  - Adapter tests: `tests/adapters/test_openrouter_chat_model.py` (`httpx.MockTransport`): tools in function format, no tools sent when none offered, results sent back (also several calls in one round), unknown tool runs nothing, broken JSON goes back as an error and is recorded under "raw", after 4 rounds the last call has `tool_choice: "none"` with tools still sent, tokens summed, every call recorded, `reasoning_details` kept on the assistant message, reasoning from every round returned.
  - Contract tests (operator reminded they cost a little): `test_openrouter_calls_an_offered_tool_and_uses_its_result` passed against the real API for `deepseek/deepseek-v4.1-flash` and `anthropic/claude-haiku-5.5`, both with thinking on; re-run after review fixes, with the direct DeepSeek tool test, 5 passed. A logged Claude run showed the second request's assistant message carrying `reasoning_details` (`reasoning.text`) and a correct reply.
  - `/run` (worktree stack, `CHAT_MODEL_ADAPTER=openrouter`, texts sent through the real app in the backend container with eval `InProcessCompanion` on the app database: real repositories and OpenRouter chat model, canned (empty) web search and a recording chat channel, since fake chat IDs can't receive sends): "look up who won the most recent Singapore Grand Prix" → Reply called `web_search` 3 times (empty canned results, so the reply said search wasn't working and answered from memory); "I've just moved to London… use London time" → `change_time_zone`, User's time zone became Europe/London. Model call log trace pages (as Admin, screenshots) show the Reply step on `deepseek/deepseek-v4.1-flash` with "Tools called: web_search, web_search, web_search" and "change_time_zone", 0 errors. After the review fixes, on a rebuilt stack: `web_search` again, and "don't message me between 11pm and 7am" → `change_quiet_hours`, quiet hours 23:00–07:00.
  - Checks: `pytest` 1967 passed, `ruff`, `ruff format --check`, `mypy` clean.
  - Code review: standards (no hard violations; shared the copied tool pieces, made the loop a pure function, request built fresh each round), spec (nothing missing; added asserts for tools on the last round and several calls in one round).
  - Caveats: a choice-level error (`choices[0].error` with an empty message) still becomes an empty reply rather than an error; this was so before 03. Arguments sent as an object rather than a JSON string would raise; OpenRouter always sends a string. The default adapter stays `deepseek` until 04.

## Completion

- Completed: 2026-11-24
- Commit: ddaf1e7 (merge of openrouter-03-tool-calls; work in 4df61aa, 25d7591, 48126db)
