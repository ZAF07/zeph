# 12 — Patterns are scored from Observations and moved between states by code, with a log

Status: ready-for-agent
Track: B
Blocked by: 11

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 21, 22, 23, 24, 25, 32, 80, 83). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

After tagging, code scores each of the User's catalog Patterns from its Observations and moves it between states. Score: each Observation's weight is its sign's strength times its kind of evidence, reduced when unclear, zero when situational, negative when against, fading by a half-life at read time. A situation is one Life Thread (with no Thread, the same person and setting); within a Thread only the strongest Observation per person counts, up to a cap of people. The score is always computed from Observations, never stored as the source of truth.

This issue covers the states noticed, suspected and closed (ready, shared, confirmed and contested come with issues 07 to 09, and the state type has all seven from the start). Every move is saved in an append-only log with its cause. Starting numbers are in `.scratch/pattern-pipeline/grill-decisions.md` (decision 29). Still silent: nothing reaches a reply.

## Acceptance criteria

- [ ] A first Observation for a Pattern Type creates a noticed Pattern for the User
- [ ] A Pattern moves to suspected at the Admin-set situations and score, and to closed under the Admin-set floor
- [ ] Ten Observations about one person in one Life Thread count as one
- [ ] Observations about different people in one Life Thread add weight up to the Admin-set cap, and still count as one situation
- [ ] An unclear Observation counts at the reduced weight toward each Pattern Type; a situational one counts nothing; one against lowers the score
- [ ] Older Observations count for less by the Admin-set half-life
- [ ] Deleting an Observation changes its Pattern's score and state at once
- [ ] Every state move is logged with its cause and is never edited or removed except by Delete My Data and Account Deletion
- [ ] Scoring, counting situations and the state moves are pure functions with their own tests
- [ ] Admins see how many Patterns a User has in each state, never their content
- [ ] Every number is a Platform Setting with a hint and can be overridden in an Eval Variant
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `11-tagging-step-keeps-observations.md`

## Comments
