# 16 — Existing Patterns move across, and free noticing becomes unmatched Patterns

Status: ready-for-agent
Track: B
Blocked by: 12

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 28, 57, 86). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Production has a real User with Patterns kept under the old rules. A migration keeps every one: confirmed stay confirmed and visible, suspected become unmatched (they were hidden anyway), closed stay closed. A one-off pass, run by an Admin command, matches each to a Pattern Type where one fits.

The Pattern keeping step changes job: it no longer starts, confirms or closes catalog Patterns (code does, from Observations). It only notes what recurs across two or more Life Threads and fits no Pattern Type, as an unmatched Pattern with its evidence. Unmatched Patterns are never ready or shared and stay hidden, but still come to mind and the Read may think with them, as today. When a Pattern Type is added, an Admin command tags stored unmatched evidence again against it.

## Acceptance criteria

- [ ] After the migration every existing Pattern and its evidence is still there; confirmed ones still show on the Dashboard exactly as before
- [ ] Existing suspected Patterns are unmatched and hidden; closed ones stay closed
- [ ] The matching pass links a Pattern to a Pattern Type only where it fits, and reports what it did
- [ ] The keeping step writes only unmatched Patterns; it can't change a catalog Pattern's state
- [ ] An unmatched Pattern still comes to mind and can shape the Read, and is never offered as a Pattern
- [ ] Tagging again against a new Pattern Type turns matching unmatched evidence into Observations, checked like any other
- [ ] The migration is tested against a database holding old-style Patterns
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `12-patterns-scored-and-moved-by-code.md`

## Comments
