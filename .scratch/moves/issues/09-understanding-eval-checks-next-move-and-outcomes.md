# 09 — Understanding Eval checks next Move and Move Outcomes

Status: ready-for-agent
Lane: whichever lane is free first

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** This issue goes to whichever lane finishes first; set `Status: claimed` before starting so the other agent doesn't take it too. Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both sides' changes when resolving conflicts.

## What to build

Admins can test the sequence and the learning in the Understanding.

- The Understanding Eval case shape gains per-Message `next_move` and made-up `move_outcomes` in the case's User Memory, editable on the Eval case pages.
- Starter cases in the seed: a Conversation that should hold a next Move and then make it; a User with "Push backfired when exhausted" who is exhausted (no Push); the same User frustrated about a slipped Goal, with "Push helped when frustrated" (Push allowed).
- Evals cost money: remind the owner before any Eval Run.

## Acceptance criteria

- [ ] `next_move` and `move_outcomes` work in cases and pass and fail as expected (prior art: the Understanding Eval helper tests).
- [ ] Starter cases load from the seed and are editable on the Dashboard.
- [ ] Backend and web checks pass.
- [ ] `/run`: with the owner's go-ahead, one Eval Run of the backfired-Push case shows its Case Result.

## Blocked by

- `.scratch/moves/issues/03-next-move-in-mind.md`
- `.scratch/moves/issues/05-move-outcomes-guide-the-understanding.md`
- `.scratch/moves/issues/07-understanding-eval-checks-moves.md`
