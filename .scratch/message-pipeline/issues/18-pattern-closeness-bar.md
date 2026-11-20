# 18 — A closeness bar of its own for Patterns

Status: ready-for-agent
Lane: B
Blocked by: 14

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

Since 14, a Pattern comes to mind directly when it is at least as close in meaning as the **Life Thread closeness bar** (62) to what the User means and their latest texts. Patterns are worded in general terms ("when something grabs them, everything else goes quiet") while messages are concrete, so they score lower than Threads do: in 14's live run a clear fit scored 0.53 on the message alone and only got in at 0.626 once the Understanding's meaning was added.

Give Patterns their own Admin-editable **Pattern closeness bar**, starting at **52** (Zaf's choice, 20 Nov 2026). The Life Thread closeness bar goes back to being for Threads only. Linked recall (through a Thread in mind) is unchanged.

Measured with the real embedder on the message text alone (20 Nov 2026): messages that clearly fit a Pattern scored 0.47–0.66; unrelated ones 0.35–0.61. So at 52 some small talk will bring a Pattern to mind too; the Reply Plan still decides whether to use or offer it.

## Design

An ordinary field row with a hint in the Memory section of Platform settings, next to the Pattern push-back wait, as in the "Field rows" sample in `AdminPersona`. No new parts.

## Acceptance criteria

- [ ] Direct Pattern recall uses the new `pattern_closeness_percent` setting, not the Life Thread bar
- [ ] The Life Thread closeness bar no longer affects Patterns, and its hint no longer mentions them
- [ ] The new bar is Admin-editable with a hint, seeded at 52, and appears on existing installs without a migration
- [ ] `docs/message-pipeline/README.md` describes what was built
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 14 — Patterns come to mind in replies (done, `0db0f64`)

## Comments
