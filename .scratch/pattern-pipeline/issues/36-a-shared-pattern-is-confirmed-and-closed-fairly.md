# 36 — A shared Pattern is confirmed and closed fairly

Status: ready-for-agent
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

- [ ] A story that settles a Prediction and is tagged as an Observation moves the score once, with a test
- [ ] A shared Pattern closes on 2 failed Predictions when more didn't than did; 2 true and 2 failed keeps testing; with tests
- [ ] After 2 unanswered Predictions in a row no new one is offered, until a later reaction to the Pattern; with tests
- [ ] A narrow Pattern stays suspected in scoring where the gate would narrow it; a line against with no person named doesn't switch narrowing off; with tests
- [ ] The two new numbers are on Platform settings with hints, and overridable in Eval Variants
- [ ] `docs/pattern-pipeline/README.md` says what changed
- [ ] `ruff`, `ruff format`, `mypy` and `pytest` pass, and it was checked in the running app

## Comments
