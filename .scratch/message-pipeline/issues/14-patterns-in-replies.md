# 14 — Patterns come to mind in replies

Status: ready-for-agent
Lane: B
Blocked by: 07, 12

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

Patterns reach the Reply Plan through Recall: through their linked Threads when one comes to mind, and directly when what the User is saying is close to the Pattern in meaning, even about something new with no Thread yet. Like Threads, they stay in mind for the Conversation. The Reply Plan may build its Read on one and offer it aloud by 07's rules, as Zeph's view ("here's what I notice…"), never as fact. A suspected or confirmed Pattern can be offered; a closed one never is. One the User pushed back on waits an Admin-set time before it may be offered again. The Reply Plan records which Pattern it offered, so the keeping step (08) can confirm or close it from the User's reaction. Model Call Log shape: whether a Pattern was used or offered.

User stories covered: 24, 60.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- The push-back wait is an ordinary field row with a hint, as in the "Field rows" sample in `AdminPersona`. No new parts.
- **Model call trace** (reference `AdminModelCallTrace`): the Reply Plan step has a "Pattern" fact. The drawn values are "None" and "Used, not offered"; the value for an offered Pattern isn't drawn, so ask Zaf for it before building.
- **Shared reference.** `AdminModelCallTrace` also draws 05, 07, 09 and 11. Build your part. The full PASS is due on whichever of those issues lands last; until then, record under Comments which parts still differ and which issue owns them.

## Acceptance criteria

- [ ] A Pattern linked to a reminded Thread reaches the Reply Plan's input
- [ ] A Pattern close in meaning to a new message with no Thread reaches it too
- [ ] A closed Pattern never reaches it; a pushed-back one doesn't until the wait has passed
- [ ] A Pattern the Reply Plan offers reaches the Reply and is recorded as offered, and the next Conversation end's keeping call sees it was offered
- [ ] The push-back wait is Admin-editable with a hint
- [ ] The Model Call Log shows whether a Pattern was used or offered
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] The new field row matches the field-row sample in `AdminPersona`; the Pattern fact matches `AdminModelCallTrace` (full PASS if this is the last issue on it, otherwise the remaining differences are recorded under Comments)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 07 — Zeph forms a Read from the Outlook (`.scratch/message-pipeline/issues/07-read-from-the-outlook.md`)
- 12 — Wide recall (`.scratch/message-pipeline/issues/12-wide-recall.md`)

## Comments
