# 13 — Evals split into Understanding and Reply Plan checks

Status: completed
Lane: A
Blocked by: 09

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

The Understanding Eval today checks reading and deciding together. Split its checks between the two steps: the Understanding's (said / read / unclear, struggling, cause known, look-ups) and the Reply Plan's (Need, Moves, Threads brought up or left alone, Curiosities, ask-why, Knowledge, Woven-in Check-in, the Read formed and whether it is said). Existing cases are kept; their expectations move to the step that now owns them, and a seed never overwrites an edited case (as today). Variants' Setting Overrides cover the Reply Plan prompt and the Outlook.

Evals cost money: build and test with the fake model; don't run a real Eval Run without the owner.

User stories covered: 67, 68.

## Acceptance criteria

- [x] Each existing Understanding case runs and is marked on the step that owns each expectation
- [x] Reply Plan checks include whether a Read was formed and said
- [x] Setting Overrides accept the Reply Plan prompt and the Outlook
- [x] Eval runner and case tests pass with the fake model
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 09 — Woven-in Check-ins decided by the Reply Plan (`.scratch/message-pipeline/issues/09-check-ins-decided-by-reply-plan.md`)

## Comments

### 20 Nov 2026: done (branch `message-pipeline-13-split-evals`)

**What was built.** Each Understanding Eval check is now named after the step that owns it (`check_steps` in `core/evals/understanding_checks.py`):
- **Understanding**: struggling, cause known, looks up the past, feelings said, wants said (new expectation fields).
- **Recall**: Life Threads found.
- **Reply Plan**: Read formed, Read said (new), then Need, Moves, raised / not raised, Curiosity, asked why, Knowledge, woven in.

For example: `Reply Plan · need: picked Be heard, expected Advice`.

**Decisions** (made by the agent; the owner can reverse any of them):
- **One case run checks every step.** Running each step as its own Eval would mean replaying the conversation twice, which doubles the cost. Story 67 ("separate Evals") is met by step-marked checks inside one Eval, not by two Eval kinds.
- **Expectations stay one flat list, and code decides which step owns each one.** No migration was needed, stored and edited cases keep working untouched, and the seed rule is unchanged.
- **"found" is marked Recall.** Recall is the code step between the Understanding and the Reply Plan, so it is neither model's job.
- **"Feelings said" and "Wants said" check only the `said` slot.** Yes means something is kept as said. No means nothing is kept as said, because the User put none in words. `read` and `unclear` aren't checked separately.
- **Four new seed cases use the new checks:** `scared-before-the-exam`, `feeling-not-put-in-words`, `looks-back-at-an-old-trip`, `asks-for-zeph-view`.
- **No code was needed for the Setting Overrides.** The Reply Plan prompt and the Outlook were already editable Platform Settings. A new test proves they reach only their Variant.

**Evidence per criterion**
1. **Existing cases marked by step.**
   - Unit: `test_each_expectation_is_checked_on_the_step_that_owns_it`. Runner: `test_an_understanding_case_marks_each_check_with_the_step_that_owns_it`.
   - Running app: existing cases `advice-is-asked-for` and `sister-not-raised-twice` ran on the worktree stack. The Dashboard showed `FAIL Reply Plan · need: picked Be heard, expected Advice`, `PASS Recall · found: was reminded of Falling-out with Mei` and `PASS Reply Plan · not raised: left Falling-out with Mei alone`.
2. **Read formed and said.**
   - Running app (`asks-for-zeph-view`): `PASS Reply Plan · read formed: formed a Read` and `FAIL Reply Plan · read said: held the Read back, expected: said the Read`.
   - Running app (`scared-before-the-exam`): `PASS Reply Plan · read said: held the Read back`.
3. **Overrides for the Reply Plan prompt and the Outlook.**
   - On the new-run page, Variant B changed "Reply Plan prompt" and "Outlook". The estimate showed and the run started.
   - The stand-in model recorded the marker text in Variant B's Reply Plan calls only: calls 1 and 3 had both markers, calls 0 and 2 had neither.
   - The run page lists "Variant B · live settings with 2 changed: Outlook, Reply Plan prompt".
   - Test: `test_reply_plan_prompt_and_outlook_overrides_reach_only_their_variant`.
4. **Fake-model tests.** `tests/test_understanding_eval_helpers.py`, `tests/test_eval_runner.py` and `tests/test_eval_cases.py`: 121 passed.
5. **Migrations.** None added. Rebased onto `main` after issue 12 merged, so the one head is 0072 (issue 12's).
6. **Docs.** `CONTEXT.md` (Eval), the "Built" note under step 6 in `docs/message-pipeline/README.md`, `evals/README.md`, the seed file's header, and the Eval's Dashboard subtitle (`web/src/lib/evals.ts`) are all updated.
7. **Checks.**
   - `uv run pytest`: 1446 passed on the final code, and 1456 passed after rebasing onto issue 12.
   - `uv run ruff check .`: all checks passed. `uv run ruff format --check .`: 550 files already formatted. `uv run mypy src`: no issues in 202 files.
   - Web: lint, Prettier, tsc, and Vitest (887 tests) all pass.
8. **/run on the worktree stack (ports 3020/8020), signed in as Admin.**
   - Seed: `eval_cases` holds the 4 new cases beside the old ones.
   - Case edit page: each expectation's hint starts with its step ("Understanding: …", "Recall: …", "Reply Plan: …"), with no page errors.
   - Two runs were started from the Dashboard, with the eval-runner stopped, and worked by the real `EvalRunner` inside the backend container. Only the chat model was a stand-in, so no paid model calls were made.
   - Run `09de5cd8`: new cases on Variants A and B. Run `dc7308a7`: existing cases. Both Finished.
   - The Case Result cards showed each check with its step: `FAIL Understanding · struggling: not struggling, expected: struggling`, `PASS Understanding · wants said: kept wants said in their words`.
   - After the review fixes, a rebuild showed the corrected "Feelings said" hint.
   - After the rebase onto issue 12 (wide recall), run `8c01e487` on the rebuilt stack showed `PASS Recall · found: was reminded of Falling-out with Mei` (`reminded-of-sister`) and the Read checks on `asks-for-zeph-view`.

**Review** (`/code-review`, two axes):
- **Fixed:** clearer names (`mark_with_step`, `understanding_form`); the Read is worked out once; `cause_known` defaults to False like the other flags; the "Feelings said" hint no longer promises a read/unclear check.
- **Left, for the owner:**
  - Story 67 is met by step-marked checks, not by two Eval kinds.
  - The old cases' hints ("may fail until issue 13") were not re-checked against the real model, because that costs money. Do a real Understanding Eval Run when ready.
  - The Understanding and Reply Plan are read as the newest in the Conversation, as before, not matched to the Message.
  - `check_asked_why` and `check_woven_in` could reuse `check_yes_no`, but that would change their wording, so they were kept.
- **Unrelated stale text:** the Needs and Moves field hints still say "when the Understanding picks this Need/Move".

## Completion

- Completed: 2026-11-20
- Commit: c0aae22 "Merge message pipeline issue 13: Understanding Eval checks marked by the step that owns them" (merged into `main` locally and pushed), with:
  - ddc3726 "Message pipeline issue 13: Understanding Eval checks marked by the step that owns them"
  - 0520574 "Issue 13 review fixes: clearer names, Read worked out once, honest Feelings said hint"
  - db07784 "Message pipeline issue 13 done: archive issue with test, run and review evidence; Recall in the glossary"
  - 64d0dc3 "Issue 13: rebase evidence"
