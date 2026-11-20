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

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

The owner chose the wording on 20 Nov 2026 and the reference files already show it: tab "Day Summaries", heading, intro, hero line, empty state and the delete texts ("Day Summaries and your account stay. This can't be undone."). Take every string from the reference files, not from this issue.

- References: every `Memories*` file, `M-Memories`, `Account`, `M-Account`, `States`.
- **Hero line:** one Copy slot shared with 10. It also mentions "the patterns it has noticed". If 10 is already in, set it to the drawn text; if not, leave out the patterns part and 10 adds it.
- **Shared references.** Every `Memories*` file and `States` also draw 10's Patterns tab and empty state. The full PASS on those is due on whichever of 10 and 16 lands last; until then, record under Comments which parts still differ. `Account` and `M-Account` are yours alone.

## Acceptance criteria

- [x] The owner has chosen the new wording (tab title, heading, intro, empty state, and the delete texts that name it): it is in the reference files (20 Nov 2026)
- [ ] The Copy seed and a migration reloading those slots use the wording from the reference files
- [ ] The bug no longer reproduces: the Memories tab and Account page show the new wording
- [ ] Tests cover the new wording (`Memories.test.tsx`, any Copy migration test)
- [ ] `node design/compare.cjs Account M-Account` prints PASS; `Memories`, `M-Memories` and `States` pass in full if 10 is already in, otherwise the remaining differences are recorded under Comments
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`, `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Comments

### Note from issue 10 (20 Nov 2026)

Issue 10 is merged. The Patterns tab is in, and `memories.hero.lead` now reads "…what helps you, the patterns it has noticed, short summaries of past Conversations and the photos it kept. Delete anything you'd rather it forgot." Set it to the drawn text in full. Migration 0069 already reloaded the lead once (from the text before 10), so a migration here should match 10's text as the old seed. After 16, `node design/compare.cjs Memories M-Memories Memories--tab-patterns M-Memories--tab-patterns` should all PASS: with 16's hero line and "Day Summaries" tab name put into the fixtures, the Patterns tab gave 0.01% at both widths. `States` has no route in `routes.json`; issue 10 checked it with a scratch copy of `compare.cjs` pointing at `/design-preview/states` (0.03%).
