# 26 — Users over the daily message limit still get Check-ins

Status: needs-triage

## Parent

`.scratch/mvp/PRD.md` (a caveat left in `issues/archive/13-usage-limits.md`)

## Before deciding on a solution

Run `/grill-with-docs` on this issue first. The user wants to grill the problem with the docs before a solution is picked, so don't start on a fix until that is done.

## Symptom

Once a User reaches the Daily Message Limit, their messages get the Limit Reply ("I'm honestly wiped for today…"). But the Check-in scheduler doesn't look at the limit, so the Companion can still message the User first later that same day.

That reads oddly in character: Zeph says it needs a rest, then reaches out anyway. If the User replies to that Check-in, they get the Limit Reply again.

Check-ins also cost tokens (they go into the User's Usage), so they keep adding cost after the limit.

## What the spec says

Nothing. Issue 13 and the PRD cover the limit for incoming messages only. Check-ins aren't mentioned.

## Questions for the grilling

- Should a User over the limit get no Check-ins for the rest of their day, or should Check-ins carry on as normal?
- If skipped, should it show as "skipped" in the User's recent Check-ins, and when does the next one come?
- Should a Check-in count toward the Daily Message Limit itself?
- Does the answer change if the User is near the limit but not over it?

## Acceptance criteria

To be written after `/grill-with-docs`.

## Comments
