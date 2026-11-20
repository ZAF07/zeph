# 15 — Day Summary Eval

Status: ready-for-agent
Lane: B
Blocked by: 02

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

A new Eval (Evals run in their own service, ADR-0013; each case shape checks, saves and draws its form, ADR-0014). A Day Summary case gives a made-up day of messages and a set of questions with expected answers about the facts, the feelings and what Zeph offered and how it landed. The Eval writes the Day Summary with the real memory processing prompt, then the Judge answers each question from the Summary alone and checks it against the expected answer, giving a reason. A case passes only if every answer matches. Seed a few starting cases (e.g. a guilt-and-job-worry day like the 19 Nov review). Admins add and edit cases on the Dashboard like other Evals.

Evals cost money: build and test with the fake model; don't run a real Eval Run without the owner.

User stories covered: 66, 69.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- **Case form** (`/admin/evals/cases/day_summary/new`, reference `AdminEvalDaySummaryCase`): Key, The day (messages with From, Time, Text; Remove and "Add a message"), Questions (Question and Expected answer; Remove and "Add a question"), then "Add case". Editing a saved case drops the Key panel and the button reads "Save case".
- **A result on a run:** the Summary written, then each question with Expected, the Judge's answer, Match or Miss, and the Judge's reason, as in "How a result reads, on a run".
- **Fixtures:** the new case form opens filled in as drawn.

## Acceptance criteria

- [ ] Day Summary cases can be created, edited, duplicated and archived on the Dashboard
- [ ] A run writes the Summary with the live (or overridden) memory processing prompt and the Judge answers from the Summary only
- [ ] A case fails when any answer misses, with the Judge's reason shown
- [ ] Starting cases are seeded
- [ ] Eval runner, case and Dashboard tests pass with the fake model
- [ ] `node design/compare.cjs AdminEvalDaySummaryCase` prints PASS, and a run's result page reads as the drawn sample
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 02 — One Day Summary per day, carrying feeling as well as facts (`.scratch/message-pipeline/issues/02-day-summaries.md`)

## Comments
