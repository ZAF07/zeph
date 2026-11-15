# 22 — Call DeepSeek by its current model name, with a Thinking switch per call

Status: ready-for-agent

## What

Every model setting uses the legacy names `deepseek-chat` and `deepseek-reasoner`. DeepSeek's [Change Log](https://api-docs.deepseek.com/updates/) says these two names point to the non-thinking and thinking modes of one model, and were due to be discontinued on 2026-07-24. They still answer today (2026-11-15), but could stop at any time, and every call would then fail.

The current model is `deepseek-flash` (DeepSeek-V4.1-Flash-1017; see [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing)). Thinking is a setting on the call, not a separate model: see the [Thinking Mode guide](https://api-docs.deepseek.com/guides/thinking_mode).

Checked in issue 21: both legacy names come back from the API as `model: deepseek-flash`; only `deepseek-reasoner` returns `reasoning_content` and reasoning tokens. This is also why DeepSeek's usage page shows a single model for both. The reply already works with thinking on and tools (issue 21).

## Decisions (2026-11-15)

- **Thinking is its own switch, not part of the model.** On the Dashboard's Prompts and Models page (`web/src/components/PromptsAndModels.tsx`), each call keeps its model picker as it is and gets a "Thinking" on/off toggle beside it. Why: the LLM is an adapter (ports and adapters), not core; more models may be added later, and most models today can turn thinking on or off.
- **The core asks, the adapter does it.** The chat model port takes whether to think for the call; each model adapter turns that into what its API needs (for DeepSeek, the thinking parameter). Core code never knows a model's way of switching.
- **Model choices:** `available_models` becomes `deepseek-flash` (replacing `deepseek-chat` and `deepseek-reasoner`). `deepseek-v4-pro` is not added until there is a reason.
- **Old values keep working:** a stored `deepseek-chat` or `deepseek-reasoner` is read as `deepseek-flash`, with thinking on for `deepseek-reasoner`, so nothing breaks before the settings are reset.
- **Every model setting gets the switch**, including the photo model. Starting values follow issue 21: thinking **on** for the Understanding, Safeguard, memory processing, Life Thread keeping, Portrait, Curiosity keeping and Check-in calls; **off** for the reply, Knowledge "when it helps", personal sticker keeping and photo calls.
- **On/off only.** No effort level for now (see issue 23).
- **A model that can't do what was asked** (can't turn thinking off, or has none) gets the closest it can; the adapter logs a warning and the User sees no error.
- **The Model Call Log records whether thinking was on** for each call, beside the model.
- **Seed file only, no migration** (as issues 17 and 21: not live, Admins own settings in production). At the end, reset the local main database's model and thinking settings with a one-off command, shown to the User before it runs.

## Acceptance criteria

- [ ] No model setting or code default uses `deepseek-chat` or `deepseek-reasoner`; a stored old name still works as described above
- [ ] Admins see a Thinking toggle beside each model on the Prompts and Models page, and a change reaches the next call
- [ ] The calls with thinking on show reasoning tokens in the Model Call Log; the others don't; the log shows whether thinking was on
- [ ] The DeepSeek adapter is the only place that knows how DeepSeek switches thinking
- [ ] Each call works in the running app (`/run`), the Dashboard toggle included
- [ ] `make eval` is no worse than issue 21's runs (reminder: evals cost money)
- [ ] `make check-python` and `make check-web` pass
- [ ] The local main database has the new settings

## Comments
