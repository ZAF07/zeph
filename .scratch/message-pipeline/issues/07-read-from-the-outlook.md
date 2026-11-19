# 07 — Zeph forms a Read from the Outlook

Status: ready-for-agent
Lane: A
Blocked by: 05

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

The heart of the review: Zeph stops only mirroring.

- **Outlook:** the Persona becomes two Admin-editable texts: its voice (today's Persona text) and its Outlook (new, plain prose, seeded with a starting text the owner can rewrite). The Outlook goes only into the Reply Plan's instructions; the voice stays in front of the Reply and Check-ins sent on their own. Both show on the settings page with hints.
- **Read:** the Reply Plan always forms a Read (Zeph's honest view of what is really going on, from the Outlook, the Understanding and memory) and decides whether to say it now: only when there is room (not mid-vent, in crisis or light chat; a vent is heard first, the Read comes once it is spent), it is worth saying (it adds something the User hasn't said) and it isn't a repeat (never the same Read twice in a Conversation). When the User asks for Zeph's view, it gives its deepest Read at once, not advice already given. The Read is offered as Zeph's view, never as fact.
- **Where we are:** the Reply Plan writes one line on where the Conversation is now ("venting, nearly spent", "asking for a view"); each Reply Plan sees the earlier ones.
- The Reply gets the Read at priority level 3 when it is to be said. Admins' own traces show the Read in full; the Model Call Log shape records only whether one was formed and said.

User stories covered: 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 22, 51, 52, 53, 63.

## Acceptance criteria

- [ ] The Outlook is an Admin-editable setting with a hint, seeded, and a change applies from the next reply
- [ ] The Outlook reaches the Reply Plan's instructions and no other call; the voice still reaches the Reply
- [ ] Every Reply Plan carries a Read and whether to say it; a Read to be said reaches the Reply at level 3, one not to be said doesn't reach it
- [ ] The Reply Plan prompt states the three conditions and the when-asked rule
- [ ] Each Reply Plan writes a where-we-are line and earlier Reply Plans in the Conversation are in its input
- [ ] The Model Call Log records whether a Read was formed and said; an Admin's own trace shows its text
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 05 — The Reply Plan takes over deciding; the Understanding only reads (`.scratch/message-pipeline/issues/05-reply-plan-takes-over-deciding.md`)

## Comments
