# 01 — Answer texts sent in a row as one Message

Status: ready-for-agent

## Parent

Split out of the Understanding grilling (`.scratch/understanding/issues/archive/01-understanding-before-reply.md`, 14 Nov 2026). Blocks `.scratch/understanding/issues/04-understanding-call-with-seeded-needs.md`.

## What to build

People often send 2–3 short texts in a row. Today each text gets its own reply, one after another; only Albums are grouped. Make the **Message** (see `CONTEXT.md`) the unit the Companion answers: it waits a few seconds (Admin setting) after the last text, then answers everything sent before the pause with one reply, which may still go out as several short texts. Reuse the Album wait idea, and fold Albums into the same rule.

- The Safeguard still checks each text as it arrives, without waiting: a crisis gets the Crisis Reply straight away and the rest of the group isn't answered normally.
- A Message counts as one toward the Daily Message Limit, like an Album.
- A text that arrives while a reply is being written starts a new Message (answered after the current one), as the per-User order works today.
- The wait uses the existing Timer port; making it work across several backend processes stays in `.scratch/scaling/issues/01-run-more-than-one-backend.md`.

## Acceptance criteria

- [ ] Three texts sent within the wait get one reply, and the reply call sees all three as the latest Message
- [ ] A text after the wait starts a new Message
- [ ] The wait is an Admin setting on the Settings page, seeded with a sensible default
- [ ] A crisis text inside a group gets the Crisis Reply at once, not after the wait
- [ ] A grouped Message counts once toward the Daily Message Limit
- [ ] Albums still work as today (one reply, one count, first few photos looked at)
- [ ] Tests at the webhook seam with the fake timer; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [ ] `/run`: three texts posted to the worktree webhook in quick succession get one reply

## Blocked by

None - can start immediately.
