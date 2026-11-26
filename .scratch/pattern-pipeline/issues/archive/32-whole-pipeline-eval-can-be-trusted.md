# 32 — Make the Whole-pipeline Eval a result we can trust

Status: completed
Track: shared
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md`. Findings from `20-findings-for-the-owner.md` (section 19), triaged with the owner on 25 Nov 2026. Built in `archive/19-whole-pipeline-eval.md`. What it can and can't show: `docs/pattern-evals/README.md`.

## Why

The Whole-pipeline Eval is the only check that the pipeline works end to end, and today a green run proves little:

- A case where nothing becomes ready passes, so a dead pipeline is all passes. A Conversation-end step that fails is logged and skipped (`core/post_conversation.py`), so it shows only as fewer Patterns found.
- A full run of the 5 cases needs about 2,000,000 tokens and stops at the 1,000,000 limit.
- 3 of the 5 cases (`goes-quiet-and-says-fine`, `cannot-stand-waiting`, `never-arrives`) have never run with the real model.
- No Pattern was shared in any real run, so the "shared" half of the result has only been seen in tests.

## What to do

Evals cost money: show the owner the estimate and get a go-ahead before every run. A case is about S$0.30; a full run about S$1.40 and over an hour.

1. **Code, no Eval cost:** a case that has true Patterns and finds none of them fails, and the result says so. A case with no true Patterns (such as `ordinary-fortnight`) still passes when nothing is ready. A Conversation-end step that failed during a case is shown on the result, not only in the log.
2. **Token limit:** the owner raises the Eval run token limit on Admin → Evals → Model Prices to about 3,000,000 before a full run. Don't change the seed default unless the owner asks.
3. **Run the three never-run cases one at a time** and correct their scripts where they don't reach ready for a reason in the script, not the pipeline.
4. **Add one case where sharing is reached:** its last Conversations invite it ("anything you've noticed about me?"), or it has Check-ins on and a week's wait. Run it once.
5. Log what the runs find in `20-findings-for-the-owner.md`. Don't tune prompts here.

## Acceptance criteria

- [x] A case that finds none of its true Patterns fails, with a test; a case with no true Patterns and nothing ready passes
- [x] A failed Conversation-end step is shown on the case result
- [x] The three look-alike cases each ran once with the real model, with Eval Run IDs and costs in Comments
- [x] A new case reaches a shared Pattern in a real run
- [x] `docs/pattern-evals/README.md` says what changed in how to read a result
- [x] The owner was shown the estimate before each run
- [x] `pytest`, `ruff`, `ruff format` and `mypy` pass, and the result was checked in the running app (`/run`)

## Out of scope

- A model that plays the User and answers Zeph: issue 26.
- A reference file for the result panel, and a share line on the Dashboard run page: these wait for the owner's design reference (20 → 19).
- `make eval` leaving out the Whole-pipeline Eval: the owner agrees with it.

## Comments

### 25 Nov 2026 — built, run and checked

**What changed**

- **A case that finds none of its true Patterns fails.** New check "true Patterns found: N of M became ready", failed at 0 (`check_ready_patterns` in `core/evals/whole_pipeline_eval.py`). A case with two true Patterns that finds one still passes. A User with no true Pattern passes with "nothing ready".
- **A failed Conversation-end step is a failed check**, "Conversation-end step failed: after Conversation 2: Could not score Patterns: ...". `end_conversation` now returns what the app logged as failed on its thread during the scheduled work (`adapters/evals/logged_failures.py`). When the Conversation end doesn't finish at all, the Error names what failed.
- **A failed case's "What happened" starts with "Why it failed"**, so the Dashboard shows both reasons with no new part (the result panel has no reference file; out of scope).
- **Scripts.** `cannot-stand-waiting` corrected (migration 0104 reloads it where no Admin edited it). New sixth case `asks-what-zeph-noticed`. The seed file's header says how to write a script that can reach ready.
- **Docs.** `docs/pattern-evals/README.md` ("How to read a Whole-pipeline result", "Second Whole-pipeline results"), `evals/README.md`, `docs/pattern-pipeline/README.md`, `CONTEXT.md`.

**Runs** (each one case, on this worktree's stack, live settings; the owner said yes to each batch first)

| Eval Run | Case | Estimate shown | Result | Tokens in / out | Cost |
|---|---|---|---|---|---|
| `cba7a37a` | `asks-what-zeph-noticed`, first script | S$0.28 | Fail: suspected, stopped by counter-test | 406,496 / 173,358 | S$0.4214 |
| `31ce319c` | `goes-quiet-and-says-fine` | S$0.28 | Pass: CONF.WITHDRAW.HURT ready; APPR.HIDE.BURDEN suspected, stopped by situations | 390,716 / 175,105 | S$0.4181 |
| `aa7520fb` | `cannot-stand-waiting`, as drafted | S$0.28 | Fail: suspected, stopped by score | 306,984 / 112,304 | S$0.2896 |
| `cb7a3516` | `never-arrives` | S$0.28 | Pass: ACH.GOAL.MOVE ready, then shared | 337,835 / 147,328 | S$0.3553 |
| `ba027a22` | `asks-what-zeph-noticed`, second script | S$0.42 | Fail: suspected, stopped by situations | 380,042 / 149,170 | S$0.3741 |
| `61815c07` | `cannot-stand-waiting`, corrected | S$0.29 | Pass: CTRL.UNCERT.PLAN ready, then shared | 299,989 / 142,775 | S$0.3339 |
| `68538bc0` | `asks-what-zeph-noticed`, third script | S$0.37 | Pass: CONF.AVOID.BELONG ready after 5 Conversations, shared in chat in the 6th | 387,962 / 188,016 | S$0.4370 |
| `6db31e15` | a throwaway case, Variants A and B | about S$0.05 | A Pass (nothing ready, none true); B Fail (Portrait step failed, shown) | 68,933 / 6,788 | S$0.0366 |

Total S$2.67. The owner was asked four times: the first four runs (told about S$1.40 to S$1.50; they cost S$1.49), the two re-runs (told about S$0.71; cost S$0.71), the third run of the new case (told about S$0.40; cost S$0.44) and the throwaway check (told about S$0.05; cost S$0.04). The Eval run token limit was not changed: each single case is under 1,000,000. A full run of the 6 cases still needs it at about 3,000,000 (the owner's step, on Admin → Evals → Model Prices).

Why the scripts failed, all reasons in the script: the new case's "not with my husband" story had a second, comparing line that was tagged against with no person, which switches off narrowing; then its mum stories were tagged "above", which for CONF.AVOID.BELONG is what anyone would do. `cannot-stand-waiting` told its strong sign as an opinion and its counter-test person had no relationship named. No prompt was tuned. What these say about the pipeline is in `20-findings-for-the-owner.md`, section 32.

**For the owner to know**

- **A failed step fails the case; the issue only said "shown".** I chose Fail so a green case means every step ran. Any error logged while the Conversation ends counts, also the Portrait or Personal Stickers. Say if you would rather it be shown without failing.
- `goes-quiet-and-says-fine` found one of its two true Patterns. Its script was not changed: one run doesn't say whether the script or the tagging is why.
- Asked what it had noticed while the Pattern was only suspected, Zeph told the whole pattern anyway (run `cba7a37a`). Known from section 08; now seen in a whole run.
- The rough estimate for a never-run Whole-pipeline case (S$0.28) is low: they cost S$0.29 to S$0.44.
- Migration 0104 is a shared file. If you edited `cannot-stand-waiting` on a stack, your copy stays.
- No Dashboard code changed, so the web checks were not run.

**Review.** Standards and spec reviews run. Fixed after: the failure reader got its own tests (`tests/test_eval_logged_failures.py`); step failures became their own function (`check_failed_steps`); a clearer constant name; an unfinished Conversation end and a missing tagging call now name what failed; section 32 of the findings had landed in the wrong place; the guide's counts and costs said which runs they add up. Not changed: failures are read from the log (logged as a finding), and warnings are not counted.

**Checks.** ruff clean, ruff format clean, mypy clean (281 files), pytest 2538 passed.

**Evidence per criterion**

- **A case that finds none of its true Patterns fails, with a test; none true and nothing ready passes.** `test_a_case_that_finds_none_of_its_true_patterns_fails`, `test_nothing_ready_passes_only_when_no_pattern_is_true`, and through the runner `test_a_whole_pipeline_case_that_finds_none_of_its_true_patterns_fails` and `..._with_no_true_pattern_and_nothing_ready_passes`. Running app: runs `aa7520fb`, `cba7a37a` and `ba027a22` failed with "true Patterns found: 0 of 1 became ready"; run `6db31e15` Variant A passed with "nothing ready".
- **A failed Conversation-end step is shown on the case result.** `test_a_whole_pipeline_case_shows_a_conversation_end_step_that_failed`. Running app: run `6db31e15` Variant B (a Portrait model that doesn't exist) failed with "Conversation-end step failed: after Conversation 1: Could not write the User Portrait: HTTPStatusError(...)", seen in the terminal report and on the Dashboard run page under "What happened".
- **The three look-alike cases each ran once with the real model.** Runs `31ce319c`, `aa7520fb` (and `61815c07` corrected), `cb7a3516`, in the table.
- **A new case reaches a shared Pattern in a real run.** Run `68538bc0`: the log of moves reads suspected → ready (10 Nov, 494 points, 3 situations) → shared, cause `shared_in_chat` (12 Nov).
- **`docs/pattern-evals/README.md` says what changed in how to read a result.** Section "How to read a Whole-pipeline result (changed 25 Nov 2026, issue 32)".
- **The owner was shown the estimate before each run.** Four asks, above.
- **Checks pass, and the result was checked in the running app.** Checks above. On this worktree's stack as a signed-in Admin: the run page of `aa7520fb` at 1280 and 390 shows Fail, "0 of 1 true Pattern found", "Stopped by: Score under the bar" and "What happened" starting "Why it failed: true Patterns found: 0 of 1 became ready"; `61815c07` shows Pass with "Got as far as: Shared"; `6db31e15` shows the failed step. Migration 0104 ran on the stack (`alembic_version` 0104) and the stored `cannot-stand-waiting` was replaced by the corrected one.

## Completion

- Completed: 2026-11-25
- Commit: 0f5119eb (merge of pattern-32-whole-pipeline-eval-can-be-trusted into main; work commits a7326f49, 8e468e80 and bd0701bc)
