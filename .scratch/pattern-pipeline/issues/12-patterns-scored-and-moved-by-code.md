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

Plan (24 Nov 2026, branch `pattern-12-scoring`, worktree `ai-chat-companion-pattern-12`):

- **One store.** Catalog Patterns live in the existing `patterns` table (ADR-0024 rejects two stores), with a new `pattern_type_id` (one per User and Pattern Type) and `pattern` text made optional. Every old-style reader (Pattern keeping, coming to mind, the Patterns tab, the Portrait, delete-without-evidence) keeps reading only rows with no Pattern Type, so nothing reaches a reply. Issue 16 joins them up.
- **Pattern state** gets all seven values. This issue moves only noticed, suspected and closed; a Pattern in ready, shared, confirmed or contested is left alone.
- **Pure rules** in a new `core/pattern_scoring.py`: an Observation's weight; grouping into situations (a Life Thread; with none, the same person and setting); within one, per direction, only the strongest Observation per person counts, up to the cap of people; the score is the sum; situations counted are those where it showed (weight for it above 0); the state each Pattern should be in: under the floor → closed, at the suspected situations and score → suspected, else noticed. States follow the evidence, so moves go back too (a deletion can take suspected back to noticed, and a closed one whose score comes back over the floor is noticed again).
- **Linking.** No link column: a User's Pattern for a Pattern Type is fed by their Observations naming it, first or second (unclear counts toward both). Any Observation, even against or situational, makes a noticed Pattern. One left with no Observations is deleted; its log stays.
- **Scoring step** at Conversation end, right after tagging, while Pattern noticing works: rescores all the User's catalog Patterns (fading can move them too). Deleting a Life Thread rescores at once.
- **Log** `pattern_moves`, append-only: User, Pattern, Pattern Type, from, to, cause (Conversation tagged, with its ID, or Observations deleted), score and situations at the move, when. No content. Only Delete My Data and Account Deletion remove it.
- **Settings**, whole numbers so the Platform settings page needs no new kind: sign weights in points (weak 30, moderate 70, strong 140; 100 points = decision 29's 1.0), kind of evidence and unclear as percents (100/70/40/30, 25), half-life 75 days, people per Thread 3, suspected 2 situations and 100 points, closed under −150 points. New "Patterns" section on Platform settings; each overridable in an Eval Variant like any editable setting.
- **Admins** see counts per state: the Users API gives counts by state, and the user panel adds a row per state with a count above 0 in the existing "What Zeph holds" style (agreed with the owner, flagged for the designer).
