# 19 — A whole-pipeline Eval with made-up Users who have hidden true Patterns

Status: completed
Track: B
Blocked by: 08

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 88). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

A new Eval kind that checks the pipeline end to end. A case is a made-up User with a hidden set of true Pattern Types and a script of several Conversations (with the clock moved between them). It runs the real reply path and Conversation-end steps, then checks which Patterns became ready or shared. A case passes when every ready Pattern is one of the true ones; the run reports how many true ones were found. Target: at least 70% of ready Patterns true. Start with 5 made-up Users.

Its limit goes in `docs/pattern-evals/README.md`: a model playing the User and a model tagging them tend to agree, so this catches breakage, not truth. It costs more than other Evals: remind the owner and show the estimate before any run.

## Acceptance criteria

- [x] The Eval kind runs from the Dashboard and the terminal, with Variants
- [x] A case scripts several Conversations for one made-up User and moves the clock between them
- [x] The result lists each Pattern that became ready or shared and whether it was one of the true ones, and how many true ones were missed
- [x] 5 starting cases are seeded, at least one with two look-alike true Patterns and one with none
- [x] The estimate is shown before the run
- [x] The guide's limits section covers this Eval
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `08-sharing-a-ready-pattern.md`

## Comments

### 2026-11-25: built, checked in the running app, archived

What was built:

- **A tenth Eval kind, `whole_pipeline`** (`core/evals/whole_pipeline_eval.py`), no Judge. A case holds the hidden true Pattern Types and a list of Conversations, each with "days after the one before" and the User's texts.
- **The real path.** Each text goes through the real webhook and reply path. After each Conversation the Eval moves the clock past the quiet gap and runs the real scheduled work once (`ManualScheduler`, `end_conversation`), so every Conversation-end step runs as in the live app. Pattern noticing (told), exploring and sharing are on.
- **The result** is read from the log of Pattern moves: each Pattern that became ready or was shared, whether it is a true one, where it stands now; each true one missed, where it stands and the ready check that stopped it.
- **Five seeded cases** in `seed/evals/cases/whole_pipeline.yaml`.
- **Terminal:** a score line against the 70% target; `make eval` runs this Eval only when named.
- **Dashboard:** the result card shows "Became ready or shared" and "True Patterns missed".

Decisions made while building (owner may want to look):

- **The User's texts are written into the case**, drafted by Claude, not written by a model during the run. A run is repeatable and cheaper; the User never answers Zeph's questions.
- **Missed true Patterns don't fail a case** (the issue's rule), so a case with nothing ready passes.
- **`make eval` with no Eval named leaves this one out**, because of its cost.
- **A case is an Error**, not a Fail, when a true Pattern Type isn't in the catalog, a Conversation wasn't processed, or a Conversation end made no tagging call.
- **The made-up User has Check-ins off**, so sharing by Check-in is not reached.
- **The result panel reuses the Tagging result's parts.** No design file was changed; its words are in no reference file.
- **The rough figure** is 300,000 tokens in and 110,000 out per case, from the real runs.

Limits and findings are in `20-findings-for-the-owner.md` (19). The ones to read first: **a full run of the 5 cases goes over the starting token limit**, and **three of the five cases have never been run**.

Evidence (25 Nov 2026, worktree stack on 3030/8030, real model `deepseek/deepseek-v4.1-flash-1017`, made-up Users only. The owner chose the smallest paid proof: 3 case runs, S$0.83 in all):

