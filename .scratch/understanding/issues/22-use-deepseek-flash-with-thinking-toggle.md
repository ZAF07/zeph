# 22 — Call DeepSeek by its current model name, with thinking on or off per call

Status: needs-triage

## What

Every model setting uses the legacy names `deepseek-chat` and `deepseek-reasoner`. DeepSeek's [Change Log](https://api-docs.deepseek.com/updates/) says these two names point to the non-thinking and thinking modes of one model, and were due to be discontinued on 2026-07-24. They still answer today (2026-11-15), but could stop at any time, and every call would then fail.

The current model is `deepseek-flash` (DeepSeek-V4.1-Flash-1017; `deepseek-v4-pro` also exists). Thinking is a setting on the call, not a separate model: see the [Thinking Mode guide](https://api-docs.deepseek.com/guides/thinking_mode) (toggle and effort control).

Checked in issue 21: both legacy names come back from the API as `model: deepseek-flash`; only `deepseek-reasoner` returns `reasoning_content` and reasoning tokens. This is also why DeepSeek's usage page shows a single model for both.

## To decide (grilling)

- How an Admin picks thinking: a per-call on/off (and effort?) setting next to each `*_model` setting, or model choices in `available_models` that carry the mode (e.g. "deepseek-flash" and "deepseek-flash (thinking)").
- Whether `deepseek-v4-pro` joins `available_models`.
- How the adapter sends the toggle through `langchain_deepseek.ChatDeepSeek` (extra body parameter) and whether reasoning is still read from `reasoning_content`.
- Whether the Model Call Log's `model` column keeps the name plus the mode.
- Seed file only, or a migration too (issue 21 chose seed file only: not live, Admins own settings in production).

## Acceptance criteria

- [ ] No model setting or code default uses `deepseek-chat` or `deepseek-reasoner`
- [ ] The calls issue 21 put on reasoner still think (reasoning tokens in the Model Call Log); the others don't
- [ ] Admins can still pick the model and thinking per call on the Dashboard
- [ ] `make eval` is no worse than issue 21's runs
- [ ] `make check-python` and `make check-web` pass

## Comments
