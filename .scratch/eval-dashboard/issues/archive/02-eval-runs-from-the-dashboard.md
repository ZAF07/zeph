# 02 — Foundation: Admins start Eval Runs from the Dashboard and watch Case Results come in

Status: completed

## Parent

`.scratch/eval-dashboard/archive/PRD.md` (decisions in `archive/01-run-evals-from-the-dashboard.md`, ADR-0013)

## What to build

An Admin opens the Eval area, ticks whole Evals, starts an Eval Run and watches Case Results appear as each case finishes. `make eval` starts the same kind of run from the terminal. Done by one agent before the two lanes start.

- The six Evals' checks and the Judge move from the pytest files into core, unchanged in what they check. The Judge's model and prompts stay as they are today (Admin-managed in 04).
- Eval Cases are seeded from `evals/cases/*.yaml` into the app database by key; the seed only adds missing keys. Read-only on the Dashboard for now.
- A new `eval-runner` Compose service (backend image) works one Queued run at a time against a separate Eval database, wiped and re-seeded at run start (ADR-0013). Always the fake chat channel and fake web search; no Check-in scheduler. Runs still Running when it starts are marked Interrupted.
- Eval Run, Case Result and the run snapshot (live Platform Settings, Judge settings, each case as it was) are saved in Eval-only tables in the app database, tied to the run, never to a User. Shape the Eval Run with one Variant (A) and try number 1 so 05 can add Variants and Repeats without reshaping it.
- Case Results: Pass, Fail or Error (with the error). The Judge's reason per rule, tokens and time. Errors don't count as fails; the run carries on.
- Dashboard: runs list (when, who, Dashboard/terminal, Evals, pass counts, tokens), New run (pick Evals), Run page that polls every 2 s while Queued or Running and stops when it ends. Built from the existing admin pages' look; send screenshots to the User at `/run` before the lanes copy the pattern.
- Runs list hides terminal runs by default, with a "Show terminal runs" toggle.
- `make eval` queues a run marked terminal on the local stack (`EVALS=...`), prints each case as it finishes, then the same report as today, and exits non-zero on any Fail or Error. A clear message when the stack isn't running. The pytest Evals are removed. `evals/README.md` updated.

## Acceptance criteria

