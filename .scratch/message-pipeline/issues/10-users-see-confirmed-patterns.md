# 10 — Users see their confirmed Patterns

Status: in-progress
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

- [ ] The user memory API returns confirmed Patterns with evidence and never suspected or closed ones
- [ ] Deleting a Pattern from the Dashboard removes it and rewrites the Portrait
- [ ] The Portrait keeping call is given confirmed Patterns only
- [ ] The Memories page shows the section, with its Copy slots editable on the Copy page
- [ ] Component tests cover the list, the empty state and delete
- [ ] `node design/compare.cjs Memories--tab-patterns M-Memories--tab-patterns` prints PASS
- [ ] The tab bar and empty state match the other `Memories*` files and `States`; full PASS (`node design/compare.cjs Memories M-Memories States`) if 16 is already in, otherwise the remaining differences are recorded under Comments
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 08 — Patterns kept at Conversation end (`.scratch/message-pipeline/issues/08-patterns-kept.md`)

## Comments

### Plan (20 Nov 2026, branch `message-pipeline-10-confirmed-patterns`)

- **When agreed:** Patterns have no "confirmed at" today (`last_offered_at` moves again if a confirmed Pattern is offered later). Add `patterns.confirmed_at`, set when the keeping step confirms one. Migration 0069 adds it (confirmed rows take their `last_offered_at`), and reloads the unedited `portrait_prompt` and `memories.hero.lead` from the seed.
- **API:** `GET /api/patterns` returns the User's confirmed Patterns, newest agreed first, each with its evidence newest first (day, Thread title, line). `DELETE /api/patterns/{id}` deletes a confirmed one (404 for suspected, closed or someone else's) and asks for the Portrait rewrite, like other deletions. Neither depends on User Memory being on.
- **Portrait:** `describe_user_memory` gets a "Patterns they agreed with" section, fed confirmed Patterns only; the prompt names it.
- **Dashboard:** `patterns` tab between `threads` and `helps`; `PatternsList` built from the existing Memories parts; Copy slots `memories.tabs.patterns`, `memories.patterns.{heading,lead,agreed,based_on,evidence_when,delete,empty_title,empty_body}`; hero line gets "the patterns it has noticed" only (16 is not in yet). Fixtures: Alex's two drawn Patterns.
