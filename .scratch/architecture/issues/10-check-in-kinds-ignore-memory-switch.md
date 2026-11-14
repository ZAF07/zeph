# 10 — Check-in Kinds ignore the User Memory switch

Status: ready-for-agent

## Parent

Follow-up to issue 02 (User Memory off means "stop learning, keep using"), decided with the user on 14 Nov 2026. `CONTEXT.md` (Check-in Kind) is already updated.

## What to build

User Memory off only means "don't learn anything new about me from now on". Memories already saved, and not deleted by the User, are used everywhere, Check-ins included. So the User Memory switch no longer limits which Check-in Kinds can be sent.

- Every Check-in Kind can go to a User whichever User Memory switch is off (the User's or the Admin's).
- Kinds that send a Shared Photo go to a User who has Shared Photos and has Photo Viewing working. User Memory no longer matters for them.
- Remove "allowed without User Memory" completely. It has no meaning now:
  - the Kind field and its database column (new migration)
  - the admin API and the "Allowed when memory is off" box on the Check-in Kinds admin page
  - the seed data and its comments (`seed/check_in_kinds.yaml`)
- Check the reply note for Features that aren't available (`reply_features_unavailable_note`). With the Admin's switch off it names "User Memory", which could lead the Companion to say it can't remember things it still uses. Make sure the reply only says it can't learn new things.

## Decisions

- Memory off = "stop learning". Never "stop using". This applies to every place saved memories are read.
- Photo Viewing stays separate: with it off, Shared Photos aren't used.

## Acceptance criteria

- [ ] With either User Memory switch off, every Check-in Kind can be chosen, and the Check-in still sees saved memories
- [ ] With either switch off, a "look back at a photo" Kind is offered when the User has Shared Photos and Photo Viewing works
- [ ] With Photo Viewing off, photo Kinds aren't offered
- [ ] "Allowed without User Memory" is gone from the code, the database (migration), the admin page and the seed data
- [ ] With the Admin's switch off, a reply never claims it can't remember saved memories
- [ ] Tests for each switch combination; backend and Dashboard checks pass
- [ ] `/run`: with each switch off, a follow-up Check-in about a saved memory is sent, and the admin Check-in Kinds page has no memory box

## Blocked by

None. Touches `core/check_ins.py`, as issue 04 does. Doing this first leaves issue 04 with fewer rules to move.
