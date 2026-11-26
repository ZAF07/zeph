# 05 — Claude models can be picked

Status: completed
Blocked by: 02

## Parent

`.scratch/openrouter/PRD.md` (user story 1).

## What to build

Admins can pick a Claude model for any core service in Prompts and models. A migration adds at least one Claude model (OpenRouter name) to the saved `available_models`, and its Model Price (SGD per million tokens) to `model_prices`. The seed only adds missing keys, so the seed file alone won't reach existing installs. The seed file gets the same additions. Every service stays on DeepSeek after this work.

## Acceptance criteria

- [x] Migration adds the Claude model to `available_models` and `model_prices`, keeping everything else (migration test)
- [x] Seed file matches
- [x] Contract test (remind the operator first): a Claude reply with thinking on returns reasoning text
- [x] `/run`: an Admin sets one core service to the Claude model, a message is sent, the reply arrives, and the Model Call Log and OpenRouter activity page show the Claude model; then set it back
- [x] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 02

## Comments

- 2026-11-24, done (branch `openrouter-05-claude-models`). Evidence:
  - Built: migration `0091_claude_models_can_be_picked.py` adds `anthropic/claude-haiku-5.5` and `anthropic/claude-sonnet-5.5` to `available_models`, and the Model Price of each one it adds to `model_prices`: haiku 0.13 in / 0.64 out, sonnet 2.56 in / 12.8 out (SGD per million tokens; Anthropic's prices on OpenRouter's model list, USD 0.10/0.50 and 2/10, at 1 USD ≈ 1.28 SGD like the DeepSeek ones). A Claude model an Admin already added is left as it is, with its price or with none. Going back keeps the models, since a service may use one. No `*_model` setting is touched, so every service stays on DeepSeek. The names come from `https://openrouter.ai/api/v1/models`.
  - Migration tests (`tests/test_claude_models_migration.py`): the models and prices are added and every other value is kept (an Admin's own price, a service's model and thinking); a Claude model already saved keeps its place and price; one saved with no price stays without one; going back keeps them.
  - Migration in the running stack, with the final code: set the database to 0090 with an Admin's own list order, own flash price, no pro price and `check_in_model` on pro, then restarted the backend. After 0091: the two Claude models at the end of the list in the Admin's order, both Claude prices added, the Admin's flash price kept, pro still without a price, `check_in_model` unchanged, and the other 150 Platform Settings (checksum), the User row and the 12 Model Call Log rows unchanged.
  - Seed: `src/companion/seed/platform_settings.yaml` has the same two names and prices. Tests: `test_the_deepseek_and_claude_models_are_the_ones_to_pick`, `test_every_model_to_pick_has_a_price`, and the settings, Eval cost and override-choice tests that list the seeded models.
  - Contract test (operator reminded in the session that it costs a little; two runs of two calls, well under a cent): `test_openrouter_returns_reasoning_when_thinking_is_on` now runs for `deepseek/deepseek-v4.1-flash-1017` and `anthropic/claude-haiku-5.5`, both passed against the real API. Finding: with thinking on, Claude decides itself whether to think. "What is 17 times 23?" came back with no reasoning (0 reasoning tokens, also with `effort: high` and on sonnet), so the test asks a question that takes a few steps. Recorded in ADR-0028.
  - `/run` (worktree stack, default `openrouter` adapter):
    - As a signed-in Admin in the Dashboard, Prompts & models showed the four models in every picker. Set Response composition to `anthropic/claude-haiku-5.5` and saved; the value held after a reload (screenshot).
    - A message was posted to the real `/telegram/webhook` of the real app inside the backend container, on the app database, through the eval `InProcessCompanion`: real repositories and the real `OpenRouterChatModel`, with a recording chat channel because fake chat IDs can't receive sends. The reply arrived ("Three tries on a chain is no joke, but you got there…").
    - Model Call Log: safeguard, understanding and reply_plan on `deepseek/deepseek-v4.1-flash-1017`, reply on `anthropic/claude-haiku-5.5` (4067 in / 60 out), no errors.
    - OpenRouter's own record of that call (`GET /api/v1/generation`, the data behind the activity page): `gen-1795534277-QxyWMskVMRJdvZ3J4B7V`, model `anthropic/claude-haiku-5.5-20261007`, provider Anthropic, `is_byok: true`, cost 0, 4067 / 60 tokens, matching the log.
    - Thinking turned on for the Reply in the Dashboard, and a puzzle sent: the reply was right, the Model Call Log row shows `anthropic/claude-haiku-5.5`, thinking on, 4121 in / 526 out, with Claude's reasoning text, and the Dashboard trace page shows the same (screenshot). OpenRouter's record `gen-1795534346-1JURyItuwQLJAA1nKaTS`: 299 reasoning tokens, `is_byok: true`.
    - Set back in the Dashboard to `deepseek/deepseek-v4.1-flash-1017`, thinking off. The next message's four calls were all DeepSeek, and no `*_model` setting holds a Claude name. 12 calls in all, 0 errors.
  - Checks, after rebasing on main (dc4f92f): `pytest` 2063 passed, `ruff`, `ruff format --check`, `mypy` clean. No `web/` files changed, so the web checks were not run.
  - Code review: standards (no hard violations; the migration now saves only on a change and names its model list, the seed test uses `MODEL_PRICES.key`), spec (a Claude model an Admin already added without a price no longer gets one; the contract question's answer is no longer in the question).
  - Also fixed: the 0090 migration tests ran to the newest revision, so 0091 changed what they checked. They, and the 0091 tests, now stop at their own revision.
  - Caveats:
    - The activity page itself needs the operator's OpenRouter login, so it was checked through OpenRouter's generation records, not by eye. The two IDs above can be looked up on the page.
    - The migration was not run on a copy of the main database (the main stack was not running); it was run on the worktree's database set to look like an existing install.
    - With thinking on, an easy Claude call shows no reasoning in the Model Call Log. That is Claude choosing not to think, not an error.
    - Two Claude models were added, not one: haiku (cheap) and sonnet (stronger). Sonnet was not called here; it is served by Anthropic under that name and takes the same request.
    - The model picker still cuts off long names (seen in 04).

## Completion

- Completed: 2026-11-24
- Commit: c7d2442 (merge of openrouter-05-claude-models; work in 38fc6e0 1665f7b 3d43edc 851335c)