- [x] An Admin starts a run of chosen Evals on the Dashboard; it goes Queued → Running → Finished and Case Results appear while it runs (`/run`: a Photo descriptions run went Queued → Running → Finished with its result appearing live; `tests/test_eval_runner.py::test_a_run_goes_from_queued_to_finished_with_a_result_per_case`)
- [x] All six Evals run in the `eval-runner` with Pass/Fail/Error and the Judge's reasons where they have a Judge (full `make eval` run in the stack: 70 cases, 68 Pass, 2 Fail, 0 Error, Judge reasons per rule; seam tests per Eval in `tests/test_eval_runner.py`)
- [x] A runner restart mid-run leaves it Interrupted, never retried (`docker compose restart eval-runner` mid Safeguard run → Interrupted with 10 results kept, runner idle after; `test_a_run_left_running_is_interrupted_at_start_up_and_never_retried`)
- [x] Made-up data is only in the Eval database; the app database's User tables and Model Call Log are untouched by a run (test) (`test_made_up_data_stays_in_the_eval_database_and_reaches_no_real_chat`)
- [x] An Eval never uses the real chat channel or web search, and no Check-in runs on the Eval database (`InProcessCompanion` always wires `RecordingChatChannel`, `NoWebSearch`, `IdleScheduler`; same test asserts nothing reached the app's chat channel)
- [x] Each run keeps its snapshot of settings, Judge settings and cases (`test_a_run_keeps_its_snapshot_of_settings_judge_and_cases`)
- [x] Terminal runs are hidden by default and shown with the toggle (`test_terminal_runs_are_hidden_unless_asked_for`, `EvalRunsList.test.tsx`; screenshot 7)
- [x] `make eval` queues a terminal run, prints results as they come, exits non-zero on Fail/Error; works in a worktree on its own stack (run in this worktree's own stack: progress lines, report, exit 2 on Fail; clear message when the stack is down)
- [x] Non-admins can't reach any Eval route or page (`test_only_admins_reach_the_eval_routes`; pages sit under the admin layout's `AdminGate`)
- [x] Tests at the API and at "work the next Queued run" (scripted model), and Dashboard component tests (`tests/test_eval_runs.py` 12, `tests/test_eval_runner.py` 9, `EvalRunsList`/`NewEvalRunForm`/`EvalRunView` tests)
- [x] One `make eval` run (remind the User first: evals cost money) is no worse than the last pytest run (User approved; full run 68/70 (Persona `asks-for-tips` and `struggling-with-shared-photos`); Persona rerun 8/9 with both passing and `are-you-human` failing on a Judge misread. Issue 18's one run was 70/70; issue 17's run on main the same day was 68/70 with two reply flakes, so within run-to-run variance)
- [x] Screenshots approved by the User at `/run` (User approved, 2026-11-15)
- [x] `make check-python` and `make check-web` pass (after rebase: 979 Python tests, 383 web tests, ruff, mypy, eslint, prettier, tsc all pass)

## Blocked by

None - can start immediately. (Best after understanding issue 22, so the Judge moves with `deepseek-flash`; not required.)

## Comments

- 2026-11-15 (implementing, branch `eval-dashboard-02-eval-runs`): built and verified except the full real `make eval` and screenshot approval.
  - Done: the six Evals' checks and the Judge moved into `core/evals/` (Judge unchanged, snapshotted with `judge_settings()`); issue 18's Persona/Settings changes ported. `eval-runner` service with its own Eval database (`<POSTGRES_DB>_eval`), always the recording chat channel, no web search, no scheduler. Eval tables in migration 0041 (0039/0040 taken by Understanding issue 18). Admin API at `/api/admin/evals` and `/api/admin/eval-runs`. Dashboard: Evals list (terminal toggle), New run, Run page polling every 2 s. `make eval` with `EVALS=`. The pytest Evals are gone; `evals/README.md` rewritten.
  - Decisions: `make eval` runs `python -m companion.eval_terminal` inside the backend container on the core Eval Runs service, instead of calling the admin API as a dev Admin (no Clerk token from the terminal); terminal runs have no Admin. Seed files moved to `src/companion/seed/evals/` (the Docker image only has `src`). Each Persona/Understanding case carries the text of the rules it names, so a case is self-contained. Understanding case `small-talk` renamed `dog-in-rain-boots`, since keys are unique across Evals and Persona has `small-talk`. Backend got a healthcheck so the runner starts after migrations.
  - Verified in the running worktree stack: 70 cases seeded; a Dashboard run of Photo descriptions went Queued → Running → Finished with its Case Result appearing live; `make eval EVALS=photo_descriptions` printed the case and report and exited non-zero on a Fail (the model leaked the test password that time; it passed the run before); restarting `eval-runner` mid-run left the run Interrupted with its 10 finished results, not retried; `make eval` with the runner stopped prints a clear message.
  - Open: one full `make eval` (costs money; blocked by the permission check, waiting for the User) to compare with issue 18's 70 of 70; User approval of the `/run` screenshots.
  - Known limits: a failure outside a case (e.g. wiping the Eval database) crashes the runner; Docker restarts it and the run is marked Interrupted.

## Completion

- Completed: 2026-11-15
- Commits (branch `eval-dashboard-02-eval-runs`):
  - `31de443` Eval dashboard issue 02: work in progress (core Eval runner, tables, adapters)
  - `61968d9` Eval dashboard issue 02: Evals move into core; Eval Runs API, runner and terminal client
  - `59416d4` Eval dashboard issue 02: eval-runner service, make eval through the stack, Dashboard Evals pages
  - `2ff4723` Eval dashboard issue 02: steadier health check, plural on the run page, photo leak noted
  - `d45217d` Eval dashboard issue 02: evals README for the runner; note on Understanding issue 17
  - `b1844c8` Eval dashboard issue 02: review fixes (start a run through a mutation, query key in one place, TSDoc, stop polling on load error, make eval checks backend too)
  - `9ab61b7` Eval dashboard issue 02: status note
  - `8faa0f7` Eval dashboard issue 02: CONTEXT.md says case keys are unique across Evals
- Archive commit: `98ea017` Eval dashboard issue 02 done: archive issue with run, eval and review evidence
- Merge commit: `d9aaf05` Merge eval dashboard issue 02 into main
