# 03 — Check-ins run in their own loop

Status: needs-triage

> **Owner: run `/grill-with-docs` before picking this up.** See `.scratch/check-in-job/PRD.md` for the findings and options. Open question for the grill: does Woven-in Check-in timing rely on Conversation ending and Check-ins running in the same tick, in that order?

## Parent

`.scratch/check-in-job/PRD.md`

## What to build

Deciding on Check-ins moves out of the shared scheduler tick into its own loop. A slow batch of Check-ins then no longer delays ending quiet Conversations, processing them, rewriting Portraits or the tidy-up work, and the reverse is also true. Shutdown stops waiting on a long Check-in batch: it finishes the User in hand and leaves the rest due for next time.

## Acceptance criteria

- [ ] Quiet Conversations still end on time while a slow Check-in batch is running.
- [ ] Stopping the backend mid-batch doesn't wait for the whole batch; Users not yet decided stay due.
- [ ] Tests cover both loops running and stopping.
- [ ] A `/run` with a slowed-down Check-in model shows Conversations ending while Check-ins are still being decided.

## Blocked by

None - can start immediately

## Comments
