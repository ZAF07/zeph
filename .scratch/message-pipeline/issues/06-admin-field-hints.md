# 06 — Every Admin field explains itself

Status: ready-for-agent
Lane: B
Blocked by: 04

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

Every editable setting on the settings page (the Persona, each prompt, model, thinking switch, limit and wording), and every field on the Needs, Moves and Check-in Kinds pages, shows a short hint under its label: what it is, what it serves, and which step reads it and when. One or two sentences, not a manual. Example (for the Outlook, which arrives in 07): "How Zeph sees people and what helps them grow. Zeph forms its Read of each User from this before every reply. Plain prose."

The `hint` mechanism exists today but 64 of 76 settings have none. Hints describe the pipeline in `docs/message-pipeline/README.md` as it stands when this lands; settings added later by other issues bring their own hints. Admin page words that aren't Copy stay in code (ADR-0019).

User stories covered: 61.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- Every editable field has a hint under its label: 13px, soft, at most two sentences. An editor (prompt, Persona text) gets a label and hint above it.
- References: `AdminPrompts` (hint under Model, Thinking and every limit; a Prompt label and hint above each editor), `AdminPersona`, `AdminCheckInKinds`. Do not restyle anything else on a service card.
- Needs and Moves have no reference file: use the same hint style as `AdminCheckInKinds`.
- **Shared references.** `AdminPrompts` also draws 05, 08 and 09; `AdminPersona` also draws 07's tabs. Build your part. The full PASS is due on whichever of those issues lands last; until then, record under Comments which parts still differ and which issue owns them. `AdminCheckInKinds` is yours alone.

## Acceptance criteria

- [ ] Every editable setting returned by the Admin settings API has a non-empty hint
- [ ] The Needs, Moves and Check-in Kinds admin pages show a hint under each field
- [ ] Hints are at most two sentences and name the step that reads the setting
- [ ] A test fails if a new editable setting is added without a hint
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] `node design/compare.cjs AdminCheckInKinds` prints PASS (both widths, and `--all-folded`)
- [ ] Hints on `AdminPrompts` and `AdminPersona` match the reference (`node design/compare.cjs AdminPrompts AdminPersona`); full PASS if this is the last issue on them, otherwise the remaining differences are recorded under Comments
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 04 — Commitments followed up, goals kept, one home per thing learned (`.scratch/message-pipeline/issues/04-commitments-goals-one-home.md`)

## Comments
