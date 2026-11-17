# 07 — Understanding Eval checks lead and supporting Moves

Status: ready-for-agent
Lane: A

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane B is changing some of the same files (Eval case shapes, Eval seed files, the Eval Dashboard pages). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

Admins can test how the Companion picks and does Moves.

- The Understanding Eval case shape gains per-Message `lead_move`, `support_move` (lists of allowed Moves) and `no_move`, editable on the Eval case pages (ADR-0014).
- Judge rules can check that the reply actually did the Move.
- A Variant's Setting Overrides can change a Move's text (not add or remove one), held to the same checks as a save; Make Live applies them through the same saves as the Moves page.
- Starter cases in the seed: the hosting chat (Research by the second or third Message, a Judge rule that the reply names real hosts under SGD 20 with managed Postgres), the internal-testing chat (Push or Plan steps), venting (no Push or Suggest), and Research with Web Search off (no Research, honest fallback).
- Evals cost money: remind the owner before any Eval Run.

## Acceptance criteria

- [ ] New expectations pass and fail as expected (prior art: the Understanding Eval helper and Eval runner tests).
- [ ] Move overrides apply inside a Variant only, and Make Live applies them.
- [ ] Starter cases load from the seed and are editable on the Dashboard.
- [ ] Backend and web checks pass.
- [ ] `/run`: with the owner's go-ahead, one Eval Run of the hosting case shows its Case Result.

## Blocked by

- `.scratch/moves/issues/02-admins-manage-moves.md`
