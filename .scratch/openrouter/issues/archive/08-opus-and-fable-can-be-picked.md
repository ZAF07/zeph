# 08 — Opus 5.5 and Fable 5.2 can be picked

Status: completed
Blocked by: 05

## Parent

`.scratch/openrouter/PRD.md` (user story 1). Asked for by the operator on 2026-11-25, after issue 05.

## What to build

Admins can also pick `anthropic/claude-opus-5.5` and `anthropic/claude-fable-5.2` for any core service in Prompts and models. A migration adds both to the saved `available_models`, and their Model Prices (SGD per million tokens) to `model_prices`, the same way issue 05 added haiku and sonnet. The seed file gets the same additions. Every service stays on DeepSeek after this work.

## Acceptance criteria

- [x] Migration adds the two models to `available_models` and `model_prices`, keeping everything else (migration test)
- [x] Seed file matches
- [x] Quick check (the operator chose this over a full `/run` on 2026-11-25): one real call to each model through the adapter replies, paid with our own key
- [x] Thinking off works for both models: the adapter leaves the off instruction out (operator's decision, 2026-11-25; adapter tests and a real call)
- [x] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 05

## Comments

- 2026-11-25, status (branch `openrouter-08-opus-and-fable`, commit ec20517, not merged): migration `0093_opus_and_fable_can_be_picked.py`, seed and tests are written, and the affected tests pass. Prices: opus 5.12 in / 25.6 out, fable 10.24 in / 51.2 out (USD 4/20 and 8/40 at 1.28). The operator asked for a quick check only, not a full `/run`.
- 2026-11-25, **blocker found by the quick check.** One real call to each model through `OpenRouterChatModel`:
  - thinking on: both reply, `is_byok: true`.
  - thinking off: both fail with 400 "Reasoning is mandatory for this endpoint and cannot be disabled." The adapter sends `reasoning: {enabled: false}`; `effort: "none"` fails the same way. Leaving the `reasoning` field out, or `effort: "low"`, works (the model then thinks a little when it needs to).
  - So a service with thinking off (Response composition, Photo viewing, Knowledge "when it helps", Personal Sticker keeping today) would fail on every call if an Admin picked Opus 5.5 or Fable 5.2 for it. Haiku 5.5 and Sonnet 5.5 accept thinking off.
  - Waiting on the operator: how thinking off should be handled for a model that must think (related to issue 07, which covers the opposite case). Not merged until decided.
- 2026-11-25, operator's decision: the adapter leaves the off instruction out for these models.
- 2026-11-25, done. Evidence:
  - Migration `0093_opus_and_fable_can_be_picked.py` (renumbered after main's `0092_unmatched_patterns`): adds the two models and the price of each one it adds; a model an Admin already added is left as it is. Tests in `tests/test_opus_and_fable_migration.py` (added with everything else kept; already saved keeps place and price; saved with no price stays without; going back keeps them). The migration is the same code as 0091, which was run on an existing-install database in issue 05; 0093 itself was only run by the tests.
  - Seed: same two names and prices; the seed, settings, Eval cost and override-choice tests list all six models.
  - Adapter (`build_request` in `src/companion/adapters/openrouter/chat_model.py`, shared by the chat model and the photo viewer): for a model in `MODELS_THAT_ALWAYS_THINK`, the `reasoning` field is left out when thinking is off. Tests: `test_thinking_off_is_left_unsaid_for_a_model_that_always_thinks` (chat model, both models; photo viewer) and `test_thinking_on_is_still_said_for_a_model_that_always_thinks`. Other models still get `reasoning: {enabled: false}`.
  - Quick check, real calls through `OpenRouterChatModel` after the fix: Opus 5.5 and Fable 5.2 each replied with thinking off and with thinking on, all four on Anthropic with `is_byok: true` (`gen-1795537400-9Krge5kuX1Gg5bQQIaTs`, `gen-1795537401-1LizN5ps4MqUTbLumPYw`, `gen-1795537403-qBAFDCuLpYQ6caahQUCm`, `gen-1795537405-eWZr2XWmkzfndzzBkIRG`).
  - Checks after rebasing on main (0e112dc): `pytest` 2101 passed, `ruff`, `ruff format --check`, `mypy` clean. No `web/` files changed.
  - ADR-0028 and `docs/DEPLOYMENT_GUIDE.md` updated.
  - Caveats:
    - No `/run` in the Dashboard and no message through the webhook, by the operator's choice. Not checked for these two models in the running app: the picker showing them, a tool call, a photo.
    - No code review pass was run on this change.
    - The thinking switch does nothing for Opus and Fable: they think when they need to, so the Model Call Log can show reasoning (and reasoning tokens are paid for) with thinking off. Issue 07 could show this in the Dashboard.
    - The adapter now holds two model names. A new model that always thinks must be added to `MODELS_THAT_ALWAYS_THINK`, or its calls fail with thinking off.
    - These are costly models: Fable is about 27 times the DeepSeek flash price per token in, Opus about 13 times.

## Completion

- Completed: 2026-11-25
- Commit: 48424e0 (merge of openrouter-08-opus-and-fable; work in 5edc776 27fa09c a0a29ec 93900c7)
