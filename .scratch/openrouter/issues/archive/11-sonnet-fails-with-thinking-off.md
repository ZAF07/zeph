# 11 — Thinking switch locked on for a model that always thinks

Status: completed
Type: bug

## Parent

`.scratch/openrouter/PRD.md` (user story 5). Found on 2026-11-25, during the `/run` of issue 09. Widened by the operator on 2026-11-25 to cover the Dashboard.

## What happens

With a core service on `anthropic/claude-sonnet-5.5` and its thinking switch off, every call fails. OpenRouter answers 400: "Reasoning is mandatory for this endpoint and cannot be disabled." For the Reply (thinking is off by default) the User gets the "my thoughts got tangled" text instead of a reply.

With thinking on, the same call works.

Opus 5.5 and Fable 5.2 always think too. Issue 08 made their calls work by leaving the off instruction out in the adapter, but the Dashboard still shows a free switch, and "off" quietly does nothing for them.

## How to see it

Set `response_model` to `anthropic/claude-sonnet-5.5`, leave `response_thinking` off, and send a message. Or send one request with `reasoning: {enabled: false}` to that model.

## Cause

The model always thinks and refuses to be told not to. The adapter leaves the `reasoning` field out only for the names in `MODELS_THAT_ALWAYS_THINK` (`adapters/openrouter/chat_model.py`), and Sonnet 5.5 is not in it. Issue 08 said Sonnet accepts thinking off, but Sonnet was never called with thinking off until the issue 09 `/run`.

## What to build

The same as issues 07 and 10 did for a model that can't think, in reverse (operator's decision, 2026-11-25):

- A Platform Setting list of models that always think, kept beside `models_that_cannot_think`. A migration and the seed fill it with Sonnet 5.5, Opus 5.5 and Fable 5.2.
- In Prompts and models, the thinking switch for such a model is shown on and can't be turned off. Holding the mouse over it shows a pop-up saying why, like the "can't think" one. A screen reader is told the same.
- A service whose thinking is off when its model is changed to one that always thinks gets thinking saved as on. The API refuses to turn it off.
- A call for such a model is never told thinking is off, whatever is saved.
- The page at rest looks the same as today, so the design reference does not change.

## Acceptance criteria

- [x] A test that is red before the fix: a Sonnet 5.5 call with thinking off sends no `reasoning: {enabled: false}`
- [x] An Admin can't turn thinking off for a model that always thinks (Dashboard and API, tests)
- [x] Changing a service's model to one that always thinks saves its thinking as on (test)
- [x] Holding the mouse over the locked-on switch shows a pop-up saying the model always thinks; a screen reader is told the same (test)
- [x] A model that can think or not, and one that can't think, behave as today
- [x] Migration and seed list Sonnet 5.5, Opus 5.5 and Fable 5.2 as models that always think (migration test)
- [x] `/run`: the Reply on Sonnet 5.5 gets a reply; the switch is locked on with the pop-up in the browser at 1280 and 390; `AdminPrompts` still passes the pixel test
- [x] Check Haiku 5.5 with thinking off still works (it did in the issue 09 `/run`)
- [x] ADR-0028 and the deployment guide name Sonnet with Opus and Fable, and say the switch is locked on
- [x] The language's checks pass

## Open question for the implementer

- The adapter holds its own list (`MODELS_THAT_ALWAYS_THINK`). Decide whether the new Platform Setting replaces it or the service simply always passes thinking on for these models, so there is one list, not two.

## Comments

