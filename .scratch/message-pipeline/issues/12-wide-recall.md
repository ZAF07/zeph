# 12 — Wide recall

Status: ready-for-agent
Lane: B
Blocked by: 05, 08

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

Recall stops starving the Reply Plan:

- It searches by meaning on what the Understanding says the User means plus a wider window of their recent texts (Admin-set; today it is 3).
- Whatever Threads pass the closeness bar come in, up to a high Admin-set cap (today it is 3).
- Threads that came to mind earlier in the Conversation stay in mind until it ends, so the start of a long Conversation still counts.
- The Reply Plan sees all of them and picks what the reply uses, so a wide memory never crowds the reply.

Hold-back rules (raised once per Conversation, brushed-off wait, asked to drop) apply as today.

User stories covered: 37, 38, 57.

## Acceptance criteria

- [ ] A Thread reminded by message 2 is still in the Reply Plan's input at message 20 of the same Conversation
- [ ] Recall's search uses the Understanding's meaning and the wider text window
- [ ] More than 3 Threads past the bar reach the Reply Plan, up to the cap
- [ ] Only Threads the Reply Plan picks reach the Reply
- [ ] The window and cap are Admin-editable with hints
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 05 — The Reply Plan takes over deciding; the Understanding only reads (`.scratch/message-pipeline/issues/05-reply-plan-takes-over-deciding.md`)
- 08 — Patterns kept at Conversation end (`.scratch/message-pipeline/issues/08-patterns-kept.md`)

## Comments
