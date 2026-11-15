# 02 — Foundation: Admins start Eval Runs from the Dashboard and watch Case Results come in

Status: ready-for-agent

## Parent

`.scratch/eval-dashboard/PRD.md` (decisions in `archive/01-run-evals-from-the-dashboard.md`, ADR-0013)

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

- [ ] An Admin starts a run of chosen Evals on the Dashboard; it goes Queued → Running → Finished and Case Results appear while it runs
- [ ] All six Evals run in the `eval-runner` with Pass/Fail/Error and the Judge's reasons where they have a Judge
- [ ] A runner restart mid-run leaves it Interrupted, never retried
- [ ] Made-up data is only in the Eval database; the app database's User tables and Model Call Log are untouched by a run (test)
- [ ] An Eval never uses the real chat channel or web search, and no Check-in runs on the Eval database
- [ ] Each run keeps its snapshot of settings, Judge settings and cases
- [ ] Terminal runs are hidden by default and shown with the toggle
- [ ] `make eval` queues a terminal run, prints results as they come, exits non-zero on Fail/Error; works in a worktree on its own stack
- [ ] Non-admins can't reach any Eval route or page
- [ ] Tests at the API and at "work the next Queued run" (scripted model), and Dashboard component tests
- [ ] One `make eval` run (remind the User first: evals cost money) is no worse than the last pytest run
- [ ] Screenshots approved by the User at `/run`
- [ ] `make check-python` and `make check-web` pass

## Blocked by

None - can start immediately. (Best after understanding issue 22, so the Judge moves with `deepseek-flash`; not required.)

## Comments
