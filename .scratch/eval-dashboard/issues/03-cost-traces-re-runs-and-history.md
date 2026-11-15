# 03 — Runs lane: cost control, full traces, single cases, Re-run failed and history

Status: in-progress

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

- [ ] Model Prices editable by Admins; seeded values as above; missing price shows "no price set" and never blocks a run
- [ ] Estimate shown before starting and is close to the run's real tokens
- [ ] A run over the token limit stops as Stopped over limit within one case
- [ ] Cancel stops within one case and keeps finished Case Results
- [ ] Every Case Result opens its full trace; the Model Call Log shows none of them
- [ ] Single cases can be run from the Dashboard and with `CASES=`
- [ ] Re-run failed runs only the Fail and Error cases
- [ ] Case history marks where the case or settings changed; deleting a run removes it and its traces
- [ ] Tests at the API, at "work the next Queued run", and Dashboard component tests
- [ ] Verified at `/run`; `make check-python` and `make check-web` pass

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
