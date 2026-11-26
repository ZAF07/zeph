# 07 — Thinking switch only when the model can think

Status: completed
Blocked by: 04

## Parent

`.scratch/openrouter/PRD.md` (user story 5). Asked for by the operator on 2026-11-24, during issue 04.

## What to build

In Prompts and models, the model and the thinking switch stay two separate choices for each core service. An Admin picks any model in the list (DeepSeek flash or pro, a Claude model, others later) and, apart from that, sets thinking on or off. The thinking switch can only be used when the chosen model can think. For a model that can't, the switch is shown off and can't be turned on, and the call is made with thinking off.

Every model in the list today (DeepSeek flash and pro, Claude) can think, so nothing is wrong until a model that can't is added.

## Open questions (answered by the operator, 2026-11-25)

- Where "can this model think" comes from: a Platform Setting list of models that can't think, kept beside the model list. Not read from OpenRouter.
- A service whose thinking is on when its model is changed to one that can't think: thinking is saved as off.

## Acceptance criteria

- [x] An Admin can't turn thinking on for a model that can't think (Dashboard and API, tests)
- [x] A call for a model that can't think is made with thinking off (test)
- [x] Models that can think behave as today
- [x] `/run`: the switch is usable for a model that can think and not for one that can't
- [x] The language's checks pass

## Blocked by

- 04

## Comments

- 2026-11-25, operator's answers to the open questions:
  - "Can this model think" comes from a Platform Setting list of models that can't think (`models_that_cannot_think`), kept beside `available_models` and filled by the seed or a migration. Empty today. Not read from OpenRouter.
  - A service with thinking on whose model is changed to one that can't think gets its thinking saved as off.
- 2026-11-25, in progress on branch `openrouter-07-thinking-switch` (worktree `ai-chat-companion-openrouter-07`).
- 2026-11-25, done. Evidence:
  - Built:
    - Platform Setting `models_that_cannot_think` (a list of model names, empty in the seed). The seed adds missing keys at startup, so existing installs get it with no migration. Like `available_models`, it is not editable in the Dashboard.
    - Saving (`with_thinking_fitted_to_the_models`, used by `PlatformSettingsService.update`): turning thinking on for a core service whose model (new or saved) can't think is refused with 422, e.g. "The Response composition thinking can't be on: deepseek/deepseek-v4-pro-0813 can't think.", and nothing is saved. Changing a service to such a model while its thinking is saved on saves thinking as off.
    - Calls (`thinking_to_use`): all 16 core services (15 chat calls and the photo look) ask it, so a model that can't think is called with thinking off whatever is saved, and the Model Call Log says off.
    - API: `GET /api/admin/core-services` also returns `models_that_cannot_think`.
    - Dashboard (`CoreServiceCard`): while the chosen model can't think the switch is off and locked. Picking such a model switches thinking off, and it stays off after going back to a model that can think.
    - ADR-0028 and `docs/DEPLOYMENT_GUIDE.md` say a new model that can't think must be added to the list.
  - Criterion 1 (can't turn thinking on; Dashboard and API):
    - Tests: `tests/test_thinking_only_when_the_model_can_think.py` (refused with the model in the same save; refused when the saved model can't think; changing the model saves thinking off and leaves other services alone; off can be saved; thinking already off is not saved again; on is fine for a model that can think) and `PromptsAndModels.test.tsx` ("keeps the thinking switch off and locked for a model that can't think", "shows thinking off when it is saved on for a model that can't think", "lets thinking be switched on again for a model that can think").
    - Running app: see `/run` below.
  - Criterion 2 (call made with thinking off):
    - Tests: `test_a_call_for_a_model_that_cant_think_is_made_with_thinking_off` (a message through the webhook), the three `thinking_to_use` tests, and `test_every_core_service_asks_whether_its_model_should_think`.
    - Running app: with Response composition on the listed model and its thinking forced to on in the database, one real message was sent through the real `/telegram/webhook` inside the backend container, on the app database, through the eval `InProcessCompanion` (real repositories and the real `OpenRouterChatModel`, with a recording chat channel because fake chat IDs can't receive sends). The reply arrived. Model Call Log: `reply` on `deepseek/deepseek-v4-pro-0813` with thinking off (2957 in / 42 out), no errors.
  - Criterion 3 (models that can think behave as today): in the same message Safeguard, Understanding and Reply Plan ran on `deepseek/deepseek-v4.1-flash-1017` with thinking on, as saved. The seeded list is empty, and the existing settings and reply tests pass unchanged.
  - Criterion 4 (`/run`, worktree stack, signed in as an Admin in a real browser; `deepseek/deepseek-v4-pro-0813` was put in the list by SQL as the stand-in for a model that can't think, since every real model can):
    - List empty: on Response composition (flash) the switch was usable; switched on, saved, still on after a reload.
    - With pro in the list: picking pro switched thinking off and locked the switch (a click did nothing; screenshot looked at). After Save and a reload it was still off and locked, and the database held the model as pro and `response_thinking` false. Safeguard's switch (flash) stayed usable.
    - API: `PATCH /api/admin/settings` with `response_thinking: true`, sent from the signed-in browser, came back 422 with the message above.
    - Thinking forced to on in the database for that service: the card showed the switch off and locked, with nothing to save.
    - Picking flash again: the switch was usable and off; saved.
    - Pixel test: `AdminPrompts` PASS (0.11% differs, height 1392 vs 1392), run from a copy of `compare.cjs` that blocks Clerk's `protect.clerk.com` probes, which otherwise hang the test on this machine. The copy was deleted afterwards.
  - Criterion 5 (checks, on the final code; main had not moved, so no rebase was needed): `pytest` 2195 passed, `ruff check`, `ruff format --check` and `mypy src` clean; web `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean and `pnpm test` 963 passed.
  - Code review (standards and spec, two agents): no hard violations. Fixed from it: thinking came back on by itself after picking a model that can't think and then one that can; thinking already off was saved again (new "last saved"); a card with thinking wrongly saved on showed "Unsaved changes" on load; clearer names.
  - Caveats:
    - The locked switch has no words saying why. The design reference for Prompts & models has no such line, and new copy needs the reference changed first.
    - Eval Run Setting Overrides are still checked one key at a time, so a Variant can hold thinking on with a model that can't think. Its calls run with thinking off, and making it live is refused with the message above.
    - The Judge has its own model and thinking and does not use this rule (the issue covers core services).
    - Opus 5.5 and Fable 5.2 always think; their switch still does nothing, as noted in issue 08. Not changed here.
    - No real model that can't think was called, because the list has none. The check used a model that can think as the stand-in, so what OpenRouter does with `reasoning: {enabled: false}` for a model with no reasoning support was not seen.
    - The running-app message cost four small real DeepSeek calls.

## Completion

- Completed: 2026-11-25
- Commit: 74de51d (merge of openrouter-07-thinking-switch; work in 8b908f7 e82b243 1e20ce2)
