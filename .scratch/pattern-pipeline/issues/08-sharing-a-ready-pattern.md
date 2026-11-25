# 08 — Zeph shares a ready Pattern with the User's quotes and a Prediction

Status: ready-for-agent
Track: A
Blocked by: 07

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 33, 34, 35, 36, 38, 39, 40, 41, 42, 43, 44). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Behind a new Feature, Pattern sharing (works only when Pattern exploring does). The Reply Plan is offered only ready Patterns to share and picks the moment; other Patterns in mind are marked not to be said, though the Read may think with them. A shared Pattern is Zeph's view, never fact, in three parts: the Pattern in warm words from its Pattern Type's approved wording fitted to the User's own people, two or three of their quotes from different Life Threads, and one Prediction. Zeph asks what would prove it wrong. A small check after the Reply says whether it was shared; only then does it move to shared and count toward the Admin-set weekly limit (start 1). A ready Pattern with no good moment within an Admin-set time (start 5 days) goes out as a Check-in.

Reactions: the model reads agreed, pushed back or brushed off; code counts agreement as a weak sign for, and makes a rejected Pattern contested: never offered again unless the User raises it. A contested Pattern keeps gathering evidence only while the User's own switch allows (on to start, on the Dashboard and in chat).

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] With Pattern sharing on, a ready Pattern is offered to the Reply Plan; a Pattern that isn't ready is marked not to be said and never reaches the Reply as a Pattern
- [ ] A shared Pattern's reply has the Pattern in the approved wording, two or three quotes from different Life Threads, one Prediction, and asks what would prove it wrong
- [ ] It is worded as Zeph's view, with no clinical words
- [ ] The after-reply check decides whether it was shared; if not, it stays ready and doesn't count toward the limit
- [ ] No more than the Admin-set number of new Patterns are shared in a week
- [ ] It is never shared while the User is struggling
- [ ] A ready Pattern not shared within the Admin-set time is sent as a Check-in
- [ ] Agreement adds a weak sign for and never confirms by itself
- [ ] Rejection makes the Pattern contested and it is never offered again unless the User raises it
- [ ] The User's switch for silent gathering on contested Patterns works on the Dashboard and in chat; off stops new Observations for them
- [ ] The Model Call Log's Reply Plan shape records whether a Pattern was offered and shared
- [ ] With Pattern sharing off, nothing is shared and ready Patterns wait
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `07-ready-gate.md`

## Comments

- 25 Nov 2026 (from issue 07): the ready gate is built (`core/ready_gate.py`). For sharing: (1) a ready Pattern is judged again only at a Conversation end or when Observations are deleted, so look again before sharing (`ReadyKeeper.look` does it with no model call), and check struggling there, which the gate doesn't; (2) "not rejected" has no source yet: make a rejected Pattern contested and the gate will never look at it; (3) the narrowing is on the Pattern (`CatalogPattern.narrowings`: tag, holds with, not with) for the wording; (4) pick quotes from Observations that are not `excluded` and not on a ruled-out topic the User didn't raise.
