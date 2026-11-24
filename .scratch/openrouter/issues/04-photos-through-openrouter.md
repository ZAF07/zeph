# 04 — Photos through OpenRouter

Status: ready-for-agent
Blocked by: 02, 03

## Parent

`.scratch/openrouter/PRD.md` (user stories 15, 21).

## What to build

An OpenRouter adapter behind the `PhotoViewer` port. It sends the instructions as a system message and the photo as an image data URL in a user message, with thinking and the model name handled as in 02. It returns the text, tokens and reasoning. With `openrouter` as the adapter, photo viewing uses it. Once this and 03 are done, every model call works through OpenRouter, so this slice makes `openrouter` the default `CHAT_MODEL_ADAPTER`, with `deepseek` kept as the backup.

## Acceptance criteria

- [ ] Adapter tests: photo sent as a data URL with its media type; model name and thinking sent as given; text and tokens returned
- [ ] Adapter choice builds the OpenRouter photo viewer for `openrouter`, and `openrouter` is now the default (tests)
- [ ] `/run`: with the default adapter, a plain reply, a tool reply and a photo reply all work; switching to `deepseek` still works
- [ ] Contract test (remind the operator first): a photo is described through OpenRouter
- [ ] `/run`: a photo posted through the Telegram webhook is looked at, and the Model Call Log shows the photo model call
- [ ] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 02
- 03

## Comments

- 2026-11-24, from 02's `/run`: the operator saw the two test calls (`deepseek/deepseek-v4-pro`, `deepseek/deepseek-v4.1-flash`) on the OpenRouter activity page, but they used OpenRouter credits, not the operator's own DeepSeek key. Before this issue makes `openrouter` the default, the operator fixes the BYOK setup (DeepSeek key added, "Shared capacity fallback" set to "Never use any other provider or key for this key's models"; see `docs/DEPLOYMENT_GUIDE.md` "OpenRouter keys") and a test call is seen on the activity page as BYOK.
- 2026-11-24, status (branch `openrouter-04-photos`, mid-task, waiting on the operator):
  - Built and tested: `OpenRouterPhotoViewer` (`src/companion/adapters/openrouter/photo_viewer.py`, tests in `tests/adapters/test_openrouter_photo_viewer.py`); `CHAT_MODEL_ADAPTER=openrouter` now builds it (`tests/test_config.py`). Contract test `test_openrouter_describes_a_photo` passed for `anthropic/claude-haiku-5.5`; not yet run for DeepSeek. The two photo contract tests pointed at a test photo path that no longer exists; fixed.
  - Asked for by the issue 03 agent: `reply_message` now raises `OpenRouterReplyError` when the choice holds an error or finished with `"error"` (a 200 with an empty reply used to pass as a normal answer). Two tests in `tests/adapters/test_openrouter_chat_model.py`.
  - **Blocker, BYOK check with real calls (`usage.is_byok` in the reply):** Claude calls use the operator's Anthropic key (`is_byok: true`, cost 0). DeepSeek calls do not: `deepseek/deepseek-v4.1-flash` and `deepseek/deepseek-v4-pro` are not served by the DeepSeek provider on OpenRouter at all, so they go to other hosts (InferenceNet, Cohere, Alibaba, Nebius) on credits. DeepSeek itself serves only `deepseek/deepseek-v4.1-flash-1017` and `deepseek/deepseek-v4-pro-0813`, and those are blocked for this account by its privacy setting ("Paid model training violation (account settings)").
  - Not done: `openrouter` as the default, `/run`, DeepSeek contract test, full `pytest`. Next: the operator decides how DeepSeek calls should be made, then finish.
