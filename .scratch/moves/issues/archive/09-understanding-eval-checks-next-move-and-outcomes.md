# 09 — Understanding Eval checks next Move and Move Outcomes

Status: completed
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

- [x] `next_move` and `move_outcomes` work in cases and pass and fail as expected (prior art: the Understanding Eval helper tests).
- [x] Starter cases load from the seed and are editable on the Dashboard.
- [x] Backend and web checks pass.
- [x] `/run`: with the owner's go-ahead, one Eval Run of the backfired-Push case shows its Case Result.

## Blocked by

- `.scratch/moves/issues/03-next-move-in-mind.md`
- `.scratch/moves/issues/05-move-outcomes-guide-the-understanding.md`
- `.scratch/moves/issues/07-understanding-eval-checks-moves.md`

## Comments

### 2026-11-17 — done (worktree `ai-chat-companion-moves-09`, branch `moves-09-eval-next-move-outcomes`)

What changed:
- **Case shape and checks** (`core/evals/cases.py`, `case_shapes.py`, `understanding_checks.py`, `understanding_eval.py`): each Message's `expect` gains `next_move` (the Moves Zeph may have in mind next, ignoring case; "has Research in mind next" / "has no next Move in mind, expected …"). The case's `memory` gains `move_outcomes` (`move`, `role`, `situation`, `feeling`, `result`, `why`, `days_ago`). On the Eval case pages: "Next Move in mind" under each Message, and a "Move Outcomes" list in Made-up User Memory. The Move role field and result choices are shared with the Move Outcome case shape.
- **Made-up Move Outcomes** (`core/evals/made_up_memory.py`): saved through the Move Outcome repository, embedded in one call with the same situation-and-feeling text as the keeping step (`text_to_embed`, pulled out of `core/move_outcomes.py`), so the real finder finds them by closeness.
- **Starter cases** (`seed/evals/cases/understanding.yaml`): `next-move-held-then-made` (Message 1 holds Research next; Message 2, with the requirements, leads with Research and names hosts), `no-push-when-exhausted` (Arjun, 1am, with "Push didn't help when exhausted" and "Push helped when frustrated"; Judge rule `no_push_while_exhausted`, where telling them to rest is fine), `push-when-frustrated` (same User and outcomes, fed up about the slipped launch; lead Push or Plan steps, rule `pushes_for_one_step`). Keys differ from the Move Outcome Eval's `push-*` cases, since keys are unique across Evals.
- Docs: `evals/README.md`, `CONTEXT.md` (Eval).

Evidence per acceptance criterion:
- **`next_move` and `move_outcomes` work in cases and pass and fail as expected**: `tests/test_understanding_eval_helpers.py` (`test_a_next_move_and_made_up_move_outcomes_are_read`, `test_the_next_move_in_mind_is_checked_ignoring_case` with pass, wrong Move and none); runner `tests/test_eval_runner.py::test_an_understanding_case_gives_its_move_outcomes_and_checks_the_next_move` (the made-up outcome reaches the Understanding with its date, next Move check passes); a bad result is refused at `memory.move_outcomes.0.result` (`test_eval_cases.py`).
- **Starter cases load from the seed and are editable on the Dashboard**: `test_the_understanding_cases_check_the_next_move_and_move_outcomes`, `test_every_seed_case_fits_its_eval_and_keys_are_unique`. `/run` (Playwright, 3010): all three rows in `eval_cases` after start-up; `no-push-when-exhausted` shows the Move Outcomes section (Push, Lead, situation, Didn't help, …) and "Next Move in mind"; changed a Move Outcome's Why and saved: "Saved.", DB row `edited = t` with the new text (then put back). Re-checked after the review fixes: both outcomes and their choices show, no page errors.
- **Backend and web checks pass**: ruff, ruff format, mypy (181 files) clean; pytest 1280 passed (then 163 passed on the Eval and Move Outcome files after the review fixes; the run's exit 1 is Docker timing out removing the test container afterwards, with other stacks running); eslint, prettier, tsc clean; vitest 483 passed. Final run after the rebase is in the Completion notes.
- **`/run` Eval Run of the backfired-Push case** (owner's go-ahead after the cost reminder):
  - Run `64edcc17`: Fail. Both made-up Move Outcomes reached the Understanding with the real embedder, the exhausted one first ("1 Nov 2026: Push (lead) didn't help. … Felt: exhausted, drained."). It picked Be heard, no lead Move, next Move Mirror. The reply said "it doesn't need to be solved now", and the reused venting rule `no_push` failed that as a suggestion. Case fixed: own rule `no_push_while_exhausted`, and `now` 01:00 to match the "it's 1am" message.
  - Re-run `2fe8566b` (owner's go-ahead), S$0.0038: **PASS**, 2 of 2. Judge: "Zeph explicitly says the bug and launch can wait and tells them to sleep, not to keep working." The run page shows the Case Result (Pass, 6,127 in / 970 out).

Code review (Standards and Spec, sub-agents):
- Fixed: shared Move role field and result choices; made-up Move Outcomes embedded in one call; runner test builds its outcome from named parts.
- Kept, as follow-ups if wanted: "no Push" is checked only by the Judge (the case shape can't say "any Move but Push"; the real run made no Move); nothing stops `next-move-held-then-made` Message 1 from already leading with Research (its next-Move check would then likely fail); `push-when-frustrated` requires a Push or Plan steps lead and a Judge rule, stricter than "Push allowed", so it tests that the past outcome is used.

## Completion

- Completed: 2026-11-17
- Final checks after rebasing on `origin/main` 7ad0eed (issue 10's merge): ruff, ruff format, mypy (181 files) clean; pytest 1284 passed; eslint, prettier, tsc clean; vitest 483 passed.
- Commits (branch `moves-09-eval-next-move-outcomes`):
  - `ea1e8d2` Moves issue 09: Understanding Eval checks next Move and Move Outcomes
  - `34d634e` Moves issue 09: review fixes
  - `19df4e1` Moves issue 09 done: archive issue with check and run evidence
- Merge into `main`: `4bb14b4` Merge Moves issue 09: Understanding Eval checks next Move and Move Outcomes
