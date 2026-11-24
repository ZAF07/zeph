# 02 — Test the water, pace between Curiosities, and backing off after brush-offs

Status: ready-for-agent
Track: A
Blocked by: 01

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 9, 10, 12, 13, 14, 15, 77). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Being proactive must not turn banter into an interview. This slice adds the fourth choice for a Need's Curiosities field and the rules for how often Zeph asks, all as code with Admin-set numbers.

Test the water: Zeph may drop one light opener; if the User doesn't engage, none for the rest of the Conversation. Just chatting starts on it. Pace: a fewest replies between two Curiosities (start 3). Follow-ups on a story the User is telling right now (the Get curious Move) don't use the Curiosity budget and have their own cap per Conversation (start 3). Backing off: after brush-offs in a row (start 2), none for the rest of the Conversation and the spacing doubles for a time (start 3 days); one engaged answer ends it. A topic the User asked to drop stays dropped.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] A Need can be set to test the water; Just chatting starts on it
- [ ] Under test the water at most one Curiosity is offered as a light opener; after the User doesn't engage, none are offered for the rest of that Conversation
- [ ] No Curiosity is offered until the Admin-set number of replies has passed since the last one
- [ ] Get curious follow-ups on the User's current story don't count toward the Curiosity limit and stop at their own cap
- [ ] After the Admin-set number of brush-offs in a row, none are offered for the rest of the Conversation and the spacing is doubled for the Admin-set time
- [ ] One engaged answer returns the spacing to normal
- [ ] Each new number is a Platform Setting with a hint, and can be overridden in an Eval Variant
- [ ] The pace and backing-off rules are pure functions with their own tests
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `01-needs-say-how-curiosities-are-treated.md`

## Comments
