# 03 — A Message waits for the User to finish, and starts over

Status: ready-for-agent
Lane: A
Blocked by: 01

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

People say one thing across several texts. Two changes:

- The Message wait (`message_wait_seconds`, Admin-set) gets a longer default: 15 seconds instead of 5.
- If a text arrives while a reply is being prepared and before any part of it has been sent, the reply in progress is dropped and the Message is answered again with every text in it. A Woven-in Check-in already saved for the dropped reply is taken back (the existing take-back path), so it stays due. Once any part of a reply has been sent, a new text starts the next Message, as today.

The Safeguard still checks each text as it arrives; a crisis gets the Crisis Reply at once and is never held back by the wait. This works inside the in-memory per-User queue (ADR-0018); no change to how many processes run. Update the **Message** term only if the code forces a wording change (it already describes this).

User stories covered: 1, 2, 3, 8.

## Acceptance criteria

- [ ] The default Message wait is 15 seconds for new installs and the setting's seed is updated
- [ ] A text arriving mid-write, before anything is sent, means one reply that answers every text, and no reply goes out for the dropped attempt
- [ ] A Woven-in Check-in saved for a dropped reply is taken back and stays due
- [ ] A text arriving after part of a reply has been sent starts the next Message
- [ ] A crisis text sent during the wait still gets the Crisis Reply at once
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 01 — Reply follows a strict priority order (`.scratch/message-pipeline/issues/01-reply-priority-order.md`)

## Comments
