# 08 — Move Outcome Eval

Status: in-progress
Lane: B

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane A is changing some of the same files (Eval case shapes, Eval seed files, the Eval Dashboard pages). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

Admins can test whether the Companion learns the right lessons.

- A new Eval: Move Outcome. A case gives a made-up User and a finished Conversation (messages and the Moves each Understanding made) and expects certain Move Outcomes: which Moves, lead or support, result, and Judge rules on the situation, feeling and why (e.g. "says the User wanted options, not questions").
- It runs through the real Conversation-end keeping step with the Platform Settings Admins set, changed only by a Variant's Setting Overrides (ADR-0013, ADR-0014), and shows on the Eval pages like the other Evals.
- Starter cases in the seed: the hosting chat (Research helped, asking questions didn't), a Push that helped when frustrated, a Push that backfired when exhausted, and an outcome that must not judge the User.
- Evals cost money: remind the owner before any Eval Run.

## Acceptance criteria

- [ ] Move Outcome cases can be added, edited, duplicated and archived on the Dashboard, and run in an Eval Run with Case Results.
- [ ] Overrides of the Move Outcome keeping prompt, model and thinking apply inside a Variant only.
- [ ] Starter cases load from the seed.
- [ ] Eval runner tests (prior art: the Eval runner tests); backend and web checks pass.
- [ ] `/run`: with the owner's go-ahead, one Eval Run of the hosting case shows its Case Result.

## Blocked by

- `.scratch/moves/issues/04-move-outcomes-kept-and-shown.md`

## Comments

### 2026-11-17 — plan (worktree `ai-chat-companion-moves-08`, branch `moves-08-move-outcome-eval`)

- New Eval `move_outcome`. Case: `now`, `messages` (each `who`, `text`; a User line also has `need`, `lead_move`, `support_move`, `mood`), `outcomes` expected (each `move`, `role`, optional `result`, `rules`) and case `rules`.
- The check connects the made-up User, writes the finished Conversation and one Understanding per User line (with its Moves) into the Eval database, then runs the real `MoveOutcomeKeeper` (Conversation-end trace) through a new Eval app method. No reply calls, no summary, Threads or Portrait calls, so a case costs one keeping call plus the Judge.
- Each expected outcome: kept (same Move and role), its result, and Judge rules on the kept situation, feeling and why. Extra outcomes are listed, not failed.
- New Judge prompt "Move Outcomes prompt" (`outcome_instructions`) in `judge.yaml`; it seeds on start, no migration.
- Variant overrides of the keeping prompt, model and thinking already work (all editable settings); a runner test proves they reach only their Variant.
- Lane A (issue 06) edits Understanding case shapes; my changes are new blocks at the ends of `cases.py` and `case_shapes.py` to keep merges easy.
