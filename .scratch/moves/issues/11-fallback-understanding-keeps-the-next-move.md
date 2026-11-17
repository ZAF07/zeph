# 11 — A fallback Understanding doesn't lose the next Move

Status: ready-for-agent
Lane: A

## Parent

`.scratch/moves/PRD.md` (follow-up to `.scratch/moves/issues/archive/06-unmade-next-move-becomes-a-curiosity.md`)

## What to build

When the Understanding model call fails or can't be read, the reply uses the fallback Understanding, which holds no next Move. If that happens on the last Message, the next Move held before it is lost at Conversation end, so the follow-up never becomes a Curiosity.

- Stored Understandings record whether they were the fallback.
- At Conversation end, Curiosity keeping is shown the next Move of the newest Understanding that wasn't the fallback.
- ADR-0016 says a fallback Understanding neither follows nor drops a next Move.

## Acceptance criteria

- [ ] A Conversation whose last Understanding is the fallback still passes the earlier unmade next Move to Curiosity keeping.
- [ ] A next Move made or dropped by a real Understanding is still not passed, even if a fallback follows it.
- [ ] Understandings store whether they were the fallback (migration; existing rows read as not fallback).
- [ ] Conversation-end-seam tests; backend checks pass.
- [ ] `/run`: a Conversation whose last Understanding is the fallback produces a Curiosity from the earlier next Move.

## Blocked by

- `.scratch/moves/issues/archive/06-unmade-next-move-becomes-a-curiosity.md` (done)
