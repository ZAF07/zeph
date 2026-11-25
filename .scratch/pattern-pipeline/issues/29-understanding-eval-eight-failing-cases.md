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

### 25 Nov 2026: run, sorted and fixed

**Answer: no case got worse because of issues 01 and 02.** No regression in how Zeph picks Needs and Moves or weaves in Check-ins was found. One case (`guess-checked-gently`) could not pass after issue 01 because the case was out of date; it is fixed here. Six cases fail often for reasons that were already there before issue 01; they are in the new issue `33-understanding-eval-cases-that-fail-for-old-reasons.md`.

**How it was run**

- "Before": a second worktree at 2ffa403 with its own stack and a fresh database, so the prompts and cases were that commit's seed. "Now": this worktree at main a5dfb998, the same way.
- The 8 cases' seed text is the same in both commits.
- One difference that could not be avoided: the old commit has no OpenRouter, so "before" called DeepSeek directly (`deepseek-flash`) and "now" calls it through OpenRouter (`deepseek/deepseek-v4.1-flash-1017`). Same model, same prices (S$0.38 in, S$1.54 out per 1M tokens).

**The owner and the estimates.** Before any run the owner was shown the stack's own estimate: about S$0.055 per run of the 8 cases, S$0.22 for the four runs, and S$0.01 for the one-case re-run. The owner said yes, with a cap of S$0.50 in total for follow-up runs of single cases without asking again. The 8 extra Check-in runs and 3 extra `guess-checked-gently` runs below were made under that cap, not shown one by one. Total spent: **S$0.33**.

