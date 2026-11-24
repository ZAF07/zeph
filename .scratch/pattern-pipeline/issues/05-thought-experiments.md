# 05 — Thought Experiments: Admins manage them, Zeph asks them in chat and as a Check-in

Status: ready-for-agent
Track: A
Blocked by: 04

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 6, 8, 71, 72, 73, 74, 75). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

A Thought Experiment is a made-up scenario written to tell two look-alike Pattern Types apart. Admins manage them on a new Dashboard page: wording, the two Pattern Types it separates, how sensitive it is, whether it is a starter, on or off. They are archived, never deleted. A check on save flags leading wording. A first set is loaded from a seed file.

For an Exploration, code picks the Thought Experiment for the look-alike pair with the most unclear evidence, at most one per Pattern per week (Admin-set). It is asked as a Curiosity in its own words, in chat or through the existing Curiosity Check-in Kind and its weekly limit. The User's answer becomes an Observation of the "what if" kind.

Also in this issue: the agent drafts the first set (about 30, each naming its pair) and writes `docs/thought-experiments/README.md`: how they work, where to find material, how to write a good one, how to manage them, and what an edit changes. The owner then refines the set.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] Admins can add, edit, switch off and archive Thought Experiments on the Dashboard; an archived one is never asked and past tries still show it
- [ ] Each has its wording, two Pattern Types, sensitivity, starter flag and on/off, each with a hint
- [ ] Saving one with leading wording shows a warning the Admin can act on
- [ ] The first set is loaded once from the seed; a seed never overwrites an edited one or brings back an archived one
- [ ] Code picks the Thought Experiment for the pair with the most unclear evidence and never more than the Admin-set number per Pattern per week
- [ ] It is asked in its own words in chat, and can be sent through the Curiosity Check-in Kind within its weekly limit
- [ ] An answer is tagged as an Observation of the "what if" kind
- [ ] `docs/thought-experiments/README.md` exists and covers how they work, sourcing, writing, managing and what an edit changes
- [ ] The owner has reviewed the drafted first set (comment on this issue when done)
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `04-explorations-and-the-agenda.md`

## Comments
