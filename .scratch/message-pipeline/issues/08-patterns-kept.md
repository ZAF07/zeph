# 08 — Patterns kept at Conversation end

Status: ready-for-agent
Lane: B
Blocked by: 06

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

New User Memory (ADR-0020). Nothing User-facing yet (10 shows them; 14 uses them in replies).

- **Storage:** per User: the pattern (a sentence or two); linked Life Threads; evidence entries (day, Thread, one self-contained line); state (suspected, confirmed, closed); when last offered and how the User took it (agreed, pushed back, brushed off); an embedding. No "how sure" score.
- **Keeping step** (new core service, own prompt, model and thinking switch, with hints), run after Life Threads at Conversation end: given the Threads the Conversation touched plus the User's other Threads closest in meaning (open or settled, however old, up to an Admin-set number), existing Patterns, and the days behind the evidence in play (up to an Admin-set number): messages while Message Retention keeps them, Day Summaries after. It may add evidence, start a suspected Pattern when the same way of thinking, feeling, acting or choosing shows up across two or more Threads (inferred values and goals included), and confirm or close one from how the User took a view Zeph offered in this Conversation (it judges from the transcript).
- No Curiosity is made to check a Pattern. While User Memory is off, nothing is started or changed.
- Delete My Data and Account Deletion remove all Patterns; Message Retention doesn't; deleting a linked Thread removes its link (and the Pattern if no evidence is left).
- **Admins** see only how many confirmed Patterns a User has. **Model Call Log:** a Pattern keeping step, no content for Users.

User stories covered: 23, 25, 26, 27, 30, 32, 55, 59, 65.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- **Users** (`/admin/users`, reference `AdminUsers`): the user panel lists "Confirmed Patterns" (a count only).
- **Prompts & models** (reference `AdminPrompts`): Pattern keeping is a core service, last in the list, with two limit rows, each with a hint.
- Fixture mode: Prompts & models lists four services in this order: Understanding, Reply Plan, Reply, Pattern keeping.
- **Shared references.** `AdminPrompts` also draws 05, 06 and 09. Build your part. The full PASS is due on whichever of those issues lands last; until then, record under Comments which parts still differ and which issue owns them. `AdminUsers` is yours alone.

## Acceptance criteria

- [ ] A Conversation touching two Threads that show the same way of acting leaves a suspected Pattern with evidence from both, when the scripted keeping answer says so
- [ ] The keeping call is given the touched and closest Threads (an old settled Thread close in meaning included) and the existing Patterns
- [ ] Days within retention reach the call as messages; older days as their Day Summaries
- [ ] A Pattern can be confirmed or closed by the keeping answer; a closed one is never changed back
- [ ] Nothing is kept while User Memory is off
- [ ] Delete My Data and Account Deletion remove all Patterns
- [ ] Prompt, model, thinking and the two limits are Admin-editable with hints; the Admin user view shows the confirmed count
- [ ] The Model Call Log shows the Pattern keeping step
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] `node design/compare.cjs AdminUsers` prints PASS
- [ ] The Pattern keeping card matches `AdminPrompts`; full PASS if this is the last issue on it, otherwise the remaining differences are recorded under Comments
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 06 — Every Admin field explains itself (`.scratch/message-pipeline/issues/06-admin-field-hints.md`)

## Comments