- **Runs from the Dashboard and the terminal, with Variants.** Terminal: `make eval CASES=ordinary-fortnight` printed `PASS whole_pipeline/ordinary-fortnight (499.3 s, 284040 tokens)` and "Whole pipeline: 0 of 0 ready Patterns true (none ready, target 70%); 0 of 0 true Patterns found" (run 838c7332). Dashboard, in the browser: New run, picked `folds-with-sister-and-friends`, added Variant B with "Situations to be ready" 9 (live 3), Start run (run f14e5466). Variant A: CONF.AVOID.BELONG ready, "True", 1 of 1 found. Variant B: nothing ready, the Pattern "Missed", "Suspected", "Too few situations". Tests: `test_a_variant_s_override_changes_what_becomes_ready_in_a_whole_pipeline_case`, `test_the_terminal_runs_the_whole_pipeline_eval_only_when_it_is_named`.
- **Several Conversations, clock moved between them.** The stored calls of the terminal run: 12 each of safeguard, understanding, reply plan and reply (12 texts), and 4 each of conversation end, life threads, pattern tagging, patterns, curiosities, move outcomes and portrait (4 Conversations). Variant A: 5 tagging calls and 1 other-side call. The Pattern needed evidence from more than one Conversation and day to be ready, and was. Test: the failed-case notes read "Conversation 1, 02 Nov 2026" and "Conversation 2, 05 Nov 2026" for `days_later: 3`.
- **The result lists each ready or shared Pattern, true or not, and the missed.** Browser, run page at 1280 and 390, each Variant's cell opened: "5 Conversations · 1 of 1 true Pattern found", "Became ready or shared", "CONF.AVOID.BELONG · Softening disagreement to protect belonging", "True", "Got as far as Ready", "True Patterns missed: None missed."; and for B "No Pattern became ready." with the missed row. No page error, no sideways scroll. A ready Pattern that is not true, and a shared one, were not seen in a real run; tests: `test_a_whole_pipeline_case_fails_when_a_ready_pattern_is_not_a_true_one`, `test_the_facts_tell_true_from_false_ready_patterns_and_list_the_missed`, `WholePipelinePatterns.test.tsx`.
- **5 starting cases, one look-alike pair, one with none.** Browser, Admin → Evals → Cases → Whole pipeline lists the five, "From the seed files"; the edit form of `goes-quiet-and-says-fine` shows CONF.WITHDRAW.HURT and APPR.HIDE.BURDEN (each lists the other as a look-alike in the catalog) and its 6 Conversations; `ordinary-fortnight` has none. Test: `test_the_seed_has_five_made_up_users_with_a_look_alike_pair_and_one_with_none`.
- **The estimate is shown before the run.** Terminal: the first line was "Estimate: 1 case, about S$0.1982 at the live prices (1 never run, so a rough figure)" (real cost S$0.1956). Browser, New run: "About 600,000 in / 220,000 out tokens · S$0.5668", per Variant, above Start run (real cost S$0.6347). The Eval's card says "It costs far more than the other Evals, so check the estimate before you start."
- **The guide's limits cover this Eval.** `docs/pattern-evals/README.md`, layer 3: Shows / Can't show (a model wrote the Users and a model tags them; five Users can't carry a 70%; nothing ready passes; a scripted User never answers; no Check-in sharing; results vary), the first results, and how to run it with the cost reminder. Also `evals/README.md`, `docs/pattern-pipeline/README.md` and `CONTEXT.md`.
- **Checks.** On the final code, rebased onto main (64fb4615): ruff clean, ruff format clean, mypy clean (267 files), pytest 2430 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 141 files, 987 tests passed. After the rebase the stack was rebuilt: the run page and both result cards still open with no page error, and the estimate for the 5 cases reads S$1.3859. The three paid runs were made before the rebase (the review fixes were in for the Dashboard run).
- **Review.** Standards and spec reviews run. Fixed: the tagging step must run after every Conversation, not only the first; blank true Pattern Types are dropped; the 70% target lives with the Eval; Pattern states are typed on the Dashboard. Left and logged in issue 20: no reference file for the result panel; no run-level share on the Dashboard; a quietly failing Conversation-end step shows only as fewer Patterns found.
- **Not checked in the running app:** a failed case (a ready Pattern that isn't true), a shared Pattern, a run stopped between Conversations, and the three other seeded cases. This worktree's own token limit was raised to 2,000,000 for the two-Variant run; the live setting is untouched.

## Completion

- Completed: 2026-11-25
- Commit: 9d875d5d (merge of `pattern-19-whole-pipeline-eval` into main; work commits d965df98, 12054598, c92af531, 0ef70be3, 67321f52)
