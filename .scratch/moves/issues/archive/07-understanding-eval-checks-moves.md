# 07 — Understanding Eval checks lead and supporting Moves

Status: completed
Lane: A

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane B is changing some of the same files (Eval case shapes, Eval seed files, the Eval Dashboard pages). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

Admins can test how the Companion picks and does Moves.

- The Understanding Eval case shape gains per-Message `lead_move`, `support_move` (lists of allowed Moves) and `no_move`, editable on the Eval case pages (ADR-0014).
- Judge rules can check that the reply actually did the Move.
- A Variant's Setting Overrides can change a Move's text (not add or remove one), held to the same checks as a save; Make Live applies them through the same saves as the Moves page.
- Starter cases in the seed: the hosting chat (Research by the second or third Message, a Judge rule that the reply names real hosts under SGD 20 with managed Postgres), the internal-testing chat (Push or Plan steps), venting (no Push or Suggest), and Research with Web Search off (no Research, honest fallback).
- Evals cost money: remind the owner before any Eval Run.

## Acceptance criteria

- [x] New expectations pass and fail as expected (prior art: the Understanding Eval helper and Eval runner tests).
- [x] Move overrides apply inside a Variant only, and Make Live applies them.
- [x] Starter cases load from the seed and are editable on the Dashboard.
- [x] Backend and web checks pass.
- [x] `/run`: with the owner's go-ahead, one Eval Run of the hosting case shows its Case Result.

## Blocked by

- `.scratch/moves/issues/02-admins-manage-moves.md`

## Comments

### 2026-11-17 — plan (worktree `ai-chat-companion-moves-07`, branch `moves-07-understanding-eval-moves`)

- **Case shape.** Each Message's `expect` gains `lead_move` and `support_move` (lists of allowed Move names, compared ignoring case) and `no_move` (yes / no / unchecked: yes means no lead and no supporting Move; no means a lead Move). `no_move: true` together with a Move list is refused. The case gains `web_search` (on/off, default on; off turns Web Search off for the made-up User) and `web_results` (owner's choice: made-up results the Eval's stand-in search returns, each `title`, `url`, `text`; empty finds nothing as today).
- **Checks.** The Understanding's saved `lead_move` / `support_move` are checked; Judge rules on a Message already judge its reply, so "the reply did the Move" is a rule like any other.
- **Move overrides.** New override key `move:<id>` with name, when it fits and how to do it (needed Feature stays the live one), checked through the Move save, like Need overrides. Found gap: the Eval database gets the live Needs but the *seed* Moves, and no Need rule-outs. So the run's snapshot gains the live Moves (new `moves_snapshot` column, migration 0057), and the Eval database is filled with the Variant's Moves and each Need's live rule-outs. A Move deleted before the run makes its Variant an Error. Make Live saves Move overrides through the Move save and compares them for "changed since the run".
- **API / Dashboard.** Override choices and the run snapshot list Moves; the Variant editor gets a "Moves" group and Move fields; labels read "Move: Research".
- **Starter cases** in `understanding.yaml`: hosting chat (Research led by the third Message, canned host results, Judge rule names hosts under SGD 20 with managed Postgres and says where from), internal-testing (Push or Plan steps), venting (no Push or Suggest), Research with Web Search off (no Research, honest fallback rule).

### 2026-11-17 — done

