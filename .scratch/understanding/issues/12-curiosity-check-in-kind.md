# 12 — "Something I've been wondering" Check-in Kind

Status: ready-for-agent

## Parent

`.scratch/understanding/PRD.md`

## What to build

A new fixed-behaviour Check-in Kind opens a Conversation with one of the User's Curiosities. Like the photo Kind, Admins can edit its wording but not what it does. It is offered to the Check-in model only for a User with a waiting Curiosity whose day has come, the Curiosities Feature working, and under the Admin-set Curiosity Check-ins per week (start 1). Sending it marks that Curiosity raised; the User's reply starts a Conversation beginning with that Check-in, as today.

## Acceptance criteria

- [ ] Seeded Kind with fixed behaviour; Admins can edit wording, not behaviour, and Users see it read-only like other Kinds
- [ ] Offered only when a Curiosity is due, the Feature works and the weekly limit isn't reached
- [ ] The sent Check-in uses that Curiosity and marks it raised
- [ ] Weekly limit is an Admin setting
- [ ] Shows in the Check-in Log with its Kind, as other Kinds do
- [ ] Tests at the scheduler/webhook seam with fake clock and scripted Check-in model; checks pass
- [ ] `/run`: a due User with a due Curiosity gets this Check-in

## Blocked by

- `.scratch/understanding/issues/11-curiosities.md`

Note: the Check-in decision is now a pure module (`.scratch/architecture/issues/archive/04-check-in-decision.md`, completed); offer this Kind through it.
