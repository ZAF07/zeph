# 04 — Commitments followed up, goals kept, one home per thing learned

Status: ready-for-agent
Lane: B
Blocked by: 02

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

Prompt and seed-text changes at Conversation end, no new storage:

- **Commitments:** the Life Thread keeping prompt adds a commitment the User agreed to ("I'll call mum tonight"; never one Zeph only suggested) to its Thread's story with its date, and later how it went once they say. The Curiosity keeping prompt makes a follow-up for each new commitment ("did you get to call your mum?"), not before the day after it was due.
- **Goals:** the memory processing prompt keeps goals the User shows plainly in the Goals category, not only ones said word for word.
- **One home:** the memory processing and Life Thread keeping prompts say a fact is a Memory Item, a story is a Life Thread, and what recurs across stories is left for Patterns (which come in 08). The seeded Challenges category description drops "patterns" (only if an Admin hasn't changed it).

Users see commitments in the Thread's story on the Memories page; the follow-up Curiosity stays hidden (ADR-0017).

User stories covered: 39, 40, 41, 42, 43, 44.

## Acceptance criteria

- [ ] The Life Thread keeping prompt asks for agreed commitments with dates and how they went, and says suggestions aren't commitments
- [ ] The Curiosity keeping prompt asks for a commitment follow-up with a not-before day after it was due; a scripted answer with one is saved with that day
- [ ] The memory processing prompt keeps goals shown plainly
- [ ] Both prompts state the one-home rule
- [ ] The Challenges description is updated only where it still matches the old seed
- [ ] Prompt changes reach existing installs through a migration that only replaces prompts still matching the old seed
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 02 — One Day Summary per day, carrying feeling as well as facts (`.scratch/message-pipeline/issues/02-day-summaries.md`)

## Comments