**Eval Runs** (cost worked out from each run's tokens at the prices above)

| Run | Stack | Cases | Passed | Tokens in / out | Cost |
| --- | --- | --- | --- | --- | --- |
| `6d5bccee-2443-41c7-b9cd-8b40dc76a828` | before | the 8 | 3 of 8 | 87,406 / 17,782 | S$0.061 |
| `b5f6435b-4679-4f80-94c5-6a059fcd386c` | before | the 8 | 2 of 8 | 86,197 / 15,549 | S$0.057 |
| `d1903574-366e-42d8-93a8-9185f6136590` | now | the 8 | 4 of 8 | 101,243 / 18,650 | S$0.067 |
| `309aecb3-ce20-49be-aa5f-e5cb10ae8506` | now | the 8 | 2 of 8 | 97,659 / 17,668 | S$0.064 |
| `4cfef3bc-678c-45e2-a0f7-bb6ce7600e78` | before | Check-in case | fail | 9,052 / 2,201 | S$0.007 |
| `7b1a1132-c083-4828-b1f5-78da1268df1b` | before | Check-in case | fail | 8,965 / 1,740 | S$0.006 |
| `49eec00f-9bf8-4617-b19b-11e21cf57018` | before | Check-in case | fail | 8,913 / 2,080 | S$0.007 |
| `74c6767c-d5fc-4bcc-aae6-699d9b47b941` | before | Check-in case | pass | 8,414 / 1,338 | S$0.005 |
| `81f9674a-8546-45ff-997b-a2706c2e11b9` | now | Check-in case | fail | 10,524 / 2,138 | S$0.007 |
| `db5ecc1e-a5c4-4a73-a4a3-60ccbaffe989` | now | Check-in case | pass | 10,142 / 2,190 | S$0.007 |
| `b9be652f-e841-42c5-914d-613172fc605c` | now | Check-in case | fail | 10,603 / 1,888 | S$0.007 |
| `8b82bf59-51de-4a24-bf6e-081cd4b2440f` | now | Check-in case | fail | 10,602 / 2,355 | S$0.008 |
| `2a882c1d-10ff-4ec6-88e0-c2d0a9c3f841` | now | `guess-checked-gently`, first rewrite | fail | 10,043 / 1,892 | S$0.007 |
| `8c5f7632-24aa-4620-9f6d-45e0458a4a7f` | now | `guess-checked-gently`, final | pass | 10,150 / 1,660 | S$0.006 |
| `e43ddd11-0591-4b5c-b619-3fb2d85e4487` | now | `guess-checked-gently`, final | fail | 10,187 / 1,658 | S$0.006 |
| `da21b1bb-3911-4a14-a7ca-72cb7556c695` | now | `guess-checked-gently`, final | pass | 10,187 / 1,429 | S$0.006 |

The runs live in the two worktree databases, which are deleted at teardown. The reports were read in full before that; what matters from them is below.

**Each case** (B = before, N = now; P pass, F fail)

| Case | B1 | B2 | N1 | N2 | Sorted as | Why |
| --- | --- | --- | --- | --- | --- | --- |
| `strong-mood-unknown-cause` | F | F | P | F | always failed (a case fault) | The Reply Plan leads with Get curious instead of setting "ask why". The reply asks what is behind the mood either way; the judge passed it 4 of 4. |
| `knowledge-for-a-reflective-question` | P | F | P | P | flaky | Once before, the Need was Advice, not Think it through. Passes now. |
| `no-knowledge-for-a-vent` | F | F | P | F | always failed (an old fault) | The Need and "no Knowledge" are right every time. The reply gives a breathing tip, which fails the judge's "no fixing" rule. |
| `check-in-not-now-while-asking-for-help` | P | P | P | F | flaky (an old fault) | Looked worse, so it was run 4 more times on each side: 3 of 6 before, 2 of 6 now. The Reply Plan weaves in the follow-up Check-in about half the time on both. The Check-in part of the prompt is the same in both commits. |
| `internal-testing-finish-line` | P | F | F | P | flaky | Now and then it picks another Need or Move (Be heard and Get curious before, Suggest now). |
| `small-talk-makes-no-move` | F | F | F | F | always failed (a case or prompt fault) | The case wants no Move. The Reply Plan always makes one: Suggest before, Get curious now. |
| `next-move-held-then-made` | F | F | F | F | always failed (a case fault) | The case wants Research held for the next reply. The Reply Plan leads with Research at once, every time. |
| `guess-checked-gently` | F | P | F | F | got worse: the case was out of date | Before, it failed or passed on the judge rule only. Now code drops Get curious when the reply raises the Curiosity (issue 01's one question per reply), so "lead Move Get curious" can never pass. Zeph's behaviour is as designed. |

**`guess-checked-gently`, what changed**

- It now expects `curiosity_raised: true`, not `lead_move: [Get curious]`.
- First try (run `2a882c1d`): with only that change it failed. On "she sounded so happy" the Reply Plan asked what made her happy and left the Curiosity. Under Just chatting a Curiosity is the model's choice, so the Message has to make it fit.
- Final case: the Curiosity's question is "Where is home for your mum these days?" (it was "Is your mum back home after her visit?", whose answer says little about the guess), the Message is "had a long call with my mum last night, she's settled back in at home after the visit", and the judge rule says the reply asks one light question whose answer would show where their mum lives and never states Singapore as fact.
- Result: passed 2 of 3 (`8c5f7632`, `da21b1bb`). The Curiosity was raised 3 of 3. The one fail (`e43ddd11`) is the rule doing its job: the reply said "how's she doing back in Singapore" and asked two questions. That is a fault in the reply, listed in issue 33.

**What was built so the changed case reaches stacks that already have it**

A seed case loads only where its key isn't stored, so editing the seed file alone changes nothing on main's stack or on prod.

- `reload_eval_case_unless_edited(connection, key)` in `src/companion/adapters/postgres/eval_case_reload.py`: removes the stored case only when no Admin edited or archived it, so the seed loads the new one. Otherwise the case is kept and a warning naming it is logged. It follows issue 28's helper for prompts.
- Migration `0102_guess_case_expects_the_curiosity.py` calls it for `guess-checked-gently`.
- The migrations guide has a new part, "Changing a seed Eval Case"; `evals/README.md` points to it.
- No prompt was changed, so issue 28's helper wasn't needed.
- Shared files touched: a migration (0102) and the migrations guide.

**Evidence per criterion**

- **Each case run twice before and twice now, with IDs and costs.** The four runs of 8 in the table above.
- **Each case sorted, with the reason.** The second table.
- **`guess-checked-gently` can be met and passed a run.** Runs `8c5f7632` and `da21b1bb` passed, on this worktree's running stack after migration 0102 reloaded the case (the stored case went from `lead_move: [Get curious]` to `curiosity_raised: true`; `alembic_version` 0102).
- **Every real regression fixed or has its own issue.** The only case that got worse is `guess-checked-gently`, fixed here. The old faults are in issue 33.
- **The owner was shown the estimate before each run.** See "The owner and the estimates": shown before the first runs; the follow-up runs were under the S$0.50 cap the owner set, not shown one by one.

**Checked in the running app.** On this worktree's stack: (1) backend rebuilt with 0102, the unedited stored case was removed and loaded again from the seed; (2) the stored case marked edited, the migration run again: the case was kept and the backend log had "Kept the stored Eval Case guess-checked-gently: an Admin edited or archived it, so the new seed case was not loaded. Change it by hand on the Dashboard."

**Checks.** ruff clean, ruff format clean, mypy clean (278 files), pytest 2471 passed. New tests: `tests/test_eval_case_reload.py` (4). No Dashboard code changed, so the web checks were not run.

**For the owner to know**

- With two tries a side, "flaky" and "always failed" are rough. A case that failed 4 of 4 is solid; a 1 of 4 could be a 2 of 4.
- A reloaded case moves to the end of the Understanding list on the Dashboard.
- Prod is at migration 0078, so 0102 runs there on the next deploy along with the rest.
- `20-findings-for-the-owner.md` was not edited (other agents are working in it); its two findings for this issue are now answered here.
