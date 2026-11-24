# 01 — Model names become OpenRouter names

Status: completed
Blocked by: none

## Parent

`.scratch/openrouter/PRD.md` (user stories 2, 9, 10, 11, 12, 13, 14).

## What to build

Saved model names switch to OpenRouter's names, while the app still calls DeepSeek directly. A data migration renames the DeepSeek model names in every `*_model` Platform Setting, in `available_models` and in the `model_prices` keys, keeping each Admin's own choice (only renamed). The seed file and the eval judge settings get the same names. The direct DeepSeek adapter turns an OpenRouter DeepSeek name into its direct DeepSeek name, so replies keep working. A non-DeepSeek name under this adapter fails with a clear error. Look up the exact OpenRouter names for `deepseek-flash` and `deepseek-v4-pro` in OpenRouter's model list first, and record them under Comments.

## Acceptance criteria

- [x] Migration renames saved model names, `available_models` and `model_prices` keys; an Admin's own choice is kept, only renamed (migration test)
- [x] Seed file and eval judge settings use the OpenRouter names
- [x] Direct DeepSeek adapter maps OpenRouter DeepSeek names to direct names; a Claude name fails clearly (tests)
- [x] Saving a model name not in `available_models` is refused (test)
- [x] `/run`: Prompts and models shows the new names, and a message sent through the Telegram webhook still gets a reply via direct DeepSeek
- [x] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

None - can start immediately

## Comments

- 2026-11-24, OpenRouter names (from `https://openrouter.ai/api/v1/models`, checked against direct DeepSeek's `/models`):
  - `deepseek-flash` → `deepseek/deepseek-v4.1-flash`. Direct `deepseek-flash` is "DeepSeek-V4.1-Flash" and takes images; OpenRouter's `deepseek/deepseek-v4-flash` is the older 0423 build and is text only, so it would break photos.
  - `deepseek-v4-pro` → `deepseek/deepseek-v4-pro` (text only on both).
- Decisions: the direct DeepSeek adapter keeps a name with no provider part as it is (so old names and the contract tests still work), maps the two OpenRouter DeepSeek names, and raises `UnsupportedModelError` for any other `provider/model` name. The migration (0087) also renames the Judge's model in `eval_judge_settings`. Past Eval Runs (snapshots, Variants, call logs) are history and keep the names they ran with.

- 2026-11-24, done. Evidence:
  - Migration: `tests/test_openrouter_model_names_migration.py` (rename, Admin's `deepseek-v4-pro` choice kept, price keys and Judge model renamed, downgrade round trip). In the running stack: took the database back to 0086, saved `response_model = deepseek-v4-pro` and `available_models = [deepseek-flash, deepseek-v4-pro]`, restarted the backend. After 0087: `response_model = deepseek/deepseek-v4-pro`, `available_models` and `model_prices` keys renamed, Judge model `deepseek/deepseek-v4.1-flash`, no `*_model` left on an old name.
  - Seed: `src/companion/seed/platform_settings.yaml` and `src/companion/seed/evals/judge.yaml` use the new names; a fresh stack seeds them.
  - Adapter: `tests/adapters/test_deepseek_chat_model.py` (both OpenRouter DeepSeek names map to direct names; `anthropic/claude-sonnet-5.5` and an unknown `deepseek/` name raise `UnsupportedModelError`).
  - Refusal: `test_saving_a_model_admins_cant_pick_is_refused`. In the running app the Admin API returned 422 "The Safeguard model must be one of the listed models." for `deepseek/deepseek-typo` and `anthropic/claude-sonnet-5.5`, and the value stayed unchanged.
  - `/run`: Prompts & models shows 15 model pickers, all on the new names with options `[deepseek/deepseek-v4.1-flash, deepseek/deepseek-v4-pro]`, no old names on the page, and the Reply picker on the kept `deepseek/deepseek-v4-pro`. A Telegram update sent to `/telegram/webhook` (real app and adapters in the backend container, `CHAT_MODEL_ADAPTER=deepseek`, only the chat channel swapped for a recording one, as fake chat IDs can't receive sends) got two reply texts. The Model Call Log shows safeguard, understanding and reply_plan on `deepseek/deepseek-v4.1-flash` and reply on `deepseek/deepseek-v4-pro`, with no errors.
  - Checks after rebasing on main: `pytest` 1926 passed, `ruff`, `ruff format --check` and `mypy` clean. The migration was renumbered 0086 to 0087 because main added `0086_directness`.
  - Caveats: saved `deepseek-chat`/`deepseek-reasoner` names (if any remain on prod) are not renamed; they still work under direct DeepSeek because names with no provider part pass through. Re-running an old Eval Run whose Variant overrides use old names is refused with the usual "must be one of the listed models", since overrides are checked again. Web test fixtures still use the old example names (cosmetic).

## Completion

- Completed: 2026-11-24
- Commit: <merge commit, filled in below after merge>
