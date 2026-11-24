# 09 — Zeph follows up a Prediction, and Predictions that came true confirm a Pattern

Status: ready-for-agent
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
