# 26 — Users over the daily message limit still get Check-ins

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md` (a caveat left in `issues/archive/13-usage-limits.md`)

## Symptom

Once a User reaches the Daily Message Limit, their messages get the Limit Reply ("I'm honestly wiped for today…"). But the Check-in scheduler doesn't look at the limit, so the Companion can still message the User first later that same day.

That reads oddly in character: Zeph says it needs a rest, then reaches out anyway. If the User replies to that Check-in, they get the Limit Reply again.

Check-ins also cost tokens (they go into the User's Usage), so they keep adding cost after the limit.

## What the spec says

Nothing. Issue 13 and the PRD cover the limit for incoming messages only. Check-ins aren't mentioned.

## Decisions (from `/grill-with-docs`, 2026-11-13)

- **Used up = count reached.** A User has used up today's Daily Message Limit once their message count for their day has reached it, even if no message was turned away yet. (A reply would get the Limit Reply straight away.)
- **No Check-ins for the rest of that day.** This covers the "would you like fewer?" message too. The limit is checked before the Check-in model is asked, so no tokens are spent.
- **One Skipped Check-in per day, User stays due.** Unlike other skips, it does not wait a full frequency gap. The User stays due, so a Check-in can come on their next day (still respecting Quiet Hours, pause, etc.). Only one such skip is recorded per User per day, not one per scheduler tick.
- **Both sides see why.** Admin reason in the Check-in Log: "User had used up today's Daily Message Limit". The User's "Recent check-ins" shows "Skipped — you'd reached today's message limit" (fixed Dashboard text, not Admin-set). Other skips still show "Skipped — gave you some space".
- **Check-ins don't count toward the limit.** A reply to a Check-in counts as one of the User's messages, as now.
- **No "near the limit" rule.** A User below the limit gets Check-ins as normal.
- A limit skip doesn't count toward the Ignore Threshold (skips are already passed over).
- No ADR: easy to reverse. Glossary updated (Skipped Check-in, Daily Message Limit).

## Acceptance criteria

- [ ] A due User whose message count for their day has reached the Daily Message Limit gets no Check-in; one Skipped Check-in is recorded with the limit reason, and the User stays due.
- [ ] Further scheduler ticks that same User-day record no more limit skips and send nothing.
- [ ] On the User's next day (outside Quiet Hours, not paused, no open Conversation), the Check-in is decided as normal.
- [ ] A due User at the Ignore Threshold who has used up the limit gets no "would you like fewer?" message that day; they get the limit skip instead, and the question can come on their next day.
- [ ] The Check-in model is not called for a User who has used up the limit.
- [ ] A User one message below the limit gets Check-ins as normal; sending a Check-in doesn't change their message count.
- [ ] Admins see the limit reason for the skip in the Check-in Log.
- [ ] The User's "Recent check-ins" on the Dashboard shows "Skipped — you'd reached today's message limit" for a limit skip, and "Skipped — gave you some space" for other skips.
- [ ] A limit skip doesn't count toward the Ignore Threshold.
- [ ] Verified in the running app (`/run`).

## Comments

- 2026-11-13: Grilled with docs. Decisions and acceptance criteria above; ready to implement.
