# 12 — Smart Check-ins

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

Check-ins feel like a friend who knows how you've been. Before sending, the Check-in service reads the User's recent Conversation Summaries and Memory Items and decides either a Check-in Kind and message, or to skip with a reason (e.g. the User asked for space). A skip moves the next attempt to the following scheduled slot. After the Admin-set number of consecutive ignored Check-ins, the Companion sends one "would you like fewer?" message and pauses Check-ins. With User Memory off, only Check-in Kinds allowed without User Memory (casual hello) are used.

Admins manage Check-in Kinds (name, description, allowed without User Memory) and see Check-in sends and skips with skip reasons, never message content.

## Acceptance criteria

- [ ] The Check-in service chooses a Check-in Kind using recent Conversation Summaries and Memory Items
- [ ] The service can decide to skip; the reason is recorded and the next attempt moves to the following slot
- [ ] After the configured number of consecutive ignored Check-ins, one "would you like fewer?" message is sent and Check-ins pause; a User reply resets the count
- [ ] With User Memory off, only Check-in Kinds allowed without User Memory are chosen
- [ ] Admins can add, edit and remove Check-in Kinds and set the ignore threshold
- [ ] Admins can see Check-in sends and skips with reasons, never message text
- [ ] Seam 2 tests with a fake chat model and clock cover: kind chosen and sent, skip recorded and rescheduled, ignore threshold → pause message, User Memory off → casual hello only
- [ ] Seam 3 tests cover the admin Check-in pages
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/04-admin-area-foundation.md`
- `.scratch/mvp/issues/11-basic-check-ins.md`
