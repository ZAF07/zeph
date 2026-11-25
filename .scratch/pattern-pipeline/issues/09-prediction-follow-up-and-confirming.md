# 09 — Zeph follows up a Prediction, and Predictions that came true confirm a Pattern

Status: in-progress
Track: A
Blocked by: 08

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 37). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

After an Admin-set wait (start 7 days) the Companion asks how the Prediction went, as a Curiosity aimed at it; it is dropped if not asked within a longer time (start 21 days). What the User reports is read by the model (came true, didn't, hasn't come up) and weighed by code as a strong sign for or against. An Admin-set number that came true (start 2), or strong evidence after sharing, moves the Pattern to confirmed; it then goes into the User Portrait. A confirmed Pattern gets a new Prediction when the last one is settled and it isn't yet confirmed.

## Acceptance criteria

- [ ] A shared Pattern's Prediction gets a follow-up Curiosity not before the Admin-set wait
- [ ] A follow-up not asked within the longer Admin-set time is closed
- [ ] A Prediction that came true adds a strong sign for; one that didn't adds a strong sign against; "hasn't come up" adds nothing and a later follow-up may be made
- [ ] The Admin-set number of Predictions that came true moves the Pattern to confirmed, with the move logged
- [ ] A shared Pattern whose score falls under the floor is closed, with the reason kept
- [ ] A shared Pattern still short of confirmed gets a new Prediction after the last is settled
- [ ] A confirmed Pattern appears in the User Portrait's input; a shared one doesn't
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `08-sharing-a-ready-pattern.md`

## Comments

- 25 Nov 2026 (from issue 08): sharing is built (`core/pattern_sharing.py`). For this issue: (1) the Prediction as told is in `predictions` (pattern, wording, when); a shared Pattern can have none, when the reply told the Pattern but gave no Prediction, so make one then; (2) reactions are in `pattern_reactions` and are worth points through `reaction_points` in `core/pattern_scoring.py`, but nothing adds them to a shared Pattern's score yet: do that where this issue reads the score to confirm or close; (3) `patterns.shared_at` says when it was first told; (4) the Reply Plan isn't shown shared Patterns yet (only the ready one and contested ones), so it can't follow one up after the Recent Messages have passed; (5) a contested Pattern stays contested even when they later agree.

- 25 Nov 2026 (start, branch `pattern-09-prediction-follow-up`): plan.
  1. **Follow-up.** At Conversation end, code (`core/predictions.py`, pure rules) writes a Curiosity with the new aim `prediction` for each shared Pattern's open Prediction: not before the Prediction's day + `prediction_follow_up_wait_days` (7), last day + `prediction_follow_up_drop_days` (21) (`curiosities.not_after`, so a late one is never offered). It carries the Pattern's approved wording and the Prediction, since the Reply Plan isn't shown shared Patterns. Offered only while Pattern sharing works.
  2. **Dropped.** A follow-up not asked by its last day is closed and its Prediction is marked "not followed up" (settled, no weight). One asked and never answered ends the same way at that day.
  3. **Outcome.** The tagging step is shown the open Predictions and answers `prediction_outcomes` (came true, didn't, hasn't come up); code keeps one only for a Prediction it showed. Came true = one strong sign for, didn't = one strong sign against (fading like reactions); "hasn't come up" adds nothing and starts a new wait from that day.
  4. **Confirm / close.** Right after reactions are settled, code scores each shared Pattern with its Observations, reactions and Prediction outcomes: under the floor → closed; `predictions_to_confirm` (2) came true, or `pattern_confirm_points_after_sharing` (300) from Observations tagged after it was shared → confirmed. The log keeps a `reason` for each. A closed Pattern that was once shared is never moved again by scoring.
  5. **New Prediction.** A shared Pattern with no open Prediction (the last settled, or the sharing reply gave none) gets a Curiosity telling the reply to give one from the Pattern Type's wording; a small check after the message (like the shared check) keeps it as worded. Never after the User asked Zeph to drop one for that Pattern.
  6. **Portrait.** Confirmed Patterns of Pattern Types go into the Portrait's input in their approved wording; shared ones don't.
