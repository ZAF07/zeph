# 06 — Unmade next Move becomes a Curiosity

Status: ready-for-agent
Lane: A

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane B is changing some of the same files (the seed settings file, the Conversation-end work). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

A follow-up the Companion meant to make comes back naturally later.

- When a Conversation ends with a next Move it had in mind but never made, Curiosity keeping is shown that next Move and why, and may turn it into a Curiosity (e.g. "did they decide what 'done' means for internal testing?").
- From there it works like any Curiosity: raised in a later chat or a Curiosity Check-in. No other state carries across Conversations.
- The seed Curiosity keeping prompt explains this.

## Acceptance criteria

- [ ] Curiosity keeping receives an unmade next Move and its why; a made one isn't passed.
- [ ] Nothing is passed while the Curiosities Feature doesn't work or User Memory is off (the existing rules).
- [ ] Conversation-end-seam tests (prior art: the Curiosity tests); backend checks pass.
- [ ] `/run`: a Conversation that ends with an unmade next Move produces a matching Curiosity.

## Blocked by

- `.scratch/moves/issues/03-next-move-in-mind.md`
