# 29 — Find out why 8 Understanding Eval cases fail

Status: ready-for-agent
Track: shared
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md`. Findings from `20-findings-for-the-owner.md` (section 02: "8 Understanding Eval cases fail, cause unknown" and "An Eval case that can't pass reliably"), triaged with the owner on 25 Nov 2026.

## Why

The whole Understanding Eval on main after issue 02 passed 22 of 30. There is no run from before issues 01 and 02, and both reloaded `reply_plan_prompt`. So a regression in how Zeph picks Needs and Moves, or weaves in Check-ins, may be on main unnoticed. More prompt changes have landed since (0086, 0100), so the longer this waits the harder it is to find.

The failing cases:

- `strong-mood-unknown-cause`
- `knowledge-for-a-reflective-question`
- `no-knowledge-for-a-vent`
- `check-in-not-now-while-asking-for-help`
- `internal-testing-finish-line`
- `small-talk-makes-no-move`
- `next-move-held-then-made`
- `guess-checked-gently`

## What to do

Evals cost money: show the owner the estimate and get a go-ahead before each run. Run only these cases (`make eval CASES=...`), never the whole Evals.

1. Run the 8 cases twice each on main as it was before issue 01's merge (2ffa403) and twice each on main now. About S$0.20.
2. Sort each case into: got worse (a real regression), always failed (a bad case or an old fault), or flaky (passes some tries).
3. `guess-checked-gently` can't pass as written: the "one question per reply" rule from issue 01 drops Get curious when the guess's Curiosity is asked. Change its expectation (for example "Curiosity raised" instead of "lead Move Get curious") and run it once.
4. Fix a regression in this issue when the fix is small and clear. Otherwise file one issue per regression and link it here.
5. A prompt change must not overwrite Admin edits: use issue 28's helper if it is merged.

Use a worktree for the old commit; don't switch branches in the main folder.

## Acceptance criteria

- [ ] Each of the 8 cases was run twice before issue 01 and twice on main now, with the Eval Run IDs and costs in Comments
- [ ] Each case is listed as got worse, always failed or flaky, with the reason
- [ ] `guess-checked-gently` has an expectation it can meet and passed a run
- [ ] Every real regression is fixed here or has its own issue
- [ ] The owner was shown the estimate before each run

## Comments
