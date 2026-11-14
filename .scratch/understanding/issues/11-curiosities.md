# 11 — Curiosities

Status: ready-for-agent

## Parent

`.scratch/understanding/PRD.md`

## What to build

The Companion has things it's been meaning to ask (`CONTEXT.md` "Curiosity").

- **New Feature "Curiosities"** (for everyone and per User, like Personal Stickers). When it doesn't work for a User, none are made or raised; none are deleted.
- **Written at Conversation end:** what to ask and why, a "not before" day or anytime, sensitivity, and the Memory Item or Thread it came from. Raised ones get how the User took them; ones no longer relevant are closed. The "waiting at once" limit drops the oldest. Not while User Memory doesn't work for the User; waiting ones are still used.
- **Raised in Conversations:** the Understanding sees waiting Curiosities whose day has come, with how many were already raised in this Conversation, and may put one in `bring_up` (open with it, weave it in) or leave it for a better moment. At most the Admin-set number per Conversation (start 1). Marked raised when the reply is sent.
- **Internal:** not shown to Users, not in User Memory. Deleting the source Memory Item or Thread removes its Curiosities. Delete My Data and Account Deletion remove them.
- Settings: raised per Conversation, waiting at once. (Curiosity Check-ins per week comes with issue 12.)

## Acceptance criteria

- [ ] Conversation end creates, updates and closes Curiosities (scripted output), honouring the waiting limit
- [ ] A Curiosity is offered to the Understanding only once its day has come, and not after the per-Conversation limit is reached
- [ ] Raised Curiosities record the reaction at the next Conversation end
- [ ] Deleting the source Memory Item or Thread removes its Curiosities
- [ ] Feature off (for everyone or one User): none made or raised
- [ ] User Memory off: none made; waiting ones still offered
- [ ] No Dashboard or User API exposes them; Delete My Data and Account Deletion remove them
- [ ] Checks pass
- [ ] `/run`: "big presentation Thursday" in one Conversation; after it ends and Thursday passes (timestamps shifted), the next Conversation raises it

## Blocked by

- `.scratch/understanding/issues/08-life-threads-and-being-reminded.md`
