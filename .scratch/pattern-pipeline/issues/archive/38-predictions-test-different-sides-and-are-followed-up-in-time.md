# 38 — Three Predictions per Pattern Type, followed up when the User next talks about it

Status: completed
Track: shared
Blocked by: 36 (same confirm rule)

## Parent

`30-owner-decisions-before-pattern-sharing-is-on.md`, answer 8 and the owner's added item on follow-ups.

## What to build

1. **Three Prediction wordings per Pattern Type (answer 8).** The catalog field becomes a list, `prediction_wordings`, each testing a different side of the Pattern. Claude drafts three for each of the 15 Pattern Types (new catalog versions); the owner corrects them later (added to the owner's list in issue 20).
2. **Code picks one not used yet.** A Prediction keeps which wording it came from (`predictions.wording_number`). Sharing gives the first; a new Prediction is the first wording this Pattern hasn't had, and when all were given, the one given longest ago.
3. **Two that came true are two different tests.** Confirming by Predictions counts each wording once.
4. **Follow up when they next talk about it.** A follow-up Curiosity may be asked before its first day when a Life Thread the Pattern showed in comes to mind in a reply on a later day than the Prediction was given. The Admin-set wait (7 days) stays as the fallback, and the last day stays.
5. **A guide for the owner:** `docs/pattern-catalog/README.md` gains a section on writing and correcting Prediction wordings.

## Acceptance criteria

- [x] Every Pattern Type has three Prediction wordings, and the catalog refuses fewer than one
- [x] A new Prediction uses a wording the Pattern hasn't had, with a test
- [x] The same wording coming true twice doesn't confirm; two different ones do, with tests
- [x] A follow-up is offered early when a Life Thread of the Pattern is in mind on a later day, and not on the day the Prediction was given, with tests
- [x] The Admin Pattern Catalog page shows all the wordings
- [x] The guide is written, and the owner's correction step is on issue 20's list
- [x] `ruff`, `ruff format`, `mypy`, `pytest` and the web checks pass, and it was checked in the running app

## Comments

### 25 Nov 2026: built

The 45 Prediction wordings are Claude's drafts. Correcting them is the owner's step, on issue 20's list; the how-to is "Writing and correcting Predictions" in `docs/pattern-catalog/README.md`.

Review fix: the early follow-up also fires when a Life Thread in mind has a person in it that the Pattern's Observations are about, not only for the same Thread.

Design files: `web/design/reference/AdminPatternCatalog.html` and its baseline were updated by the agent for the new versions and the three Prediction lines, as the catalog guide says to. The owner may want to look.

**Checks.** ruff clean, ruff format clean, mypy clean (286 files), pytest 2584 passed; web: eslint, prettier and tsc clean, Vitest 989 passed (141 files).

**How it was checked in the running app.** On this worktree's stack (fresh database, migrated to 0109, seeds loaded). Dashboard pages were driven in a real browser as a signed-in Admin and User. The chat path was run by the real core services on the stack's database with only the chat model scripted, the chat channel recording, and the clock and scheduler moved by hand (a worktree can't reach Telegram), acting as the signed-in User so the browser showed the result. Not checked: the migrations on a copy of the main database (the main stack wasn't running); the tests cover them by downgrading and migrating again.

**Evidence per criterion**

- **Every Pattern Type has three wordings; fewer than one is refused.** `test_a_pattern_type_is_read_with_all_its_details`, `test_a_pattern_type_needs_at_least_one_prediction_wording`, `test_a_version_stored_with_one_prediction_wording_is_still_read`. Running app: all 15 current versions in `pattern_types` hold 3.
- **A new Prediction uses a wording the Pattern hasn't had.** `test_a_new_prediction_uses_a_wording_the_pattern_has_not_had`, `test_once_every_wording_was_given_the_one_given_longest_ago_comes_again`, `test_predictions_that_came_true_confirm_a_pattern_and_it_joins_the_portrait`. Running app: the Prediction given at sharing had number 1; the offer after it was settled carried the second wording ("…notice how you feel about it a few hours later"), and the Prediction kept had number 2.
- **The same wording twice doesn't confirm; two different do.** `test_the_same_wording_coming_true_twice_is_one_test_passed`.
- **Early follow-up when a Life Thread of the Pattern is in mind, not on the day it was given.** `test_a_follow_up_is_due_early_when_a_thread_of_the_pattern_is_in_mind`, `test_a_follow_up_is_offered_early_once_they_talk_about_where_the_pattern_shows`. Running app: two days after sharing (first day five days away), "what a week" got no follow-up and "so, about Falling-out with Mei" got it offered.
- **The Admin Pattern Catalog page shows all the wordings.** `PatternCatalog.test.tsx`. Running app: as an Admin, every card shows Prediction 1 to 3 (15 of each). Pixel test `AdminPatternCatalog` PASS 0.00% against the updated reference (run with a copy of `compare.cjs` that blocks Clerk's probe requests, then deleted).
- **The guide is written; the owner's step is on issue 20's list.** `docs/pattern-catalog/README.md`; issue 20, section 30.
- **Checks pass; checked in the running app.** Above.

## Completion

- Completed: 2026-11-25
- Commit: MERGE_COMMIT
