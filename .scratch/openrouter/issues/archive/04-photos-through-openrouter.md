# 04 — Photos through OpenRouter

Status: completed
Blocked by: 02, 03

## Parent

`.scratch/openrouter/PRD.md` (user stories 15, 21).

## What to build

An OpenRouter adapter behind the `PhotoViewer` port. It sends the instructions as a system message and the photo as an image data URL in a user message, with thinking and the model name handled as in 02. It returns the text, tokens and reasoning. With `openrouter` as the adapter, photo viewing uses it. Once this and 03 are done, every model call works through OpenRouter, so this slice makes `openrouter` the default `CHAT_MODEL_ADAPTER`, with `deepseek` kept as the backup.

## Acceptance criteria

- [x] Adapter tests: photo sent as a data URL with its media type; model name and thinking sent as given; text and tokens returned
- [x] Adapter choice builds the OpenRouter photo viewer for `openrouter`, and `openrouter` is now the default (tests)
- [x] `/run`: with the default adapter, a plain reply, a tool reply and a photo reply all work; switching to `deepseek` still works
- [x] Contract test (remind the operator first): a photo is described through OpenRouter
- [x] `/run`: a photo posted through the Telegram webhook is looked at, and the Model Call Log shows the photo model call
- [x] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 02
- 03

## Comments

