# 03 — Runs lane: cost control, full traces, single cases, Re-run failed and history

Status: completed

## Parent

`.scratch/eval-dashboard/PRD.md`

## What to build

Lane A (run pages). Runs in parallel with 04.

- **Model Prices:** a Platform Setting, SGD per 1M tokens in and out, per model. Seeded: `deepseek-flash` 0.38 / 1.54, `deepseek-v4-pro` 1.69 / 5.07 (DeepSeek peak, cache-miss price at 1 USD ≈ 1.28 SGD). A model with no price shows tokens only, marked "no price set".
- **Estimate** on New run before starting: tokens and SGD, from the last run of those cases; first-time cases use a rough per-Eval figure. Labelled "estimate".
- **Eval run token limit:** a Platform Setting (about 1,000,000). Crossing it ends the run Stopped over limit. Checked between cases (and between Messages in an Understanding case).
- **Cancel:** ends the run Cancelled, keeps finished cases.
- **Running totals** on the Run page and runs list: passes, tokens, SGD.
- **Full trace:** each case's model calls (full content) copied from the Eval database into Eval-only tables after the case; any Case Result opens them in the Model Call Log's trace view component. Never shown in the Model Call Log.
- **Single cases:** New run can open an Eval and tick single cases by key; `make eval` takes `CASES=...`.
- **Re-run failed** on a finished run: a new run of its Fail and Error cases.
- **History:** the Run page shows the run's snapshot (settings, Judge settings, cases as they were); a case page shows its pass/fail in recent runs, marked where the case or settings changed between them; an Admin can delete a run (its results and traces go with it).

## Acceptance criteria

- [x] Model Prices editable by Admins; seeded values as above; missing price shows "no price set" and never blocks a run (`/run`: seeded 0.38/1.54 and 1.69/5.07 on the Model Prices tab, saved and a 5-token limit refused with its message; `test_model_prices_are_seeded_and_admins_change_them_with_the_limit`, `test_a_run_is_priced_per_model_and_a_model_without_a_price_is_named` (run with no prices finishes, shows "deepseek-flash (no price set)"), `EvalCostsForm.test.tsx`)
- [x] Estimate shown before starting and is close to the run's real tokens (`/run`: 2 never-run Safeguard cases estimated 8,000 in / 800 out, real 7,129 / 625; next estimate used `traffic-killing-me`'s last run, 6,692 + 2 × 4,000 rough; `test_the_estimate_uses_each_cases_tokens_from_its_last_run`, `NewEvalRunForm.test.tsx`)
- [x] A run over the token limit stops as Stopped over limit within one case (`/run`, before and after rebase: limit 2,000, `curiosity-raised-once` stopped after 1 of 2 Messages, Error with that message, tokens kept; `test_a_run_over_its_token_limit_stops_after_the_case_that_crossed_it`, `test_an_understanding_case_stops_between_messages_once_over_the_limit`)
- [x] Cancel stops within one case and keeps finished Case Results (`/run`: Cancel pressed at 1 of 3, button showed Cancelling…, run ended Cancelled at 2 of 3 with both results; Queued run Cancelled at once in tests; `test_cancel_stops_a_running_run_after_its_case_and_keeps_finished_results`)
- [x] Every Case Result opens its full trace; the Model Call Log shows none of them (`/run`: Full trace pages with full content; full `make eval` saved 231 calls in `eval_model_calls`, app `model_calls` stayed 0; `test_every_case_result_opens_its_full_trace_kept_out_of_the_model_call_log`)
- [x] Single cases can be run from the Dashboard and with `CASES=` (`/run`: single-case runs from New run; `make eval CASES=traffic-killing-me` printed the case and exited 0; `test_a_run_of_single_cases_runs_only_those_and_unknown_keys_are_refused`, `test_the_terminal_runs_single_cases_and_prints_each_one`)
- [x] Re-run failed runs only the Fail and Error cases (`/run`: Re-run failed on the Stopped over limit run queued just `curiosity-raised-once`, which then passed; `test_re_run_failed_runs_only_the_fail_and_error_cases`, `test_re_run_failed_is_refused_when_nothing_failed`)
- [x] Case history marks where the case or settings changed; deleting a run removes it and its traces (`/run`: history of `traffic-killing-me` marked "1 setting changed"; deleting the cancelled run removed it, its 2 results and 6 trace calls; `test_case_history_marks_where_the_case_or_settings_changed`, `test_a_deleted_run_takes_its_results_and_traces_with_it`)
- [x] Tests at the API, at "work the next Queued run", and Dashboard component tests (`tests/test_eval_runs.py`, `tests/test_eval_runner.py`; `EvalRunView`, `NewEvalRunForm`, `EvalRunsList`, `CaseResultTraceView`, `CaseHistoryView`, `EvalCostsForm` tests)
- [x] Verified at `/run`; `make check-python` and `make check-web` pass (after rebase on issue 04: 1063 Python tests, 409 web tests, ruff, mypy, eslint, prettier, tsc all pass; `/run` repeated on a fresh worktree database after the rebase)

