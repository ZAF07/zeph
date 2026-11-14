# 11 — Curiosities

Status: in-progress

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

## Comments

- Branch `understanding-11-curiosities`, worktree `ai-chat-companion-understanding-11` (ports 3210/8210/5642).
- Plan:
  - New `curiosities` table (migration 0032): what to ask, why, not-before day (or none), sensitivity (low / medium / high), state (waiting / raised / closed), reaction, source Memory Item or Life Thread, raised at and in which Conversation. The source columns are foreign keys with `ON DELETE CASCADE`, so every way a Memory Item or Thread is deleted (Dashboard, "forget that" in chat, a memory processing "remove") takes its Curiosities with it.
  - New Feature **Curiosities** (on for everyone at the start, like the other non-plan Features; not in the reply's "unavailable" note, since Users don't know about it).
  - Conversation end: a separate "Curiosity keeping" model call (own Admin prompt and model, step `curiosities` in the Model Call Log), run after Life Thread keeping, only while User Memory and Curiosities work. It sees today's date, the User's Memory Items and the Threads the Conversation touches (to name a source), the waiting Curiosities and those raised in this Conversation, recently raised ones (so it doesn't ask again), and the Conversation. It adds new ones, edits or closes waiting ones, and records how the User took raised ones. Over the waiting limit, the oldest waiting ones are closed.
  - Reply: before the Understanding, the code lists waiting Curiosities whose day has come (in the User's time zone), with how many were raised in this Conversation and the limit; none once the limit is reached or when the Feature is off. The Understanding may put one in `bring_up` as `{"curiosity": n, "how": ...}`; the code caps it at what's left of the limit. The reply gets the question, why, and how to bring it up. It is marked raised after the reply is sent.
  - Settings: `curiosities_per_conversation` (1), `curiosities_waiting_limit` (10) on Settings; prompt and model on Prompts and Models.
  - Delete My Data and Account Deletion delete them; no Dashboard or User API returns them.