- 2026-11-24, from 02's `/run`: the operator saw the two test calls (`deepseek/deepseek-v4-pro`, `deepseek/deepseek-v4.1-flash`) on the OpenRouter activity page, but they used OpenRouter credits, not the operator's own DeepSeek key. Before this issue makes `openrouter` the default, the operator fixes the BYOK setup (DeepSeek key added, "Shared capacity fallback" set to "Never use any other provider or key for this key's models"; see `docs/DEPLOYMENT_GUIDE.md` "OpenRouter keys") and a test call is seen on the activity page as BYOK.
- 2026-11-24, done (branch `openrouter-04-photos`). Evidence:
  - Built: `OpenRouterPhotoViewer` (`src/companion/adapters/openrouter/photo_viewer.py`) sends the instructions as a system message and the photo as an image data URL in a user message, with the model name and thinking as in 02, and returns text, tokens and reasoning. It shares `build_request`, `send_request` and `to_model_answer` with the chat model. `build_photo_viewer` builds it for `openrouter`, and `openrouter` is the default `CHAT_MODEL_ADAPTER` (`config.py`). `DEEPSEEK_API_KEY` is now only needed for the `deepseek` backup; a chosen adapter without its key fails at startup.
  - Asked for by the issue 03 agent: `reply_message` raises `OpenRouterReplyError` when the choice holds an error or finished with `"error"` (a 200 with an empty reply used to pass as a normal answer). Tests for the chat model and the photo viewer.
  - **BYOK (the operator asked that calls use their own keys, never credits).** Checked with real calls and `usage.is_byok` in the reply. Claude calls used the Anthropic key from the start. DeepSeek calls did not, for two reasons: (1) DeepSeek's own servers on OpenRouter serve only `deepseek/deepseek-v4.1-flash-1017` and `deepseek/deepseek-v4-pro-0813`; the names saved by 01 (`deepseek/deepseek-v4.1-flash`, `deepseek/deepseek-v4-pro`) are served only by other hosts, on credits; (2) the account's privacy setting refused DeepSeek ("Paid model training violation"). The operator changed the privacy setting. In code:
    - migration `0090_deepseek_served_model_names.py` renames the saved names to the dated ones in every `*_model` setting, `available_models`, `model_prices` and the Judge's model, keeping Admin choices, and adds pro to `available_models` (the operator wants Admins to pick flash or pro; model and thinking stay separate choices). Seed, Judge seed and the direct-DeepSeek name mapping follow. Tests: `tests/test_deepseek_served_model_names_migration.py` (rename, pro not added twice, a model saved under both names kept once, going back).
    - every request allows only the model's maker to answer (`provider: {only: [<name before "/">]}`), so a call fails instead of going to another host on credits;
    - a reply whose usage says `is_byok: false` is logged as a warning.
    - After the fix: flash and pro, thinking on and off, all `is_byok: true`, cost 0. During the `/run` the key's credit usage stayed at $0.02505 (spent earlier, by 02, 03 and the first probes here) while own-key usage went from $0.0094 to $0.0139.
  - Adapter tests (`tests/adapters/test_openrouter_photo_viewer.py`, `httpx.MockTransport`): photo as a data URL in a user message after the instructions; the data URL carries the media type; model name as given, maker only, no tools; thinking on/off as `reasoning.enabled`; text, tokens and reasoning returned; error status and error bodies raised.
  - Adapter choice (`tests/test_config.py`): the default is `openrouter` and builds both OpenRouter adapters; `deepseek` builds both direct ones; each fails at startup without its key.
  - Contract tests (operator reminded they cost a little): all 6 OpenRouter tests passed against the real API, re-run after the review fixes: `test_openrouter_describes_a_photo` for `deepseek/deepseek-v4.1-flash-1017` and `anthropic/claude-haiku-5.5`, plus the reply, reasoning and two tool tests. The photo tests pointed at a test photo path that no longer exists; fixed for the direct DeepSeek one too.
  - `/run` (worktree stack, no `CHAT_MODEL_ADAPTER` set, so the default; updates posted to the real `/telegram/webhook` of the real app in the backend container through the eval `InProcessCompanion` on the app database: real repositories, real OpenRouter chat model and photo viewer; recording chat channel that serves `weekend-list.jpg` in place of Telegram's download, canned web search, since fake chat IDs can't receive sends):
    - plain text: a normal reply; "I've just moved to London, please use London time" called `change_time_zone` and confirmed; the photo with a caption got a reply about the list's items (compost, monstera, Gran).
    - Model Call Log: 13 calls on `deepseek/deepseek-v4.1-flash-1017`, 0 errors, with a `photo` step (506 in / 136 out) and the Reply step showing `change_time_zone`. Seen as Admin on the Dashboard trace page (screenshot): the Photo card shows the model, Thinking off and the tokens.
    - With `CHAT_MODEL_ADAPTER=deepseek`, the same three messages worked (DeepSeekChatModel and DeepSeekPhotoViewer; the saved dated names are sent as direct names); 26 calls in all, 0 errors.
    - Reply model set to `deepseek/deepseek-v4-pro-0813` with thinking on: the reply came, logged with that model and thinking on; then set back.
  - Checks, after the last rebase on main: `pytest` 2056 passed, `ruff`, `ruff format --check`, `mypy` clean.
  - Code review: standards (no hard violations; added `model_maker`, `warn_if_paid_with_credits` and `required_key`, simplified the migration), spec (migration renumbered after main's, double-name edge cases handled, clearer error text, photo tests for the maker pin and the choice error).
  - Caveats:
    - The migration was not run on a copy of the main database (the main stack's Postgres was not running); it is covered by the migration tests. The `/run` was done before the migration was renumbered from 0089 to 0090 (number only).
    - The main folder's `.env` (and likely production's) sets `CHAT_MODEL_ADAPTER=deepseek` outright. The new default only applies once that line is removed or set to `openrouter`, with `OPENROUTER_API_KEY` set.
    - The maker rule means a model whose maker is not also its OpenRouter provider can't be called until the rule is widened (ADR-0028).
    - The credits warning comes after a call; the maker rule and the two account settings are the guard.
    - On Prompts and models, the model picker cuts off the longer names (`deepseek/deepseek-v4.1-flash…`).
    - Thinking switch usable only when the model can think: filed as issue 07, not built here.

## Completion

- Completed: 2026-11-24
- Commit: 8389576 (merge of openrouter-04-photos; work in 76f63f0 ad292ed 25f0bdb f89d76e 68cc6eb)
