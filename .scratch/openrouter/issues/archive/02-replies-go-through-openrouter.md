# 02 — Replies go through OpenRouter

Status: completed
Blocked by: 01

## Parent

`.scratch/openrouter/PRD.md` (user stories 3, 4, 5, 6, 7, 8, 17, 18, 21, 22, 23, 25, 26, 27).

## What to build

A new OpenRouter adapter behind the `ChatModel` port, built on plain `httpx` (not LangChain) against OpenRouter's Chat Completions API, taking an optional HTTP client like the Tavily adapter. It sends the model name exactly as read from Platform Settings, maps the `thinking` flag to `reasoning: {enabled: true|false}`, and returns the reply text, tokens in and out, and the reasoning text from the reply's `reasoning` field. Tools are not part of this slice. When a call asks for tools, the adapter refuses clearly until 03 lands. `OPENROUTER_API_KEY` is read through config, and `CHAT_MODEL_ADAPTER` gains `openrouter`. The default stays `deepseek` until 04, so shipping this slice never breaks tool or photo replies for real Users. A missing key fails at startup. Add an ADR "Model calls go through OpenRouter, direct DeepSeek kept as backup" (updating ADR 0003's adapter list), and fix the Model Price entry in `CONTEXT.md`. Record the manual OpenRouter step: set "Shared capacity fallback" to "Never use any other provider or key for this key's models" on each BYOK key.

## Acceptance criteria

- [x] Adapter tests with `httpx.MockTransport`: model name sent as given; thinking on/off maps to `reasoning`; reasoning text returned; tokens recorded; an HTTP error is handled as today
- [x] `openrouter` builds the OpenRouter adapter, `deepseek` still builds the direct one and stays the default; a missing key fails at startup (tests)
- [x] Contract tests (remind the operator first; costs money): a DeepSeek reply; a reply with thinking on that returns reasoning text
- [x] ADR added; `CONTEXT.md` Model Price entry updated; manual BYOK fallback step written down
- [x] `/run` with `CHAT_MODEL_ADAPTER=openrouter`: an Admin changes a core service's model in Prompts and models, a message is sent, and both the Model Call Log and the OpenRouter activity page show the new model
- [x] `/run`: with thinking on, the reasoning shows in the Model Call Log
- [x] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 01

## Comments

- 2026-11-24, in progress (branch `openrouter-02-replies`). Built: `src/companion/adapters/openrouter/chat_model.py` (plain `httpx`, model name as given, `reasoning: {enabled}`, reasoning text from `message.reasoning`, tokens from `usage`; HTTP error status raises `httpx.HTTPStatusError`, an error body with a 200 raises `OpenRouterReplyError`, both caught by core as today; any tools raise `ToolsNotSupportedError` before sending). `CHAT_MODEL_ADAPTER=openrouter` builds it; a missing `OPENROUTER_API_KEY` fails in `build_chat_model`, which runs at app start. ADR 0028, ADR 0003 list, `CONTEXT.md` Model Price, BYOK step in `docs/DEPLOYMENT_GUIDE.md`. Two contract tests added.
  - Decisions: photos stay on direct DeepSeek under `openrouter` until 04, so the stack still starts. Under `openrouter` the reply and Reply Plan steps nearly always offer tools, so until 03 they fall back as on any model error; `/run` uses a tool-free service (Safeguard or Understanding) to show the model change.
  - Code review: standards clean; fixes made for reasoning type, ADR 0003 list, 200-with-error body.
  - Waiting on: `OPENROUTER_API_KEY` in `.env` and the operator's OK to run the paid contract tests and `/run`.

- 2026-11-24, done. Evidence:
  - Adapter: `tests/adapters/test_openrouter_chat_model.py` (8 tests, `httpx.MockTransport`): model name and messages sent as given, `reasoning: {enabled: true|false}`, text, tokens and reasoning returned, no reasoning or usage gives None and 0, an error status raises `httpx.HTTPStatusError` and a 200 error body raises `OpenRouterReplyError` (both caught by core's `except Exception` as today; seen in `/run`, where the refused steps logged their error and the User got the usual fallback text), tools refused before any request.
  - Adapter choice: `tests/test_config.py` (`deepseek` is the default and builds the direct adapters; `openrouter` builds `OpenRouterChatModel` with photos on direct DeepSeek; `openrouter` without `OPENROUTER_API_KEY` raises `MissingSettingsError`; an unknown name is refused). In the running stack the backend started healthy with `CHAT_MODEL_ADAPTER=openrouter`; `build_chat_model` runs in `build_production_app`.
  - Contract tests (operator OK'd, DeepSeek model): `test_openrouter_generates_a_deepseek_reply` and `test_openrouter_returns_reasoning_when_thinking_is_on` passed against the real API (`deepseek/deepseek-v4.1-flash`).
  - Docs: `docs/adr/0028-model-calls-go-through-openrouter-direct-deepseek-kept-as-backup.md`, ADR 0003's adapter list, `CONTEXT.md` Model Price, BYOK step under "OpenRouter keys" in `docs/DEPLOYMENT_GUIDE.md`.
  - `/run` (worktree stack, `CHAT_MODEL_ADAPTER=openrouter`): `available_models` set by SQL to both DeepSeek names (a fresh seed has one). As an Admin in Prompts & models, Safeguard's model changed from `deepseek/deepseek-v4.1-flash` to `deepseek/deepseek-v4-pro` and saved ("Saved.", still set after reload). One text was sent through the real app and adapters in the backend container (eval `InProcessCompanion` on the app database: real repositories and OpenRouter chat model, only the chat channel recording, as fake chat IDs can't receive sends). Model call log trace page: Safeguard on `deepseek/deepseek-v4-pro`, thinking on, 497 in / 33 out; Understanding on `deepseek/deepseek-v4.1-flash`, 846 in / 586 out; Reply Plan and Reply show `ToolsNotSupportedError` (expected until 03). The operator saw both calls with those models on the OpenRouter activity page.
  - Thinking: `model_calls.content.reasoning` is filled for Safeguard and Understanding (thinking on), e.g. "We need answer only label. Need analyze. Latest message: ...".
  - Checks after rebasing on main: `pytest` 1957 passed (after rebasing on main with pattern 14), `ruff`, `ruff format --check` and `mypy` clean.
  - Caveats: the two `/run` calls used OpenRouter credits, not the operator's own DeepSeek key, so the BYOK setup isn't right yet (noted on 04, which must not make `openrouter` the default until it is). Under `openrouter`, replies and Reply Plans fall back until 03 because they offer tools; the default stays `deepseek`, so real Users are unaffected.

## Completion

- Completed: 2026-11-24
- Commit: <to be filled in after merge>
