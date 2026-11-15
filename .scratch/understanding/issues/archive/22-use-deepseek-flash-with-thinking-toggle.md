# 22 — Call DeepSeek by its current model name, with a Thinking switch per call

Status: completed

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

- [x] No model setting or code default uses `deepseek-chat` or `deepseek-reasoner`; a stored old name still works as described above (old names only in `adapters/deepseek/chat_model.py`'s `build_client`; unit tests, contract tests and a /run with stored old names)
- [x] Admins see a Thinking toggle beside each model on the Prompts and Models page, and a change reaches the next call (/run: all 11 cards show it; turned Understanding off then on from the Dashboard, the next message's Understanding call followed each time)
- [x] The calls with thinking on show reasoning tokens in the Model Call Log; the others don't; the log shows whether thinking was on (/run table below; trace page shows "Thinking On/Off")
- [x] The DeepSeek adapter is the only place that knows how DeepSeek switches thinking (`"thinking": {"type": "enabled"|"disabled"}` only in `build_client`)
- [x] Each call works in the running app (`/run`), the Dashboard toggle included (all 11 calls, see Comments)
- [x] `make eval` is no worse than issue 21's runs (69/70; issue 17: 68/70)
- [x] `make check-python` and `make check-web` pass (after rebase: 999 passed; web 384 passed, lint, format, typecheck)
- [x] The local main database has the new settings (one-off reset, see Comments)

## Comments

- 2026-11-15, from the eval dashboard grilling (`.scratch/eval-dashboard/issues/archive/01-run-evals-from-the-dashboard.md`): no change to this issue's scope. FYI: (1) the Thinking switch will be a Platform Setting that Eval Variants can override, so keep it a normal Platform Setting (not a model-name suffix); (2) the Eval Judge's model is hardcoded as `deepseek-chat` in `evals/judge.py` (`JUDGE_MODEL`); move it to `deepseek-flash` here too; (3) Eval Model Prices are seeded only for `deepseek-flash` and `deepseek-v4-pro`, so old names show "no price set" until this lands.
- 2026-11-15 (implementation):
  - **Settings:** an on/off `<call>_thinking` Platform Setting beside each of the 11 `<call>_model` settings (new `SettingKind.ON_OFF`, `read_on_off`), each core service names its `thinking_key`, `available_models` is `[deepseek-flash]`. Seed values exactly as decided (on: Understanding, Safeguard, memory processing, Life Thread keeping, Portrait, Curiosity keeping, Check-in; off: reply, Knowledge "when it helps", Personal Sticker keeping, photo). `tests/test_model_defaults.py` pins them.
  - **Port and adapter:** `ChatModel.generate` and `PhotoViewer.look` take `thinking: bool`; every call site passes its setting. `build_client` in the DeepSeek adapter sends `thinking: enabled/disabled` (DeepSeek's default is on, so off is always sent), maps `deepseek-chat` to `deepseek-flash` with thinking as asked and `deepseek-reasoner` to `deepseek-flash` with thinking on (warning when asked off).
  - **Model Call Log:** a `thinking` column (migration **0042**, renumbered from 0041 at rebase because eval dashboard issue 02 took 0041; the column is the one exception to "no migration", needed for the log), shown as "Thinking On/Off" on each call card.
  - **Judge:** `deepseek-flash`, thinking off (`JUDGE_THINKING`), and the Eval Run's Judge snapshot records it.
  - **Contract tests (real DeepSeek):** thinking on gives reasoning and off gives none, for `deepseek-flash` and the old `deepseek-chat`; photo with `deepseek-flash`; tools with thinking on. 5 passed.
  - **/run** (worktree stack; real app, Postgres, DeepSeek chat model and photo viewer, fastembed; chat channel, clock, scheduler, timer and auth faked as a worktree has no Telegram chat). Dashboard: all 11 cards show the Thinking switch beside `deepseek-flash`; Understanding switched off, saved, stayed off after reload; fine at 390 px. Then 2 texts, a photo (`weekend-list.jpg`) and a sticker, end of Conversation, a Check-in, and a Knowledge upload. Log (step, thinking, tokens out, has reasoning): safeguard on 79 yes; understanding **off** 133 no (as set on the Dashboard); reply off 18 no; photo off 86 no; personal_stickers off 49 no; conversation_end on 542 yes; life_threads on 678 yes; curiosities on 908 yes; portrait on 493 yes; check_in on 404 yes; no errors, all answers used (Check-in sent, sticker kept, Threads and Curiosities saved). Knowledge "when it helps" (not a User's call, so not in the log) drafted the description with thinking off. Switched Understanding back on from the Dashboard: the next Understanding call was on, 475 out, with reasoning. Stored old names (`understanding_model: deepseek-reasoner` with thinking off, `response_model: deepseek-chat`): Understanding thought (451 out, reasoning, warning logged), reply didn't; no errors.
  - **Caveat:** the log records the thinking that was asked for. For a stored `deepseek-reasoner` with thinking off it says "Off" though the call thinks. This only happens before settings are reset to `deepseek-flash`.
  - **Eval** (before rebase, `make eval`): 69 of 70; 382,000 tokens in, 44,000 out, 8.7 min; Understanding 32/32 checks. The fail was reply-side: `strong-mood-unknown-cause` asked two questions at once (`gentle_probe`). After rebase onto eval dashboard issue 02 (Evals now run through the eval-runner), `make eval EVALS=photo_descriptions,understanding`: Photo 1/1, Understanding 40/41 (reply-side flake: `brushed-off-not-raised-too-soon` asked how dad was though the Understanding left the Thread alone), rerun 41/41. Both flakes noted on issue 25.
  - **/code-review:** Standards: no hard breaks; merged the two `deepseek-reasoner` checks, save-failed wording now says thinking. Kept `model` and `thinking` as separate settings (the decided Platform Setting that Eval Variants override) rather than one `ModelChoice` value. Spec: matches; evals README updated; migration and the log caveat noted above.
  - **Local main DB reset** (shown, then run): started only the main Postgres, migrated 0040 → 0042, deleted `available_models` and every `*_model` / `*_thinking` setting (13 rows, including the long-unused `memory_retrieval_model`), re-seeded: all 11 on `deepseek-flash` with Thinking as seeded; stopped Postgres. The owner's Admin had set `response_model` to `deepseek-reasoner`; the reply's Thinking is now off (the decided starting value) and can be switched on on the Dashboard.

## Completion

- Completed: 2026-11-15
- Commits: `dcdb024` (deepseek-flash, Thinking switch, log, Judge, tests), `bb0fac5` (review fixes, eval notes); merged to main in `92e60da`
