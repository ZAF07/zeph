# 04 — User Memory and Check-ins as Features

Status: ready-for-agent

## Parent

`.scratch/features/PRD.md`

## What to build

User Memory and Check-ins join the Feature list. These two also have the User's own switch, so a Feature works only when the Admin side allows it and the User has it on.

- An Admin "off" never changes the User's own choice; when the Admin side turns back on, the User's own setting applies again.
- User Memory off by an Admin behaves exactly like the User turning it off: memory retrieval, memory processing at Conversation end and Check-in choice keep and use nothing. Nothing is deleted, and the User can still see and delete their memories on the Dashboard.
- Check-ins off by an Admin: none are decided or sent.
- On the Dashboard, a switch whose Admin side is off shows "Not available on your account" and is disabled. The User API refuses changes to it and changes nothing. The statuses come from the backend; the Dashboard holds no rule.

## Acceptance criteria

- [ ] With User Memory off by an Admin, nothing new is kept or used, existing memories stay viewable and deletable, and the User's own switch is unchanged
- [ ] With Check-ins off by an Admin, no Check-in is sent and the User's Check-in settings are unchanged
- [ ] Turning the Admin side back on restores the User's own choice
- [ ] The Dashboard shows "Not available on your account" with the switch disabled, and the API refuses the change
- [ ] The per-User panel shows "Off: the User turned it off" when only the User's switch is off
- [ ] Seam 1 tests cover the API and memory retrieval; seam 2 tests cover memory processing and Check-ins; seam 3 tests cover the disabled switches
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/features/issues/02-per-user-feature-switches.md`
