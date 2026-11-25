# 32 — Make the Whole-pipeline Eval a result we can trust

Status: ready-for-agent
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

- [ ] A case that finds none of its true Patterns fails, with a test; a case with no true Patterns and nothing ready passes
- [ ] A failed Conversation-end step is shown on the case result
- [ ] The three look-alike cases each ran once with the real model, with Eval Run IDs and costs in Comments
- [ ] A new case reaches a shared Pattern in a real run
- [ ] `docs/pattern-evals/README.md` says what changed in how to read a result
- [ ] The owner was shown the estimate before each run
- [ ] `pytest`, `ruff`, `ruff format` and `mypy` pass, and the result was checked in the running app (`/run`)

## Out of scope

- A model that plays the User and answers Zeph: issue 26.
- A reference file for the result panel, and a share line on the Dashboard run page: these wait for the owner's design reference (20 → 19).
- `make eval` leaving out the Whole-pipeline Eval: the owner agrees with it.

## Comments
