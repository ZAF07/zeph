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

## Comments

### 2026-11-14 — plan (branch `understanding-12-curiosity-check-in-kind`)

- Check-in Kinds get a second fixed flag, `raises_curiosity` (like `sends_shared_photo`: Admins can't set it; a Kind they add never has it). The seed file gets a sixth Kind, "Something I've been wondering".
- Migration 0034: adds the flag, `check_ins.curiosity_id` (set null if the Curiosity is deleted), and on an existing install adds the Kind last unless one has its name.
- New setting `curiosity_check_ins_per_week` (start 1, 0–7) on Settings under Curiosities. "Per week" means the last 7 days, counted from sent Check-ins of a Kind that raises a Curiosity.
- The pure decision (`decide_check_in`) offers that Kind only when Curiosities works for the User, they have a waiting Curiosity whose day has come in their time zone, and fewer than the weekly limit were sent in the last 7 days. The facts are read in bulk for every due User.
- The Check-in model then also sees the due Curiosities, numbered (question, why, sensitivity), and must name one as `"curiosity": <number>` when it picks the Kind; a missing or wrong number is an unusable answer (tried again next tick), like photos. The ask sits in code, so the stored Check-in prompt is unchanged.
- Once the message counts as sent, the Curiosity is marked raised (no Conversation yet). When the User's reply starts the Conversation with that Check-in, the Curiosity is linked to it, so it counts toward the per-Conversation limit and the keeper records how they took it at Conversation end.
- Admin card shows "Asks something Zeph has been wondering"; Users see the Kind on their Check-ins page like the others. The Check-in Log shows its Kind name as today.
