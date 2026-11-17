# 05 — Move Outcomes guide the Understanding

Status: ready-for-agent
Lane: B

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane A is changing some of the same files (the seed settings file, the Understanding module). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

Zeph picks help that has worked for this User in moments like this one.

- Before each Understanding, find the User's own Move Outcomes closest in meaning to the incoming Message (with the Conversation so far), compared against each Move Outcome's situation and feeling through the existing Embedder port.
- Admins set how many reach the Understanding (starting at 3) and the closeness bar, as new Platform Settings on the settings page.
- The Understanding is shown them with their dates; the seed Understanding prompt says that a Move that helped before may not help now, depending on how the User feels.
- Move Outcomes are used while User Memory is off (that only stops learning).
- Look-ups are per User and indexed, for many Users at once.

## Acceptance criteria

- [ ] Only the User's own Move Outcomes, close enough and up to the Admin-set count, reach the Understanding.
- [ ] They still reach it with User Memory off.
- [ ] Admins change the count and closeness bar on the Dashboard.
- [ ] Webhook-seam tests with the fake embedder (prior art: the Life Thread and older Summaries tests); backend and web checks pass.
- [ ] `/run`: a User with a "Push backfired when exhausted" outcome who says they're exhausted gets an Understanding that sees it.

## Blocked by

- `.scratch/moves/issues/04-move-outcomes-kept-and-shown.md`
