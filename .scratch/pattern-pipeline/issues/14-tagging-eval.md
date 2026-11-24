# 14 — A Tagging Eval with its first cases, and the Pattern Evals guide

Status: ready-for-agent
Track: B
Blocked by: 11

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 87, 89). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Everything downstream trusts the tagging step, so it gets its own Eval kind in the existing Eval runner. A case is a made-up Conversation (with any Life Threads it needs) plus the Observations expected: Pattern Type, for or against, unclear or not, situational or not. The real tagging step and code checks run on it. About 40 starting cases in a seed file, including ambiguous ones (must come back unclear), ones with nothing to tag (must come back empty) and ones anyone would do.

Also write `docs/pattern-evals/README.md`: the three layers of testing, what each can and can't show (a model playing a User and a model tagging them tend to agree), and what must be done later (a second rater, 200 labelled Observations, turning the score into a probability from Prediction outcomes, a psychologist's review). Evals cost money: remind the owner and show the estimate before any run.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] Tagging is an Eval kind Admins can run from the Dashboard and the terminal, with cases they can add and edit
- [ ] A case passes only when the Observations kept match what was expected, and its result shows what was tagged and what was dropped
- [ ] About 40 starting cases are seeded, covering clear, ambiguous, nothing-to-tag, against and anyone-would-do-it situations for the Pattern Types that exist
- [ ] A Variant can override the tagging prompt, model and thinking switch
- [ ] The run shows its cost estimate first
- [ ] `docs/pattern-evals/README.md` exists and covers the layers, their limits and what must be done later
- [ ] The owner has corrected the drafted cases (comment on this issue when done)
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `11-tagging-step-keeps-observations.md`

## Comments