- 2026-11-25, operator: do the same as for models that can't think, in reverse. The switch defaults to on, is locked, and a hover pop-up says why.
- 2026-11-25, open question answered: the Platform Setting replaces the adapter's list, so there is one list. The core always asks for thinking on for a listed model; the adapter holds no model names and sends what it is told.
- 2026-11-25, in progress on branch `openrouter-11-always-think` (worktree `ai-chat-companion-openrouter-11`).
- 2026-11-25, done. Evidence:
  - Built:
    - Platform Setting `models_that_always_think` (Sonnet 5.5, Opus 5.5, Fable 5.2), in the seed and in migration 0099 (a list already saved is kept).
    - Calls (`thinking_for_model`, used by `thinking_to_use`): a listed model is always asked to think, whatever is saved. The two calls that name their own thinking follow the same rule: the Check-in "brought up" check and the Judge.
    - Saving (`with_thinking_fitted_to_the_models`): turning thinking off for a service on a listed model is refused with 422, e.g. "The Response composition thinking can't be off: anthropic/claude-sonnet-5.5 always thinks.", and nothing is saved. Changing a service to such a model while its thinking is saved off saves thinking as on.
    - API: `GET /api/admin/core-services` also returns `models_that_always_think`.
    - Dashboard (`CoreServiceCard`): while the chosen model always thinks the switch is on and locked, with the pop-up "This model always thinks, so thinking stays on." and the same words as the switch's description.
    - The adapter's `MODELS_THAT_ALWAYS_THINK` is gone. ADR-0028 and `docs/DEPLOYMENT_GUIDE.md` name Sonnet with Opus and Fable and say the switch is locked on.
  - Criterion 1 (red before the fix): on main, `build_request('anthropic/claude-sonnet-5.5', False, ...)` gave `'reasoning': {'enabled': False}`. Now `test_a_call_for_a_model_that_always_thinks_is_never_told_thinking_is_off` (a message through the webhook with Sonnet and thinking saved off) sees the call made with thinking on. Running app: see `/run`.
  - Criterion 2 (can't turn thinking off): `tests/test_thinking_stays_on_for_a_model_that_always_thinks.py` (refused with the model in the same save; refused when the saved model always thinks) and `PromptsAndModels.test.tsx` ("keeps the thinking switch on and locked for a model that always thinks", "shows thinking on when it is saved off for a model that always thinks"). Running app: see `/run`.
  - Criterion 3 (model change saves thinking on): `test_changing_to_a_model_that_always_thinks_saves_thinking_as_on` (other services untouched) and `test_thinking_already_on_is_not_saved_again_for_a_model_that_always_thinks`. Running app: after picking Sonnet and Save, the database held `response_model` Sonnet and `response_thinking` true.
  - Criterion 4 (pop-up and screen reader): the Dashboard test checks the tooltip's words and the switch's accessible description, and that both are gone for a free model. Running app: see `/run`.
  - Criterion 5 (others behave as today): the issue 07 tests pass unchanged; `test_a_model_that_can_think_or_not_follows_its_switch`, `test_thinking_can_be_turned_off_with_a_model_that_can_think_or_not`. Running app: Safeguard's switch (DeepSeek flash) was free with no pop-up; Haiku's switch was free and could be switched and saved.
  - Criterion 6 (migration and seed): `tests/test_models_that_always_think_migration.py` (the list is added and nothing else changes; a saved list is kept; the seed lists the three). Running app: the worktree database was at 0099 with the three names.
  - Criterion 7 (`/run`, worktree stack rebuilt on the final code, signed in as an Admin in a real browser):
    - The Reply on Sonnet: with `response_model` Sonnet and `response_thinking` forced to false by SQL (the case that failed), one real message went through the real `/telegram/webhook` inside the backend container, on the app database, through the eval `InProcessCompanion` (real repositories and the real `OpenRouterChatModel`, with a recording chat channel because fake chat IDs can't receive sends). A reply came back. Model Call Log: `reply` on `anthropic/claude-sonnet-5.5`, thinking on, 4040 in / 85 out, no error.
    - Switch at 1280: on Response composition (flash) the switch was off and free. Picking Sonnet turned it on and locked it; no pop-up until the mouse was over it, then "This model always thinks, so thinking stays on."; a click changed nothing; the pop-up went when the mouse left. After Save and a reload it was still on and locked. Screenshot looked at.
    - Switch at 390: on and locked, with the pop-up to the left of the switch covering nothing. Screenshot looked at.
    - API: `PATCH /api/admin/settings` with `response_thinking: false`, sent from the signed-in browser, came back 422 with the message above.
    - Pixel test: `AdminPrompts` PASS (0.11% differs, height 1392 vs 1392), from a copy of `compare.cjs` that blocks Clerk's `protect.clerk.com` probes; the copy was deleted afterwards.
  - Criterion 8 (Haiku with thinking off): in the same run, with `response_model` Haiku and thinking off, a second real message got a reply. Model Call Log: `reply` on `anthropic/claude-haiku-5.5`, thinking off, 4123 in / 134 out, no error.
  - Criterion 9 (docs): ADR-0028 (the "always think" consequence rewritten) and the deployment guide's model paragraph.
  - Criterion 10 (checks, on the final code; main had not moved, so no rebase was needed): `pytest` 2313 passed, `ruff check`, `ruff format --check` and `mypy` clean; web `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean and `pnpm test` 976 passed.
  - Code review (standards and spec, two agents): no caller can still send thinking off to a listed model. Fixed from it: a test for the "brought up" check on a model that always thinks; the rule renamed `thinking_for_model`; the card asks one pure function how a model locks thinking.
  - Caveats:
    - The adapter no longer protects Opus and Fable by itself. A future caller that skips `thinking_for_model` and asks a listed model for thinking off gets OpenRouter's 400. ADR-0028 says so.
    - A listed model's calls now say `reasoning: {enabled: true}` where Opus and Fable calls with thinking off used to leave the field out, and the Model Call Log shows thinking on for them.
    - The migration does not change a service already saved on a listed model with thinking off. Its calls think and the Dashboard shows the switch on; the saved value turns to on at the next save of that card's model.
    - The Judge's call is fitted, but its settings form still shows a free switch.
    - Picking a model that always thinks and then a free one, without saving, leaves the switch on (the reverse of issue 07). The card shows "Unsaved changes".
    - An Eval Run started before this change has no list in its snapshot, so its Judge calls would fail if it were still running when the new code starts.
    - Mouse only, as in issue 10: no pop-up on a phone or by keyboard. A screen reader still gets the words.
    - The design fixtures have no locked switch, so the pixel test does not cover the pop-up itself.
    - The running-app messages cost eight small real model calls.

## Completion

- Completed: 2026-11-25
- Commit: c336eab (merge of openrouter-11-always-think; work in 0858dac 5984b83 7499d72)
