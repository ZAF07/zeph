# 06 — "Look back at a photo" Check-in

Status: ready-for-agent

## Parent

`.scratch/photos/PRD.md`

## What to build

A new Check-in Kind that reaches out about one of the User's Shared Photos ("saw this again, how's the monstera doing?").

- A seeded Check-in Kind "look back at a photo", not allowed without User Memory. Admins can edit or turn it off like other Kinds.
- The Check-in decision sees the User's Shared Photo descriptions. When it picks this Kind, it names one Shared Photo, which is sent with the Check-in message.
- If the photo can't be sent, the Check-in message still goes out and the error is logged.

## Acceptance criteria

- [ ] A User with Shared Photos can get this Check-in, with one of their own Shared Photos and a short message
- [ ] A User with User Memory off, or no Shared Photos, never gets it
- [ ] Admins see and can edit or turn off the Kind; existing installs get it
- [ ] Seam 2 tests cover sending, User Memory off, no Shared Photos and a failed photo send
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/photos/issues/05-send-photo-back.md`
