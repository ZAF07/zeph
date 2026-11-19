# 09 — Woven-in Check-ins decided by the Reply Plan

Status: ready-for-agent
Lane: A
Blocked by: 07

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

The separate Woven-in Check-in model call is retired. When a Check-in is due mid-Conversation, the Reply Plan is given the due Check-in Kinds without fixed behaviour and weighs one against everything else the reply could do: it chooses whether a Woven-in Check-in fits now, which Kind, and a note, or none. It is never woven in while the User is struggling, nor while paused unless an Admin asked with Check in Now (keep these as code rules).

Everything else about Woven-in Check-ins works as today: saved, logged as sent with its Kind and marked woven in (and the Admin for Check in Now), moving the Due Time, taken back when the reply fails or (from 01 and 03) leaves it out or is dropped, going out on its own if no reply weaves it in before the Conversation ends. The `woven_check_in_prompt` setting is removed by migration. Check-ins sent on their own keep their own decision and prompt.

User stories covered: 19, 20, 64.

## Acceptance criteria

- [ ] No separate woven-in Check-in model call is made; the Reply Plan's input holds the due Kinds when one is due and nothing when none is
- [ ] A Reply Plan choosing a Kind makes a Woven-in Check-in that reaches the Reply as an optional extra and is logged as today
- [ ] Struggling, paused and Check in Now rules still hold
- [ ] The woven-in Check-in prompt is gone from the settings page and the database
- [ ] Existing Woven-in Check-in tests pass, rewritten for the Reply Plan where they scripted the old model
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 07 — Zeph forms a Read from the Outlook (`.scratch/message-pipeline/issues/07-read-from-the-outlook.md`)

## Comments
