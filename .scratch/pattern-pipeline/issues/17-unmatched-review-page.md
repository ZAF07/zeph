# 17 — Admins review what Zeph keeps noticing that fits no Pattern Type

Status: ready-for-agent
Track: B
Blocked by: 16

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 84, 85). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

An Admin page lists what keeps turning up unmatched, so the catalog can grow. To protect privacy each entry is a general description with no User details (no names, quotes, places or dates) and how many Users it appeared for. The description is written when the unmatched Pattern is kept, about the way of acting and never about the person, and like descriptions are grouped by meaning. The Admin marks each entry: new Pattern Type, folded into an existing one (naming it), or dropped. Writing the YAML stays manual. The model-suggestions feature is out of scope (parked in the decisions file).

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] The page lists unmatched entries with a general description and a count of Users, most Users first
- [ ] No entry shows a User's name, quote, or any detail that could identify them; a test checks the description is built only from the general wording
- [ ] Like descriptions from different Users are grouped into one entry
- [ ] An Admin can mark an entry as new Pattern Type, folded into a named Pattern Type, or dropped, and filter by that
- [ ] A dropped entry doesn't return unless it appears for more Users
- [ ] A non-Admin can't reach the page or its API
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `16-existing-patterns-move-across-and-unmatched-patterns.md`

## Comments
