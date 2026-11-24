# 01 — Each Need says how Curiosities are treated, and a picked Curiosity is part of the plan

Status: ready-for-agent
Track: A
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 1, 11, 76, 81). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Zeph is passive because a Curiosity can be dropped twice (the Reply Plan is told to leave it out unless the moment is right, then the Reply gets it as an optional extra) and a model writes it with nothing to aim at (ADR-0026). This slice changes its standing. It needs no Pattern Catalog.

Each Need gets an Admin-set field for how Curiosities are treated while it is picked: ask by default, only if it fits, or never (test the water comes in issue 02). Under ask by default the Reply Plan must bring up a due Curiosity or give its reason for not doing so. A Curiosity the Reply Plan picks reaches the Reply at the Reply Plan's level of the priority order, not among the optional extras. Every Curiosity records its aim (a commitment to follow up, a look-back, a guess to check, an unmade next Move; Exploration and Prediction aims come later), and the keeping step makes none without one. The Model Call Log's Reply Plan shape records how many Curiosities were offered and whether one was asked.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] On the Needs admin page each Need has a Curiosities field with a hint, saved and applied from the next reply; Being heard starts as never, the fallback Need as only if it fits, the rest as agreed with the owner in the issue
- [ ] With a Need set to ask by default and a Curiosity due, the Reply Plan is told to ask one or say why not, and its reason is saved when it doesn't
- [ ] With a Need set to never, no Curiosity is offered to the Reply Plan
- [ ] A picked Curiosity appears in the Reply's instructions at the Reply Plan's level, not under optional extras, and the reply asks it
- [ ] The existing rules still hold: one question per reply, the per-Conversation limit, never while struggling
- [ ] Every new Curiosity has an aim; the keeping step saves none without one; existing waiting Curiosities are given an aim by migration and none are lost
- [ ] The Model Call Log shows Curiosities offered and asked for each reply
- [ ] A Variant can override a Need's Curiosities field in an Eval Run
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

None - can start immediately

## Comments
