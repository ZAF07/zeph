# 03 — Next Move in mind

Status: ready-for-agent
Lane: A

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane B is changing some of the same files (migrations, the seed settings file, the Understanding module). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

The Companion works through a sequence of Moves over a Conversation.

- Each Understanding may hold a next Move in mind, with why (e.g. "Next: Research, once I know their requirements"). It must be one the Need allows now or could plausibly allow later; an unknown Move is dropped.
- Understandings store the next Move and why. The Model Call Log shape shows the next Move's name.
- Each Understanding sees the earlier ones in the Conversation with their lead, supporting and next Moves, so it can follow the next Move or drop it when things change (e.g. the User reacted badly).
- The seed Understanding prompt explains the next Move.

## Acceptance criteria

- [ ] An Understanding's next Move and why are stored and shown to the next Understanding in the same Conversation.
- [ ] Earlier Moves are shown to later Understandings.
- [ ] The Model Call Log shows the next Move's name, no content.
- [ ] Webhook-seam tests (prior art: the Understanding tests); backend checks pass.
- [ ] `/run`: a multi-Message chat shows a next Move held and then made in a later reply.

## Blocked by

- `.scratch/moves/issues/01-moves-shape-replies.md`
