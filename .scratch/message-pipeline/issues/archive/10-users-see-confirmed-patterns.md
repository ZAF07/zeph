# 10 — Users see their confirmed Patterns

Status: completed
Lane: B
Blocked by: 08

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

The Memories page gets a section for the User's confirmed Patterns, each with its evidence (the days and lines that show it), each deletable. Suspected and closed Patterns never show. Deleting one removes it and rewrites the Portrait within a minute, as other memory deletions do. The User Portrait is rewritten from confirmed Patterns too, never suspected ones.

Its words are Copy slots in the Memories tab (ADR-0019): heading, line under it, empty state, delete button. The section works whether User Memory is on or off (Users can always see and delete).

User stories covered: 28, 29, 31.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- **Patterns tab** (`/memories?tab=patterns`, references `Memories--tab-patterns` and `M-Memories--tab-patterns`): a new tab between "What's going on" and "What helps you". Each confirmed Pattern shows its text, "You agreed with this on <day>", and "What it is based on": one line per evidence entry with day, Thread name and the line. Plus a delete button.
- **Empty state:** "Patterns, none confirmed" in `States`.
- **Copy:** the wording in these files is the wording to seed: Patterns heading, the line under it, the empty state title and body, and the delete button's label.
- **Tab bar and hero line:** every `Memories*` file now shows the Patterns tab, and the hero line mentions "the patterns it has noticed". The hero line is one Copy slot shared with 16: if 16 is already in, set it to the drawn text; if not, add only the patterns part and leave the rest to 16.
- **Fixtures:** Alex has the two Patterns drawn.
- **Shared references.** Every `Memories*` file and `States` also draw 16's wording. Build your part. The full PASS is due on whichever of 10 and 16 lands last; until then, record under Comments which parts still differ.

## Acceptance criteria

- [x] The user memory API returns confirmed Patterns with evidence and never suspected or closed ones
- [x] Deleting a Pattern from the Dashboard removes it and rewrites the Portrait
- [x] The Portrait keeping call is given confirmed Patterns only
- [x] The Memories page shows the section, with its Copy slots editable on the Copy page
- [x] Component tests cover the list, the empty state and delete
- [x] `node design/compare.cjs Memories--tab-patterns M-Memories--tab-patterns` prints PASS — `PASS Memories--tab-patterns 0.25%`; `M-Memories--tab-patterns` is 0.58% (FAIL) only from 16's hero words; with 16's two drawn texts in place both print PASS at 0.01% (see Evidence)
- [x] The tab bar and empty state match the other `Memories*` files and `States`; full PASS (`node design/compare.cjs Memories M-Memories States`) if 16 is already in, otherwise the remaining differences are recorded under Comments
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 08 — Patterns kept at Conversation end (`.scratch/message-pipeline/issues/08-patterns-kept.md`)

## Comments

### Plan (20 Nov 2026, branch `message-pipeline-10-confirmed-patterns`)

- **When agreed:** Patterns have no "confirmed at" today (`last_offered_at` moves again if a confirmed Pattern is offered later). Add `patterns.confirmed_at`, set when the keeping step confirms one. Migration 0069 adds it (confirmed rows take their `last_offered_at`), and reloads the unedited `portrait_prompt` and `memories.hero.lead` from the seed.
- **API:** `GET /api/patterns` returns the User's confirmed Patterns, newest agreed first, each with its evidence newest first (day, Thread title, line). `DELETE /api/patterns/{id}` deletes a confirmed one (404 for suspected, closed or someone else's) and asks for the Portrait rewrite, like other deletions. Neither depends on User Memory being on.
- **Portrait:** `describe_user_memory` gets a "Patterns they agreed with" section, fed confirmed Patterns only; the prompt names it.
- **Dashboard:** `patterns` tab between `threads` and `helps`; `PatternsList` built from the existing Memories parts; Copy slots `memories.tabs.patterns`, `memories.patterns.{heading,lead,agreed,based_on,evidence_when,delete,empty_title,empty_body}`; hero line gets "the patterns it has noticed" only (16 is not in yet). Fixtures: Alex's two drawn Patterns.

### Evidence (20 Nov 2026, rebased on `main` at 2f7af62)

