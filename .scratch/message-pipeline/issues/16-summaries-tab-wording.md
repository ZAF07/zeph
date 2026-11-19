# 16 — Memories tab still says "Conversation Summaries" after the move to Day Summaries

Status: needs-triage
Type: bug
Blocked by: None (follows 02, already merged)

## Symptom

Issue 02 turned Conversation Summaries into **Day Summaries**: one per User per day. The Dashboard list already shows one entry per day. The wording Users see still describes the old model:

- The Memories tab is called "Conversation Summaries".
- Its heading is "Conversation Summaries".
- Its intro says "After each Conversation, Zeph writes a short note so it can pick up where you left off."
- The empty state says "No Conversation Summaries yet" and "They appear a little while after a Conversation ends."
- The Memories hero says "short summaries of past Conversations".
- The Delete My Data and Delete all memories texts say "Conversation Summaries … stay".

Expected: the wording matches the domain term (**Day Summary**, `CONTEXT.md`; "Conversation Summary" is on its _Avoid_ list) and says that each one is the account of a day, updated each time the User talks that day.

The wording was left alone in 02 on purpose, so the pixel-tested design (ADR 0018) wouldn't move. Nothing crashes; the UI is just out of date. The owner will revisit the exact wording.

## Repro

Deterministic. Open the Dashboard → Memories → the "Conversation Summaries" tab (`/memories?tab=summaries`).

## Suspected location

- Copy seed, `src/companion/seed/copy.yaml`: `memories.tabs.summaries`, `memories.summaries.heading`, `memories.summaries.lead`, `memories.summaries.empty_title`, `memories.summaries.empty_body`, the Memories hero description, and the Delete My Data / delete-all-memories texts that name Conversation Summaries. Changing seeded Copy needs a migration that reloads those slots (ADR 0019).
- Design references in `web/design/reference/` that show the old wording: `Memories.html`, `M-Memories.html`, `Memories--tab-summaries.html`, `Memories--tab-about.html`, `Memories--tab-helps.html`, `Memories--tab-photos.html`, `Memories--tab-threads.html`, `Account.html`, `M-Account.html` and `States.html`. They must change together with the Copy so `web/design/compare.cjs` still passes.
- Tests that assert the old text: `web/src/components/Memories.test.tsx`.

## Acceptance criteria

- [ ] The owner has chosen the new wording (tab title, heading, intro, empty state, and the delete texts that name it)
- [ ] The Copy seed and a migration reloading those slots use it; the design references are updated to match
- [ ] The bug no longer reproduces: the Memories tab and Account page show the new wording
- [ ] Tests cover the new wording (`Memories.test.tsx`, any Copy migration test)
- [ ] The pixel test passes (`web/design/compare.cjs`)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`, `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Comments
