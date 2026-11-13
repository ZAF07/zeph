# 04 — Shared Photos kept and shown on the Dashboard

Status: ready-for-agent

## Parent

`.scratch/photos/PRD.md`

## What to build

Photos that matter to the User become Shared Photos in their User Memory, and Users can see and delete them.

- When a Conversation ends, memory processing (which already reads the descriptions) also picks the photos that matter to the User, with a "why it matters" note for each. Those become Shared Photos: Telegram ids, description, note, caption, sent at, Conversation. Memes, receipts and screenshots aren't kept. The memory processing prompt changes, so the migration resets the stored prompt so the new seed loads (as migration 0012 did for the Check-in prompt).
- With User Memory off, none are kept.
- Shared Photos stay after Message Retention deletes their messages. Delete My Data and Account Deletion delete them.
- The Memories page gets a Photos section: each Shared Photo with the photo (served through the backend, downloaded from Telegram like sticker previews), description, note and date. Delete only, no editing.

## Acceptance criteria

- [ ] At Conversation end, picked photos become Shared Photos with a note; others aren't kept
- [ ] With User Memory off, none are kept
- [ ] Shared Photos survive Message Retention; Delete My Data and Account Deletion remove them
- [ ] The Memories page shows each Shared Photo with its photo, description, note and date, and deletes one
- [ ] An existing install loads the new memory processing prompt
- [ ] Seam 2 tests cover picking, User Memory off and retention; seam 1 tests cover list, photo and delete endpoints and Delete My Data; seam 3 tests cover the Photos section
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/photos/issues/01-companion-sees-a-photo.md`
