# 36 — A shared Pattern is confirmed and closed fairly

Status: completed
Track: shared
Blocked by: none

## Parent

`30-owner-decisions-before-pattern-sharing-is-on.md`, answers 2, 6, 7, 9 and 10.

## What to build

1. **One story counts once (answer 2).** The tagging step keeps which Conversation gave a Prediction its outcome (`predictions.outcome_conversation_id`). When a Prediction came true or didn't, that Conversation's Observations of the same Pattern Type count nothing for that Pattern: not in its score, not in "strong evidence after sharing". The quotes are still kept and shown.
2. **Closing on failed Predictions (answer 7).** A shared Pattern is closed when `predictions_to_close` (new Admin setting, 2) Predictions didn't come true and more didn't than did; logged with the new reason `predictions_did_not`. It is confirmed by Predictions only when more came true than didn't. The score floor stays and is still looked at first.
3. **"Strong evidence after sharing" stays 300 (answer 6).** No change.
4. **Stop after unanswered Predictions (answer 9).** After `predictions_unanswered_to_stop` (new Admin setting, 2) Predictions in a row ended "not followed up", no new Prediction is offered for that Pattern until the User brings the Pattern up (a reaction to it is read in a later Conversation).
5. **One narrowing rule (answer 10).** Scoring leaves out evidence against that only narrows a Pattern, with the same function the gate uses, everywhere a Pattern's score is read. Evidence against with no person tag is left out of the narrowing check: it no longer switches narrowing off, and still counts against in full.

## Acceptance criteria

- [x] A story that settles a Prediction and is tagged as an Observation moves the score once, with a test
- [x] A shared Pattern closes on 2 failed Predictions when more didn't than did; 2 true and 2 failed keeps testing; with tests
- [x] After 2 unanswered Predictions in a row no new one is offered, until a later reaction to the Pattern; with tests
- [x] A narrow Pattern stays suspected in scoring where the gate would narrow it; a line against with no person named doesn't switch narrowing off; with tests
- [x] The two new numbers are on Platform settings with hints, and overridable in Eval Variants
- [x] `docs/pattern-pipeline/README.md` says what changed
- [x] `ruff`, `ruff format`, `mypy` and `pytest` pass, and it was checked in the running app

## Comments

### 25 Nov 2026: built

Review fixes: failed Predictions are counted once per wording, like the ones that came true (the first version compared a per-wording count with a per-Prediction count); a Prediction with no number counts as the first wording.

Left as it is: the stop after unanswered Predictions also lifts when the User agrees after Zeph itself named the Pattern (issue 39), which is looser than "the User brings it up".

**Checks.** ruff clean, ruff format clean, mypy clean (286 files), pytest 2584 passed; web: eslint, prettier and tsc clean, Vitest 989 passed (141 files).

**How it was checked in the running app.** On this worktree's stack (fresh database, migrated to 0109, seeds loaded). Dashboard pages were driven in a real browser as a signed-in Admin and User. The chat path was run by the real core services on the stack's database with only the chat model scripted, the chat channel recording, and the clock and scheduler moved by hand (a worktree can't reach Telegram), acting as the signed-in User so the browser showed the result. Not checked: the migrations on a copy of the main database (the main stack wasn't running); the tests cover them by downgrading and migrating again.

**Evidence per criterion**

- **A story that settles a Prediction counts once.** `test_a_story_that_settles_a_prediction_moves_the_score_once`, `test_a_story_that_settles_a_prediction_and_is_tagged_too_counts_once`. Running app: a shared Pattern at 410 points; the User said the Prediction didn't happen and the same story was tagged against; the score read 244 (one strong sign, plus fading over the 9 days), with `outcome_conversation_id` set.
- **Closing on 2 failed; 2 and 2 keeps testing.** `test_enough_predictions_that_did_not_come_true_close_a_shared_pattern`, `test_predictions_confirm_only_when_more_came_true_than_did_not`, `test_the_same_wording_failing_twice_is_one_test_failed`, `test_enough_predictions_that_didnt_come_true_close_a_shared_pattern`. Running app: after a second, different Prediction didn't come true the log read shared → closed, reason `predictions_did_not`, at 87 points (above the floor), and the Patterns tab showed it under "Didn't hold up".
- **No new Prediction after unanswered ones, until a reaction.** `test_no_new_prediction_is_offered_after_two_in_a_row_got_no_answer`, `test_predictions_are_offered_again_once_the_user_brings_the_pattern_up`. Running app (the number set to 1): 22 days with no answer → "not_followed_up" and 0 offers waiting; after a Conversation where they agreed with the Pattern, 1 offer waiting.
- **Narrowing in scoring; a line with nobody named doesn't switch it off.** `test_scoring_leaves_out_evidence_that_only_narrows_like_the_gate`, `test_evidence_against_with_nobody_named_does_not_switch_narrowing_off`, `test_evidence_that_only_narrows_a_shared_pattern_does_not_count_against_it`. Running app: the Pattern became ready and was shared narrowed ("It shows with family, friend; not with partner") with its score counted without the partner story.
- **The two numbers are settings with hints and Eval overrides.** `test_the_closing_and_stopping_numbers_are_settings_with_hints_and_eval_overrides`. Running app: as an Admin on Platform settings, both rows show with their hints; changed "Unanswered Predictions in a row" to 3, saved, reloaded (3), put back to 2.
- **Docs.** `docs/pattern-pipeline/README.md` ("Changed (25 Nov 2026)"), `lifecycle.md`.
- **Checks pass; checked in the running app.** Above.

## Completion

- Completed: 2026-11-25
- Commit: MERGE_COMMIT
