# 11 — A tagging step keeps checked Observations, silently

Status: ready-for-agent
Track: B
Blocked by: 10

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 56, 68, 79, 82). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

A new Conversation-end step, after Life Threads and before Pattern keeping, behind a new Feature, Pattern noticing (off for everyone to start). It is given the Conversation, the Threads it touched and the whole Pattern Catalog, and writes Observations: Pattern Type (one, or two when it can't tell, which makes it unclear) and the sign matched; for or against; the User's exact quote; a context line; who it is about; relationship, power, setting and stance from the fixed lists; the kind of evidence (real story, reported habit, answer to a "what if", own opinion). Code marks one situational when its tags match its Pattern Type's "anyone would do this" description.

Code keeps only Observations whose Pattern Type and sign exist, whose quote is word for word in the User's own texts of that Conversation (never the Companion's), and whose tags come from the lists. Each kept Observation stores the catalog version it was tagged under and stays after Message Retention deletes its message (ADR-0027). Nothing changes in chat. Own prompt, model and thinking switch as Platform Settings.

## Acceptance criteria

- [ ] With Pattern noticing on for a User, ending a Conversation runs the tagging step and saves the valid Observations
- [ ] An Observation with an unknown Pattern Type or sign, a quote not word for word in the User's texts, a quote from the Companion's texts, or a tag outside its list is dropped
- [ ] An Observation naming two Pattern Types is saved as unclear
- [ ] An Observation whose tags match the "anyone would do this" description is saved as situational
- [ ] Each Observation keeps its catalog version, day, Life Thread if any and who it is about
- [ ] The Model Call Log shows the tagging step with how many Observations were tagged and how many dropped, never their words
- [ ] Observations survive Message Retention deleting their message
- [ ] With User Memory off, or Pattern noticing off, the step doesn't run and nothing is deleted
- [ ] Deleting a Life Thread removes its Observations; Delete My Data and Account Deletion remove them all
- [ ] The tagging prompt, model and thinking switch are Platform Settings with hints, and show in the core services list
- [ ] Replies are unchanged
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `10-pattern-catalog-loads-and-admins-read-it.md`

## Comments