Built as planned (see the plan above), with the owner's choice of made-up web pages for Eval searches. What changed:
- **Case shape and checks** (`core/evals/cases.py`, `case_shapes.py`, `understanding_checks.py`, `understanding_eval.py`): per-Message `lead_move`, `support_move` (ignoring case) and `no_move`; case `web_search` and `web_results`. A supporting Move alone isn't a lead. `no_move: true` with Move lists is refused at the field.
- **Eval web search** (`adapters/evals/stand_ins.py` `CannedWebSearch`, `in_process_companion.py`): every search finds the case's pages; reading a page gives its text; with none, nothing. `web_search: false` turns Web Search off for the made-up User as an Admin would.
- **Move overrides** (`core/evals/setting_overrides.py`): `move:<id>` with name, when it fits and how to do it, checked by the Move save (`MoveService.checked`); the needed Feature stays live. The run snapshot keeps the live Moves (migration 0057 `moves_snapshot`); the Eval database gets the Variant's Moves and each Need's live rule-outs (`environment.py`), where before it got the seed Moves and no live rule-outs. Make Live saves them through the Move save and compares them for "changed since the run".
- **API / Dashboard**: override choices and run snapshot list Moves; Variant editor has a Moves group (`MoveOverrideFields`); run page labels "Move: Research" with its text then and in the Variant.
- **Starter cases** (`seed/evals/cases/understanding.yaml`): `hosting-research` (the real chat's two messages and Zeph's shortlist questions as earlier lines, then Research must lead; canned host pages; Judge rule `names_hosts_under_budget`), `internal-testing-finish-line` (Push or Plan steps, `sets_a_finish_line`), `venting-is-not-pushed` (Be heard, `no_fixing`, `no_push`), `research-with-web-search-off` (`honest_no_lookup`), `small-talk-makes-no-move` (`no_move: true`).
- Docs: `CONTEXT.md` (Eval, Setting Override), ADR-0013 (the fake search finds a case's pages), `evals/README.md`.

Evidence per acceptance criterion:
- **New expectations pass and fail as expected**: `tests/test_understanding_eval_helpers.py` (`test_moves_are_read_and_a_move_expected_alongside_no_move_is_refused`, `test_the_moves_made_are_checked_ignoring_case`, `test_the_wrong_moves_or_a_move_when_none_was_expected_fail`, `test_a_supporting_move_without_a_lead_is_not_a_lead`); runner: `tests/test_eval_runner.py::test_an_understanding_case_checks_the_moves_and_searches_its_web_results`, `test_with_web_search_off_an_understanding_case_cannot_research`; Dashboard save points at `messages.0.expect.no_move` (`test_eval_cases.py`).
- **Move overrides apply inside a Variant only, and Make Live applies them**: tests `test_a_move_override_reaches_only_its_variant_and_live_moves_stay`, `test_a_run_uses_the_live_moves_and_each_needs_live_rule_outs`, `test_make_live_saves_a_move_override_and_keeps_its_needed_feature`, `test_a_move_changed_live_since_the_run_is_applied_only_if_confirmed`, `test_a_move_deleted_before_the_run_starts_makes_its_variant_an_error`; API refusals in `test_eval_runs.py`. `/run`: run `257c9c49` (Variant B changed Research's "how to do it" on the Dashboard): B's reply instructions held the new text, A's didn't (SQL on `eval_model_calls`). "Make Variant B live" on the run page showed "Applied: Move: Research"; the live Move's text changed and `needed_feature` stayed `web_search`.
- **Starter cases load from the seed and are editable on the Dashboard**: `test_the_understanding_cases_check_moves_and_web_search`, `test_every_seed_case_fits_its_eval_s_case_shape`. `/run` (Playwright, 3010): the Understanding tab lists all five; `hosting-research` shows the Web Search section (Railway page), Lead Move / Supporting Move / Makes no Move; duplicated to `hosting-run-check`, turned Web Search off and saved: DB row `web_search = false`, `edited = t`. No page errors.
- **Backend and web checks pass** (rebased on `origin/main` 084afad): ruff, ruff format, mypy (182 files) clean; pytest 1275 passed; eslint, prettier, tsc clean; vitest 483 passed.
- **`/run` Eval Run of the hosting case** (owner's go-ahead after the cost reminder):
  - Run `257c9c49`, A live and B Move override, S$0.0305: both Fail. The trace showed Zeph led with Research (support Suggest) on **Message 1**, searched the made-up pages twice and named hosts with prices; the case wrongly checked Message 3. Case rebuilt on the real chat (above).
  - Re-run `904dfc07` of the fixed case (owner's go-ahead), S$0.0061: **PASS**, 5 of 5. Lead move Research; Judge passed `names_hosts_under_budget` ("names Railway (USD 5/~SGD 7 with Postgres) and Render (USD 7/~SGD 9.50 plus Postgres from USD 6) … from their pricing pages, and doesn't punt back").

Code review (Standards and Spec, sub-agents):
- Fixed: `no_move: false` passed with only a supporting Move; the lead check said "made no Move" when a support was made; lead and supporting checks now share one helper; venting no longer forbids every Move (Judge rule `no_push` instead); Web Search off no longer forces a Suggest lead; `OverriddenThen` renamed `NeedsAndMovesAtRunStart`.
- Kept, as follow-ups if wanted: the need/move/setting key check repeats in a few places (follows the Need pattern); Move-to-row written in both the Eval environment and the snapshot repository; a Variant that swaps two Moves' names is refused (Needs behave the same).

## Completion

- Completed: 2026-11-17
- Commit: <to be filled in after merge>