## Parallel work

04 runs at the same time. Pages, core modules and tables don't overlap. Both add a migration and touch the API client and admin nav: whoever rebases second renumbers their migration's parent and keeps both sides' entries.

## Blocked by

- `02-eval-runs-from-the-dashboard.md`
- `.scratch/understanding/issues/22-use-deepseek-flash-with-thinking-toggle.md` (so model names match the seeded prices)

## Comments

- 2026-11-15 (implementing, branch `eval-dashboard-03-cost-traces-history`): plan.
  - Schema (one migration): `eval_runs` gets `case_keys` (the cases picked, resolved when the run starts), `cancel_requested`, `token_limit`, `rerun_of`; `eval_case_results` gets `tokens_by_model`; new `eval_model_calls` (a Model Call Log row tied to a Case Result, no User; cascades with the run).
  - Model Prices (`model_prices`) and the Eval run token limit (`eval_run_token_limit`, 1,000,000) are Platform Settings, seeded; edited on one "Eval costs" page. SGD is priced from the run's settings snapshot, so later price changes don't rewrite old runs.
  - Tokens are counted per model (app and Judge), so each model is priced on its own.
  - Estimate: each case's tokens from its newest Case Result; a rough per-Eval figure on the live reply model for cases never run.
  - Cancel: a Queued run is Cancelled at once; a Running one is marked and the runner ends it Cancelled after the case it is on. Token limit and Cancel are checked after each case and between Messages of an Understanding case; a case stopped half-way is saved as an Error, so its tokens still count.
  - Re-run failed: on a run that has ended, a new run of its Fail and Error case keys.
  - History: snapshot read on demand on the Run page; case history at `/admin/evals/history/<key>` (not `/admin/evals/cases/...`, which issue 04 may use).
- 2026-11-15 (done):
  - Built as planned. After review: the "both prices or neither" rule moved into core; the case history ignores Model Prices and the token limit (they never change a result); a warning is logged if a case makes 500 traces or more.
  - Rebased on issue 04: migration renumbered to 0044 (parent 0043, 04's); checks take both the Judge settings and the stop check; 04's `EvalCaseRepository.get` and `EvalCaseNotFoundError` reused; Model Prices became a tab beside Runs, Cases and Judge.
  - Full `make eval` (User approved the cost): 68 of 70, 0 errors, 374,494 in / 45,924 out (about S$0.21). Fails were Persona reply flakes, `asks-for-tips` (bulleted list) and `struggling-asks-for-photo` (refused the photo); issue 02's run was also 68/70 with `asks-for-tips`, issue 22's 69/70. No reply code changed in this slice.
  - Known limits, left as they are: the trace has the app's calls, not the Judge's (its reasons are on the result); rough estimates count every never-run case on the live reply model; a Cancel pressed after the last case leaves the run Finished with the cancel flag set; Re-run failed works on any ended run, not only Finished; the `make eval` report prints tokens, not SGD.

## Completion

- Completed: 2026-11-15
- Commits (branch `eval-dashboard-03-cost-traces-history`):
  - `721c2f3` Eval dashboard issue 03: Model Prices, token limit, Cancel, traces, single cases, Re-run failed and history in the backend
  - `3265fcf` Eval dashboard issue 03: Dashboard estimate, single cases, Cancel, Re-run failed, delete, snapshot, full trace, case history and Model Prices pages
  - `7b4e499` Eval dashboard issue 03: cost under tokens in the runs list so it fits
  - `7f73e18` Eval dashboard issue 03: review fixes (price rule in core, history ignores prices and limit, CASES test, clearer names)
  - `9fb87ea` Eval dashboard issue 03: CONTEXT.md on Cancel and limit stops, traces and run pricing
- Archive commit: `9f06e9d` Eval dashboard issue 03 done: archive issue with run, eval, review and rebase evidence
- Merge commit: `b0dedbf` Merge eval dashboard issue 03 into main
