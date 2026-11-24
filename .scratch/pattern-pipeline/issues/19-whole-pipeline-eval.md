# 19 — A whole-pipeline Eval with made-up Users who have hidden true Patterns

Status: ready-for-agent
Track: B
Blocked by: 08

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 88). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

A new Eval kind that checks the pipeline end to end. A case is a made-up User with a hidden set of true Pattern Types and a script of several Conversations (with the clock moved between them). It runs the real reply path and Conversation-end steps, then checks which Patterns became ready or shared. A case passes when every ready Pattern is one of the true ones; the run reports how many true ones were found. Target: at least 70% of ready Patterns true. Start with 5 made-up Users.

Its limit goes in `docs/pattern-evals/README.md`: a model playing the User and a model tagging them tend to agree, so this catches breakage, not truth. It costs more than other Evals: remind the owner and show the estimate before any run.

## Acceptance criteria

- [ ] The Eval kind runs from the Dashboard and the terminal, with Variants
- [ ] A case scripts several Conversations for one made-up User and moves the clock between them
- [ ] The result lists each Pattern that became ready or shared and whether it was one of the true ones, and how many true ones were missed
- [ ] 5 starting cases are seeded, at least one with two look-alike true Patterns and one with none
- [ ] The estimate is shown before the run
- [ ] The guide's limits section covers this Eval
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `08-sharing-a-ready-pattern.md`

## Comments