1. **API: confirmed only, with evidence.** `tests/test_patterns_dashboard.py`: confirmed Patterns newest agreed first, each with evidence newest day first (`day`, `thread`, `line`); suspected and closed never returned; a suspected or someone else's Pattern can't be deleted (404); list and delete work with User Memory off. Running app (worktree stack, real Postgres): with one confirmed, one suspected and one closed Pattern inserted for a run-check User, `/memories?tab=patterns` showed only the confirmed one; after review, two confirmed (agreed 15 Nov and 9 Nov, the older one updated more recently) showed newest agreed first, the suspected one hidden.
2. **Delete from the Dashboard rewrites the Portrait.** Playwright clicked "Delete pattern: Treats rest…": `204 /api/patterns/22222222-…01`, the empty state "No patterns yet" showed, the row and its evidence were gone (suspected and closed rows untouched), `user_portraits.rewrite_requested_at` was set, and about 45 s later the scheduler wrote a new Portrait with no trace of the deleted Pattern ("No patterns have been confirmed yet"). Test: `test_deleting_a_pattern_removes_it_and_rewrites_the_portrait_without_it`.
3. **Portrait given confirmed Patterns only.** `describe_user_memory` gets a "Patterns they agreed with" section from `PatternRepository.list_confirmed`; `test_the_portrait_is_written_from_confirmed_patterns_only` checks the confirmed one is in and the suspected and closed ones are not; `portrait_prompt` names them.
4. **When agreed.** `patterns.confirmed_at`, set the first time the keeping step confirms a Pattern (new or existing), kept when it is offered again: `test_agreeing_with_a_pattern_records_the_day_and_a_later_reaction_keeps_it`, `test_a_new_pattern_agreed_with_at_once_is_dated_and_agreeing_again_keeps_the_day`.
5. **Copy slots editable.** Admin Copy page, Memories tab, lists `Tabs: Patterns` and the eight `Patterns tab: …` slots; editing the heading to "Patterns you agreed with" and saving made `/api/copy` return it; set back to "Patterns" after.
6. **Component tests.** `Memories.test.tsx`: the list (text, "You agreed with this on 12 Nov", "What it is based on", "12 Nov · Pushing hard at work"), delete, failed delete, empty state, User Memory off, `?tab=patterns`, and every word from Copy on the tab, with and without Patterns.
7. **Pixel test** (fixture dev server, `STATE_USER` session): `PASS Memories--tab-patterns 0.25%, height 1089 vs 1089`; `FAIL M-Memories--tab-patterns 0.58%, height 1603 vs 1603`, the diff only in the hero line's end. With 16's two drawn texts put in the fixture Copy for one run (then restored): `PASS Memories--tab-patterns 0.01%`, `PASS M-Memories--tab-patterns 0.01%`, `PASS Memories--tab-helps 0.00%`, `PASS M-Memories 0.27%`. `States` has no route in `routes.json`, so it ran on a scratch copy of `compare.cjs` with `/design-preview/states` added: `PASS States 0.03%, height 2218 vs 2218` with the new "Patterns, none confirmed" sample.
8. **Still different until 16 lands** (16 owns them): the hero line ends "short summaries of past Conversations" where every `Memories*` file draws "a short account of each day you talked", and the tab reads "Conversation Summaries" where they draw "Day Summaries". As run today: `Memories--tab-summaries` 0.71% and `M-Memories` 0.91% FAIL, the other Memories tabs PASS at 0.25–0.35%. The full `Memories M-Memories States` PASS is due with 16.
9. **Migration.** 0069 (`down_revision` 0068) is the only head after rebasing on main. It adds `confirmed_at` (confirmed rows take `last_offered_at`, else `updated_at`) and reloads `portrait_prompt` and `memories.hero.lead` only where still on the old seed: `test_the_migration_reloads_…`, `test_the_migration_keeps_…`, `test_the_migration_dates_confirmed_patterns_…`. Applied on the worktree stack: `alembic_version` 0069, the column present, the new prompt and hero line served.
10. **Docs.** `CONTEXT.md` (Pattern: the day agreed, the Patterns tab, delete rewrites the Portrait; User Portrait: deleting a Pattern rewrites it) and `docs/message-pipeline/README.md` (Built notes under c. Patterns and f. User Portrait, the prompt tables).
11. **Checks** (after rebase): `uv run pytest` 1415 passed; `uv run ruff check .` All checks passed; `uv run ruff format --check .` 544 files already formatted; `uv run mypy src` no issues in 198 files. `pnpm lint` clean, `pnpm format:check` clean, `pnpm typecheck` clean, `pnpm test` 130 files, 879 tests passed; `pnpm build` compiled.
12. **Review** (`/code-review`, two axes): no hard violations or spec gaps. Fixed: the confirmed filter is one SQL method (`list_confirmed`) used by the API and the Portrait; the `confirmed_at` fallback lives in one place; `MemoryCard` padding; a test for a Pattern agreed with at once. Kept: the Portrait prompt says "recent days", which is what the call is given.

## Completion

- Completed: 2026-11-20
- Commit: <to be filled in after the merge>
