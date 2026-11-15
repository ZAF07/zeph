# 06 — Cancel pressed after the last case, and SGD in the `make eval` report

Status: completed

## Parent

`.scratch/eval-dashboard/issues/archive/03-cost-traces-re-runs-and-history.md` (two known limits left there)

## What to build

- **Cancel after the last case:** if an Admin presses Cancel after the runner's last stop check but before it ends the run, the run ends Finished with the cancel flag set, so the page goes from "Cancelling…" to "Finished". A run an Admin asked to cancel should end Cancelled, decided in the same step that ends it.
- **SGD in the terminal report:** `make eval` prints tokens but not cost. Add the run's SGD (at the prices it started with) and any models with no price set, as the Dashboard shows.

## Acceptance criteria

- [x] A run whose cancel was asked for ends Cancelled even when every case had finished (test) (`test_a_cancel_asked_for_after_the_last_case_still_ends_the_run_cancelled`, red then green; `/run` against the worktree's database: Running run, Cancel, then `end(FINISHED)` → `cancelled`)
- [x] The `make eval` report prints the run's SGD and names models with no price set (test) (`test_the_report_prints_the_runs_cost_and_models_with_no_price`, red then green; `/run`: `make eval CASES=traffic-killing-me` printed "Cost: S$0.0023, at the prices the run started with", exit 0)
- [x] Verified at `/run`; `make check-python` and `make check-web` pass (1089 Python tests, ruff, mypy; web checks pass)

## Blocked by

None

## Comments

- 2026-11-15 (done): `end` decides Cancelled vs Finished in one SQL statement from the run's cancel flag, so there's no gap. While editing, I briefly cut out issue 05's `mark_made_live`/`unmark_made_live` (they sit between `end` and `delete`); mypy caught it before any commit and they were restored as they were. No code review sub-agents for a diff this small; reviewed by hand.

## Completion

- Completed: 2026-11-15
- Commits (branch `eval-dashboard-06-cancel-and-terminal-cost`):
  - `2920bf1` Eval dashboard issue 06: a cancel asked for after the last case ends the run Cancelled; make eval prints the run's SGD
- Archive commit: `1f59f03` Eval dashboard issue 06 done: archive issue with test and run evidence
- Merge commit: `86aa793` Merge eval dashboard issue 06 into main
