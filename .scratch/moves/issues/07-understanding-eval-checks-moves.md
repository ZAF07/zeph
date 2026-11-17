# 07 — Understanding Eval checks lead and supporting Moves

Status: claimed
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

## Comments

### 2026-11-17 — plan (worktree `ai-chat-companion-moves-07`, branch `moves-07-understanding-eval-moves`)

- **Case shape.** Each Message's `expect` gains `lead_move` and `support_move` (lists of allowed Move names, compared ignoring case) and `no_move` (yes / no / unchecked: yes means no lead and no supporting Move; no means a lead Move). `no_move: true` together with a Move list is refused. The case gains `web_search` (on/off, default on; off turns Web Search off for the made-up User) and `web_results` (owner's choice: made-up results the Eval's stand-in search returns, each `title`, `url`, `text`; empty finds nothing as today).
- **Checks.** The Understanding's saved `lead_move` / `support_move` are checked; Judge rules on a Message already judge its reply, so "the reply did the Move" is a rule like any other.
- **Move overrides.** New override key `move:<id>` with name, when it fits and how to do it (needed Feature stays the live one), checked through the Move save, like Need overrides. Found gap: the Eval database gets the live Needs but the *seed* Moves, and no Need rule-outs. So the run's snapshot gains the live Moves (new `moves_snapshot` column, migration 0057), and the Eval database is filled with the Variant's Moves and each Need's live rule-outs. A Move deleted before the run makes its Variant an Error. Make Live saves Move overrides through the Move save and compares them for "changed since the run".
- **API / Dashboard.** Override choices and the run snapshot list Moves; the Variant editor gets a "Moves" group and Move fields; labels read "Move: Research".
- **Starter cases** in `understanding.yaml`: hosting chat (Research led by the third Message, canned host results, Judge rule names hosts under SGD 20 with managed Postgres and says where from), internal-testing (Push or Plan steps), venting (no Push or Suggest), Research with Web Search off (no Research, honest fallback rule).
