# 08 — Move Outcome Eval

Status: completed
Lane: B

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane A is changing some of the same files (Eval case shapes, Eval seed files, the Eval Dashboard pages). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

Admins can test whether the Companion learns the right lessons.

- A new Eval: Move Outcome. A case gives a made-up User and a finished Conversation (messages and the Moves each Understanding made) and expects certain Move Outcomes: which Moves, lead or support, result, and Judge rules on the situation, feeling and why (e.g. "says the User wanted options, not questions").
- It runs through the real Conversation-end keeping step with the Platform Settings Admins set, changed only by a Variant's Setting Overrides (ADR-0013, ADR-0014), and shows on the Eval pages like the other Evals.
- Starter cases in the seed: the hosting chat (Research helped, asking questions didn't), a Push that helped when frustrated, a Push that backfired when exhausted, and an outcome that must not judge the User.
- Evals cost money: remind the owner before any Eval Run.

## Acceptance criteria

- [x] Move Outcome cases can be added, edited, duplicated and archived on the Dashboard, and run in an Eval Run with Case Results.
- [x] Overrides of the Move Outcome keeping prompt, model and thinking apply inside a Variant only.
- [x] Starter cases load from the seed.
- [x] Eval runner tests (prior art: the Eval runner tests); backend and web checks pass.
- [x] `/run`: with the owner's go-ahead, one Eval Run of the hosting case shows its Case Result.

## Blocked by

- `.scratch/moves/issues/04-move-outcomes-kept-and-shown.md`

## Comments

### 2026-11-17 — plan (worktree `ai-chat-companion-moves-08`, branch `moves-08-move-outcome-eval`)

- New Eval `move_outcome`. Case: `now`, `messages` (each `who`, `text`; a User line also has `need`, `lead_move`, `support_move`, `mood`), `outcomes` expected (each `move`, `role`, optional `result`, `rules`) and case `rules`.
- The check connects the made-up User, writes the finished Conversation and one Understanding per User line (with its Moves) into the Eval database, then runs the real `MoveOutcomeKeeper` (Conversation-end trace) through a new Eval app method. No reply calls, no summary, Threads or Portrait calls, so a case costs one keeping call plus the Judge.
- Each expected outcome: kept (same Move and role), its result, and Judge rules on the kept situation, feeling and why. Extra outcomes are listed, not failed.
- New Judge prompt "Move Outcomes prompt" (`outcome_instructions`) in `judge.yaml`; it seeds on start, no migration.
- Variant overrides of the keeping prompt, model and thinking already work (all editable settings); a runner test proves they reach only their Variant.
- Lane A (issue 06) edits Understanding case shapes; my changes are new blocks at the ends of `cases.py` and `case_shapes.py` to keep merges easy.

### 2026-11-17 — done

Built as planned (see the plan above). What changed:
- New Eval `move_outcome` (`core/evals/move_outcome_eval.py`; case shape in `case_shapes.py`, reader in `cases.py`). It saves the finished Conversation and one Understanding per User message (Need, lead and supporting Moves, mood) in the Eval database. It then runs the real `MoveOutcomeKeeper` through `EvalCompanion.keep_move_outcomes`, in a Conversation-end trace with the Eval database's Platform Settings.
- Each expected Move Outcome is checked three ways: it was kept (same Move and role), it has the expected result if one is given, and it passes Judge rules on the kept situation, feeling and why. Facts hold every outcome kept and the keeping call's time and tokens.
- New Judge prompt "Move Outcomes prompt" (`outcome_instructions` in `seed/evals/judge.yaml`). The seed adds missing Judge keys on start, so no migration was needed.
- Seed file `seed/evals/cases/move_outcome.yaml` has 4 starter cases: `hosting-research-helped`, `push-helped-when-frustrated`, `push-backfired-when-exhausted` and `outcome-does-not-judge`.
- Dashboard: the Eval name and label were added (`web/src/lib/api-client.ts`, `evals.ts`). The case form is drawn from the shape.
- Docs: `evals/README.md` and `CONTEXT.md` (Eval, Judge).

Evidence per acceptance criterion:
- Cases added, edited, duplicated, archived and run:
  - `tests/test_eval_cases.py::test_an_admin_adds_edits_duplicates_and_archives_a_case_of_every_eval[move_outcome]`.
  - The case's own checks point at the wrong field (Moves on a Zeph line, a User line with no Need, an expected Move no message made, an unknown rule): `test_an_eval_s_own_checks_point_at_the_field_that_is_wrong`.
  - Run with Case Results: `tests/test_eval_runner.py::test_a_move_outcome_case_keeps_outcomes_from_its_conversation_and_judges_them` and `test_a_move_outcome_not_kept_or_with_the_wrong_result_fails`.
  - `/run` in the browser: duplicated `hosting-research-helped` to `hosting-copy`, edited its first mood to "stressed" and saved, then archived it. The list shows "Archived · Edited · Changed by Run check", and the database row has `archived = t` and `mood = stressed`.
- Overrides of the keeping prompt, model and thinking apply inside a Variant only: `test_move_outcome_keeping_overrides_reach_only_their_variant`. Variant B's keeping call used the override prompt, `deepseek-pro` and thinking off. Variant A used the live `deepseek-flash` with thinking on. The live settings were unchanged.
- Starter cases load from the seed: `test_every_seed_case_fits_its_eval_s_case_shape`. `/run`: the Dashboard's Move Outcome tab lists all 4 as "From the seed files", and New run shows "Move Outcome · 4 cases".
- Tests and checks on the final rebased code (main with issue 06):
  - `ruff check`, `ruff format --check` and `mypy` clean (180 files); `pytest` 1253 passed.
  - Web: `pnpm lint`, `format:check` and `typecheck` clean; `pnpm test` 480 passed, including the new `NewEvalRunForm` test.
- `/run`, one Eval Run of the hosting case (the owner gave the go-ahead after the cost reminder):
  - `make eval CASES=hosting-research-helped` on the worktree stack (3010/8010), run `04a6273a`, finished: PASS, 6 of 6 checks and rules, 1,775 tokens in and 798 out, S$0.0019, 11.7 s.
  - Research (lead): kept, helped, and the Judge passed `wanted_options`.
  - Plan steps (lead): kept, didn't help, and the Judge passed `questions_handed_back` ("asking the person to name options pushed the work back onto them when they had no shortlist yet").
  - The run page shows the Case Result (Pass, tokens, S$0.0019) with no page errors.

Code review:
- Standards: no hard violations.
  - Fixed: the two Judge rule checks share one helper (`ask_about_rules`), and the test helper's parameter is now named `move_number`, with a docstring.
  - Kept: the Eval's own result words ("mixed" reads better than "had mixed results" in "expected X, kept Y"). Also kept: the keeping-step wiring in the Eval adapter, since adapters may build core classes.
- Spec:
  - Fixed: the keeping call's time and tokens are now kept in facts, and the override test now also changes the model.
  - Noted: each mood is saved at medium strength, because the case form has no strength field.

Caveats:
- Facts (the outcomes kept and the call's time and tokens) are stored, but the Dashboard doesn't show them, the same as other Evals. Failed cases note the outcomes kept and the Conversation.
- A case can't expect two outcomes for the same Move and role. That matches keeping, which writes one per Move and role.
- No migration. Shared files touched: `CONTEXT.md`, `evals/README.md` and `judge.yaml`.

## Completion

- Completed: 2026-11-17
- Commit: `24fedb0` — Moves issue 08: Move Outcome Eval
- Commit: `6e109f0` — Moves issue 08: review fixes
- Commit: `3a40d98` — Moves issue 08: CONTEXT.md says the Judge marks Move Outcome cases and what the Move Outcome Eval checks
