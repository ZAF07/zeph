# 04 — Shared Photos kept and shown on the Dashboard

Status: ready-for-agent

## Parent

`.scratch/photos/PRD.md`

## What to build

Photos that matter to the User become Shared Photos in their User Memory, and Users can see and delete them.

**First, before anything else:** check that an older Telegram file id still downloads, since Shared Photos rely on it (moved here from issue 01, where no days-old photo file id existed yet). Re-download this real photo file id, made on 2026-11-13 by the bot's `sendPhoto` to the owner's chat and stored on photo messages in the app's database, with `getFile` then the file download (or by sending it as a photo update to the running app's webhook):

- `file_id`: `AgACAgUAAxkDAAPzavaxvf82fkk6N0Dp5dgOOelpfO4AAn0VaxsYkrFXUsuQqSSQGPsBAAMCAAN4AAM9BA`
- `file_unique_id`: `AQADfRVrGxiSsVd9` (the eval image `evals/images/weekend-list.jpg`)

Record the date and the result under `## Comments`. If it no longer downloads, stop and raise it: Shared Photos would need a different plan (ADR 0007).

- When a Conversation ends, memory processing (which already reads the descriptions) also picks the photos that matter to the User, with a "why it matters" note for each. Those become Shared Photos: Telegram ids, description, note, caption, sent at, Conversation. Memes, receipts and screenshots aren't kept. The memory processing prompt changes, so the migration resets the stored prompt so the new seed loads (as migration 0012 did for the Check-in prompt).
- With User Memory off, none are kept.
- Shared Photos stay after Message Retention deletes their messages. Delete My Data and Account Deletion delete them.
- The Memories page gets a Photos section: each Shared Photo with the photo (served through the backend, downloaded from Telegram like sticker previews), description, note and date. Delete only, no editing.

## Acceptance criteria

- [ ] Checked first: the 2026-11-13 photo file id above still downloads days later (date and result recorded)
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

### 2026-11-13 — note from issue 03

- Each saved photo (`ChannelPhoto` in a message's `photos`) now holds its own `description`, so memory processing can pick Shared Photos by photo, including photos from an album, without reading them back out of the message text. Album messages read "[photo 1: …] [photo 2: …] caption".
