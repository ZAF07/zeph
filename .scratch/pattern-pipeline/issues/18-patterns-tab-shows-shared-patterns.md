# 18 — The Patterns tab shows Patterns being tested, confirmed, disagreed with and that didn't hold up

Status: ready-for-agent
Track: B
Blocked by: 08

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 45, 46, 47, 48, 49, 50). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Users see a Pattern only once the Companion has told them about it. The Memories page's Patterns tab shows: shared ones as being tested, with their quotes, the Prediction and how it went; confirmed ones with their evidence and Prediction record; contested ones as "you disagreed", where the User can delete it or turn silent gathering off; and closed ones only if they were ever shared, as "didn't hold up". Never a score or percentage: words and evidence only. Noticed, suspected, ready and unmatched Patterns never show.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] The tab shows shared, confirmed, contested and once-shared closed Patterns, each under its own wording
- [ ] Each shows its quotes grouped by part of life, its Prediction and how it went
- [ ] No score, percentage or state name from the code is shown
- [ ] Noticed, suspected, ready, never-shared closed and unmatched Patterns are not returned by the API at all
- [ ] A User can delete any shown Pattern; it is gone at once and the User Portrait is rewritten without it
- [ ] The contested section has the silent gathering switch
- [ ] Confirmed Patterns from before this work still show
- [ ] New Copy slots hold every heading, label and empty state
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `08-sharing-a-ready-pattern.md`

## Comments
