# 10 — Users see their confirmed Patterns

Status: ready-for-agent
Lane: B
Blocked by: 08

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

The Memories page gets a section for the User's confirmed Patterns, each with its evidence (the days and lines that show it), each deletable. Suspected and closed Patterns never show. Deleting one removes it and rewrites the Portrait within a minute, as other memory deletions do. The User Portrait is rewritten from confirmed Patterns too, never suspected ones.

Its words are Copy slots in the Memories tab (ADR-0019): heading, line under it, empty state, delete button. The section works whether User Memory is on or off (Users can always see and delete). Build it against the design folder and the pixel test (ADR-0018 UI; read `web/design/README.md` first). If the design has no Patterns section yet, follow the existing Life Threads tab's look and say so in the issue comments.

User stories covered: 28, 29, 31.

## Acceptance criteria

- [ ] The user memory API returns confirmed Patterns with evidence and never suspected or closed ones
- [ ] Deleting a Pattern from the Dashboard removes it and rewrites the Portrait
- [ ] The Portrait keeping call is given confirmed Patterns only
- [ ] The Memories page shows the section, with its Copy slots editable on the Copy page
- [ ] Component tests cover the list, the empty state and delete
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 08 — Patterns kept at Conversation end (`.scratch/message-pipeline/issues/08-patterns-kept.md`)

## Comments
