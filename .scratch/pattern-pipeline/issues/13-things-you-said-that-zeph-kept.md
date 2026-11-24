# 13 — "Things you said that Zeph kept": Users see and delete their kept quotes

Status: ready-for-agent
Track: B
Blocked by: 11

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 20, 51, 52, 53, 54, 55, 58). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Quotes kept as evidence are the User's own words, so they must see and be able to delete them even while the Pattern is hidden (ADR-0027). A new list on the Memories page shows every kept quote with its context line (shown apart, as Zeph's note) and day, with no Pattern named. Deleting one removes the Observation and scores its Pattern again.

Wherever Message Retention is explained, Copy says plainly that quotes kept as evidence stay until deleted. Before Pattern noticing starts for an existing User, they are told what has changed.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] The Memories page lists every kept quote with its context line and day, newest first, with no Pattern Type or Pattern named
- [ ] The quote and Zeph's note are shown apart
- [ ] A User can delete a quote; it is gone at once and can't come back from a Conversation end already under way
- [ ] The list works whether User Memory is on or off
- [ ] New Copy slots hold the list's title, explanation and empty state, and the retention wording names kept quotes
- [ ] An existing User is told what changed, in chat or on the Dashboard as agreed with the owner in this issue, before their first Observation is kept
- [ ] Admins see only how many kept quotes a User has
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `11-tagging-step-keeps-observations.md`

## Comments
