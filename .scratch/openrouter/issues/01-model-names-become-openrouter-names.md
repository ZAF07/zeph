# 01 — Model names become OpenRouter names

Status: ready-for-agent
Blocked by: none

## Parent

`.scratch/openrouter/PRD.md` (user stories 2, 9, 10, 11, 12, 13, 14).

## What to build

Saved model names switch to OpenRouter's names, while the app still calls DeepSeek directly. A data migration renames the DeepSeek model names in every `*_model` Platform Setting, in `available_models` and in the `model_prices` keys, keeping each Admin's own choice (only renamed). The seed file and the eval judge settings get the same names. The direct DeepSeek adapter turns an OpenRouter DeepSeek name into its direct DeepSeek name, so replies keep working. A non-DeepSeek name under this adapter fails with a clear error. Look up the exact OpenRouter names for `deepseek-flash` and `deepseek-v4-pro` in OpenRouter's model list first, and record them under Comments.

## Acceptance criteria

- [ ] Migration renames saved model names, `available_models` and `model_prices` keys; an Admin's own choice is kept, only renamed (migration test)
- [ ] Seed file and eval judge settings use the OpenRouter names
- [ ] Direct DeepSeek adapter maps OpenRouter DeepSeek names to direct names; a Claude name fails clearly (tests)
- [ ] Saving a model name not in `available_models` is refused (test)
- [ ] `/run`: Prompts and models shows the new names, and a message sent through the Telegram webhook still gets a reply via direct DeepSeek
- [ ] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

None - can start immediately

## Comments

- 2026-11-24, OpenRouter names (from `https://openrouter.ai/api/v1/models`, checked against direct DeepSeek's `/models`):
  - `deepseek-flash` → `deepseek/deepseek-v4.1-flash`. Direct `deepseek-flash` is "DeepSeek-V4.1-Flash" and takes images; OpenRouter's `deepseek/deepseek-v4-flash` is the older 0423 build and is text only, so it would break photos.
  - `deepseek-v4-pro` → `deepseek/deepseek-v4-pro` (text only on both).
- Decisions: the direct DeepSeek adapter keeps a name with no provider part as it is (so old names and the contract tests still work), maps the two OpenRouter DeepSeek names, and raises `UnsupportedModelError` for any other `provider/model` name. The migration (0086) also renames the Judge's model in `eval_judge_settings`. Past Eval Runs (snapshots, Variants, call logs) are history and keep the names they ran with.
