# 13 — Evals split into Understanding and Reply Plan checks

Status: ready-for-agent
Lane: A
Blocked by: 09

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

The Understanding Eval today checks reading and deciding together. Split its checks between the two steps: the Understanding's (said / read / unclear, struggling, cause known, look-ups) and the Reply Plan's (Need, Moves, Threads brought up or left alone, Curiosities, ask-why, Knowledge, Woven-in Check-in, the Read formed and whether it is said). Existing cases are kept; their expectations move to the step that now owns them, and a seed never overwrites an edited case (as today). Variants' Setting Overrides cover the Reply Plan prompt and the Outlook.

Evals cost money: build and test with the fake model; don't run a real Eval Run without the owner.

User stories covered: 67, 68.

## Acceptance criteria

- [ ] Each existing Understanding case runs and is marked on the step that owns each expectation
- [ ] Reply Plan checks include whether a Read was formed and said
- [ ] Setting Overrides accept the Reply Plan prompt and the Outlook
- [ ] Eval runner and case tests pass with the fake model
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 09 — Woven-in Check-ins decided by the Reply Plan (`.scratch/message-pipeline/issues/09-check-ins-decided-by-reply-plan.md`)

## Comments
