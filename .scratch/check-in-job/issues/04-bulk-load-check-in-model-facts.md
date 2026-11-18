# 04 — Facts for the Check-in model are read for all due Users at once

Status: needs-triage

> **Owner: run `/grill-with-docs` before picking this up.** See `.scratch/check-in-job/PRD.md` for the findings and options.

## Parent

`.scratch/check-in-job/PRD.md`

## What to build

What the Check-in model is told about each User (recent Check-ins, User Portrait, Memory Items, Conversation Summaries, Shared Photos, due Curiosities) is read for all due Users in one query per kind of fact, the same way `_gather_facts` already reads the planning facts. Memory Categories are read once per tick, not once per User. The number of queries for a tick then stays the same however many Users are due. What the model is told must not change.

## Acceptance criteria

- [ ] The queries for a tick don't grow with the number of Users sent to the Check-in model.
- [ ] The text the Check-in model is given for a User is the same as before.
- [ ] Tests cover several Users at once, including ones with no memory, photos or Curiosities.
- [ ] A `/run` on copied data, with issue 01's logging, shows the query count and tick time before and after.

## Blocked by

- `.scratch/check-in-job/issues/01-tick-timing-and-backlog-logged.md`

## Comments
