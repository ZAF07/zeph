# 04 — Explorations and the Agenda: Zeph knows what it is trying to learn and comes back to it

Status: ready-for-agent
Track: A
Blocked by: 01, 12

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 2, 3, 4, 5, 7, 29). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Zeph needs to remember what it is exploring. An Exploration is its ongoing effort on one suspected Pattern: what it still needs to learn (an unclear story to settle, a part of the User's life it hasn't seen, a counter-test), each try (which Curiosity, when, whether what came back was useful, vague or brushed off), and what to try next and not before when. The Agenda is the User's active Explorations, at most an Admin-set number (start 3), ranked by code.

After scoring at Conversation end, code keeps the Agenda and writes the next aimed Curiosity for each Exploration, least pushy way first: a follow-up on a story, "would it have gone differently with…", then (issue 05) a Thought Experiment, then "this week, notice when…". A try that gets nothing useful leaves the need open. An Exploration is never worked on two Conversations in a row, waits after a try with nothing (start 3 days), rests after tries with nothing (start 4) and wakes on new evidence. The Reply Plan sees the Agenda with each Exploration's earlier tries on every reply, and Get curious is aimed by its open needs. All behind a new Feature, Pattern exploring, which works only when Pattern noticing does.

## Acceptance criteria

- [ ] A suspected Pattern gets an Exploration with its open needs worked out by code from its Observations (unclear, missing part of life, counter-test)
- [ ] At most the Admin-set number of Explorations are active for a User, ranked by code
- [ ] Code writes an aimed Curiosity for an Exploration's top need; the model only words it
- [ ] Each try is saved with its Curiosity, when it was asked and how it went
- [ ] A try that came back vague or brushed off leaves the need open, and the next try uses a different way after the Admin-set wait
- [ ] The same Exploration is not worked on in two Conversations in a row
- [ ] An Exploration rests after the Admin-set number of tries with nothing, frees its place, and wakes when a new Observation arrives for its Pattern
- [ ] The Reply Plan is given the Agenda with earlier tries, and Get curious is given the open needs
- [ ] An answer to an aimed Curiosity that settles an unclear Observation is tagged as clear at Conversation end
- [ ] With Pattern exploring off for a User, no Explorations or aimed Curiosities are made and none are deleted
- [ ] Delete My Data and Account Deletion remove Explorations
- [ ] Agenda ranking and the Exploration rules are pure functions with their own tests; every number is a Platform Setting with a hint
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `01-needs-say-how-curiosities-are-treated.md`
- `12-patterns-scored-and-moved-by-code.md`

## Comments
