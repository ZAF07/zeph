# 01 — Eval dashboard: Admins run and tune Evals from the Dashboard

Status: needs-triage

## Idea (from the User, during the Understanding grilling, 14 Nov 2026)

Admins should have a quick, easy way to run Evals on demand from the Dashboard and see the results visually, as they come in. They should also be able to adjust the test cases, prompts and anything else the real platform has, so humans can steer and check the Companion without a redeploy.

## Shape so far (not decided; grill first)

- **Test cases become Admin-managed data** (ADR-0004): editable on the Dashboard, seeded from files. Today they are Python in `evals/cases.py`.
- **Evals already use the live settings** (`CONTEXT.md`: each Eval "uses the platform settings Admins have set"), so a changed prompt, Need or model already affects the next run.
- **Draft settings:** a run can try a change before it goes live (a new prompt, Need or model), including side-by-side comparisons such as `deepseek-chat` vs `deepseek-reasoner`. This also covers the "try a stronger reply model" idea from `.scratch/understanding/issues/archive/01-understanding-before-reply.md`.
- **Runs in the background with live progress:** pick Evals, see a cost estimate first, then watch pass/fail per case, the Judge's reason, tokens and time.
- **A failed case opens its full-content trace** in the Model Call Log (ADR-0010: Eval runs keep full content).
- **Eval code moves into a core service**, so `make eval` and the Dashboard run the same thing.

## Open questions for the grilling

- How draft settings are kept apart from what real Users get.
- Where long runs execute (background jobs; see `.scratch/scaling/issues/01-run-more-than-one-backend.md`).
- Cost limits per run, and who may start one.
- How results are kept and compared over time.

## Depends on

- Model Call Log, from the Understanding PRD (`.scratch/understanding/`).
- The Understanding Eval writes its cases as data files, so they move here without a rewrite.

## Next

`/grill-with-docs`, then `/to-prd`.
