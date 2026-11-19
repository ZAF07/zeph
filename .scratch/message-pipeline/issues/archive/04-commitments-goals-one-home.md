# 04 — Commitments followed up, goals kept, one home per thing learned

Status: completed
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

- [x] The Life Thread keeping prompt asks for agreed commitments with dates and how they went, and says suggestions aren't commitments
- [x] The Curiosity keeping prompt asks for a commitment follow-up with a not-before day after it was due; a scripted answer with one is saved with that day
- [x] The memory processing prompt keeps goals shown plainly
- [x] Both prompts state the one-home rule
- [x] The Challenges description is updated only where it still matches the old seed
- [x] Prompt changes reach existing installs through a migration that only replaces prompts still matching the old seed
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 02 — One Day Summary per day, carrying feeling as well as facts (`.scratch/message-pipeline/issues/02-day-summaries.md`)

## Comments

### Run check, 19 Nov 2026 (worktree stack, copy of the main database)

- **Fresh install:** the worktree's own new database migrated to 0065. The three prompts hold the new text, and Challenges reads "What they find hard or keep running into: worries, struggles, setbacks."
- **Migration on real data:** main was at 0063. Its stored `life_thread_keeping_prompt` and `curiosity_keeping_prompt` equal the old seed word for word (checked against the texts in 0065). After `make db-copy` and a restart, `alembic_version` = 0065. All three prompts reloaded with the new text (one home, commitments, goals shown plainly), and Challenges dropped "patterns". The 9 Day Summaries from 0064 are still there.
- **Admin edits kept:** `test_the_migration_keeps_prompts_and_wording_an_admin_edited` shows edited prompts and an edited Challenges description survive the migration.
- **A real Conversation end** (the real model, the running scheduler; a Conversation inserted by SQL for the owner, since worktree fake chats stop at show_typing):
  - The User agreed to "call her tonight after dinner and say sorry". The Thread "Fight with mum and apology call" holds "They agreed to call her back on 19 Nov 2026 after dinner to say sorry for hanging up."
  - Zeph's suggestions that the User didn't take up were not kept as commitments. Journaling ("nah journaling isn't my thing") became a Preferences item. The running Thread says "Zeph suggested a short run this week; they said maybe, without making a firm commitment."
  - Follow-up Curiosity: "Did the call with your mum happen after dinner — how did it go?", `not_before` 2026-11-20 (the day after it was due), medium, linked to that Thread.
  - Goal shown plainly ("I really need to get back into running… a 10k by March") was kept in Goals: "They want to get back into running and aim to run a 10k by March, though they haven't gone for a run yet."
  - The Model Call Log shows `conversation_end`, `life_threads` and `curiosities` calls with no errors, each carrying the new prompt text.
- **A commitment done in the same Conversation** (after the review fix, prompt reloaded): the User said "I'll email him right now", then "done! sent it". The Thread "Landlord and broken boiler" records it with dates, and no follow-up Curiosity was made.
- **Users see commitments** in the Thread's story, which the Memories page already shows; no Dashboard code changed.
- **Checks** (after rebasing on main at 0b29457): `uv run pytest` 1357 passed; `ruff check`, `ruff format --check` and `mypy src` are clean. 0065 is the only migration on 0064.
- **Docs:** README steps a, b and d have "Built" notes. CONTEXT.md already described this (Memory Item, Memory Category, Life Thread, Curiosity), so it needed no change.

### Caveats / follow-ups for the owner

- The Curiosity keeping prompt still asks for a Curiosity about "a pattern you notice". This goes against "never made to check a Pattern" (README step d, CONTEXT Pattern). It is outside this issue, so I left it for issue 08 (Patterns kept). In the run, the model wrote one run Curiosity "more a pattern to watch than a plan to push".
- The Life Thread prompt says to start a Thread for a commitment when none fits, so a one-off promise can become its own small Thread.
- Code review: Standards found no rule breaks; I fixed its two naming points. From the Spec review I fixed "no follow-up for a commitment already done in the Conversation".

## Completion

- Completed: 2026-11-20
- Commit: `958ed8d` (merge into main): "Merge message pipeline issue 04: commitments the User agreed to go into their Life Thread with the day due and how they went (suggestions aren't commitments), each followed up by a Curiosity not before the day after; goals shown plainly kept in Goals; memory processing and Life Thread keeping prompts state one home per thing learned; Challenges drops patterns; migration 0065 reloads only prompts and wording still matching the old seed"
- Branch commits:
  - `690da13` "Commitments, goals, one home: Life Thread keeping keeps agreed commitments with their day and how they went; Curiosity keeping follows each up after its day; memory processing keeps goals shown plainly; both prompts state the one-home rule; Challenges drops patterns; migration 0065 reloads only unedited prompts and wording"
  - `f0c16c4` "Commitments review: no follow-up for a commitment already done in the Conversation; clearer test helper names"
  - `87f628b` "Commitments, goals, one home: issue 04 evidence recorded, completed and archived"
