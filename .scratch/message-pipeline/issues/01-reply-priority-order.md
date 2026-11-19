# 01 — Reply follows a strict priority order

Status: ready-for-agent
Lane: A
Blocked by: None - can start immediately

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

The Reply's instructions stop being a flat stack. They are put together in a fixed priority order, with a line telling the model that when two clash the higher one wins:

1. Safety, privacy and the User's own boundaries (e.g. a Thread they asked Zeph to drop).
2. What they just asked or need right now.
3. The Need, the Moves and the rest of today's guidance from the Understanding.
4. What was picked from memory, used accurately; nothing suspected stated as fact.
5. The Persona's voice (it stays in front of the instructions, as today; the order line says where it ranks).
6. Optional extras: a Woven-in Check-in, a Curiosity to raise, Knowledge passages, a sticker, a Shared Photo. Each is to be left out if it doesn't fit what the User needs right now.

The Woven-in Check-in is no longer phrased as an order ("Weave it into this reply"): it becomes an optional extra the reply may leave out. If the reply leaves it out, it is not logged as sent and stays due (it is taken back like a failed reply's). Everything else about the reply path stays as it is; the Reply Plan comes in 05.

This alone stops the review's worst moment: a "present-moment pause" Check-in overriding "give one short, real read".

User stories covered: 19, 20, 21.

## Acceptance criteria

- [ ] The Reply's instructions list their sections in the priority order above, with the clash rule stated once
- [ ] A due Woven-in Check-in reaches the Reply as an optional extra, never as an order
- [ ] A Woven-in Check-in the Reply leaves out is not logged as sent and stays due; one the Reply uses is logged as today
- [ ] A direct question in the Message is answered before any optional extra (tested through the instructions the scripted model receives)
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

None - can start immediately

## Comments
