# 15 — Decision shape in the Model Call Log

Status: ready-for-agent

## Parent

`.scratch/understanding/PRD.md`

## What to build

The Model Call Log's Understanding entry shows the shape of the decision, never the words: the Need picked, the mood intensity and whether the cause was known, how many Life Threads were reminded, how many were brought up (and lead or weave), how many were left alone, how many held back, and how many `look_up_past` phrases were asked for. This is for every User, as ADR-0010 and PRD story 68 promise ("Need picked, how many Threads found, whether one was raised, which tools were called").

Today the decision shape is only the tools called. Issue 03 left the rest "to the Understanding slices", but issues 04 (Needs) and 08 (Life Threads) did not add it.

## Acceptance criteria

- [ ] The Understanding entry in a trace shows the Need, intensity, cause known, and the counts above, for a plain User and for an Admin
- [ ] No titles, stories, nuance or mood words appear in a plain User's entry
- [ ] Admin Model Call Log page shows them; Vitest + RTL tests
- [ ] Tests at the webhook and Admin API seams; checks pass
- [ ] `/run-dashboard`: open a trace and see the decision shape

## Blocked by

- `.scratch/understanding/issues/08-life-threads-and-being-reminded.md` (completed)
