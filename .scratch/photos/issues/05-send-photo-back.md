# 05 — Send a Shared Photo back

Status: ready-for-agent

## Parent

`.scratch/photos/PRD.md`

## What to build

The Companion can now and then send a User's own Shared Photo back, the way a friend brings up an old memory.

- The reply sees descriptions of the User's relevant Shared Photos, picked the same way relevant Memory Items are, so it can bring them up in words too.
- The reply is offered a `send_photo` tool when the User has Shared Photos in use. It sends only that User's own Shared Photos, at most one per reply, after the text (like stickers), using Telegram's file id.
- The tool's description is an Admin-managed setting: use it rarely and never when the User is struggling.
- If Telegram refuses the photo, the text reply still goes out and the error is logged.

## Acceptance criteria

- [ ] The reply can mention a relevant Shared Photo and send it back, at most one per reply
- [ ] A Shared Photo of another User can never be sent, even if the model asks for it
- [ ] With User Memory off, no Shared Photos are shown to the reply and the tool isn't offered
- [ ] A failed send still delivers the text
- [ ] The tool description is editable on the admin Prompts page
- [ ] Seam 1 tests cover sending, the one-per-reply rule, other Users' photos and failure; adapter test for Telegram send photo
- [ ] A Persona Eval: a struggling User with Shared Photos gets no photo sent back (`make eval`)
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/photos/issues/04-shared-photos.md`

## Comments

### 2026-11-13 — note from issue 04

- **Check first, before anything else:** that a days-old Telegram photo file id still downloads, since sending a Shared Photo back relies on it (moved here from issue 04, which could only check it the same day). Re-download `AgACAgUAAxkDAAPzavaxvf82fkk6N0Dp5dgOOelpfO4AAn0VaxsYkrFXUsuQqSSQGPsBAAMCAAN4AAM9BA` (`file_unique_id` `AQADfRVrGxiSsVd9`, made 2026-11-13) with `getFile` then the download, record the date and result here, and stop and raise it if it fails (ADR 0007).
- Shared Photos now exist: `SharedPhoto` (`core/models.py`), listed by `PhotoService.list_shared` and `UserMemoryRepository.list_shared_photos`, each with `file_id`, description, note and caption.

### 2026-11-13 — old file id check

- 2026-11-13 19:16 (+08): `getFile` then the download for `AgACAgUAAxkDAAPzavaxvf82fkk6N0Dp5dgOOelpfO4AAn0VaxsYkrFXUsuQqSSQGPsBAAMCAAN4AAM9BA` worked: `ok: true`, `file_unique_id` `AQADfRVrGxiSsVd9`, 21,343 bytes, a 640×480 JPEG.
- Still the same day it was made (about 2 hours later than issue 04's check), so it proves hours, not days. No days-old file id exists yet; the re-check needs a later date. Nothing suggests ADR 0007 needs a different plan.

### 2026-11-13 — plan (branch `photos-05-send-photo-back`)

- Memory retrieval: when User Memory works and the User has Shared Photos, "Shared Photos" is one more pickable group in the existing picking call, described by a new Admin setting `shared_photos_memory_description`. If picked, the memory section lists each Shared Photo (date, description, note) and `recall` also returns their IDs.
- New `send_photo` tool in `PhotoTools` (like `send_sticker`): lists only those Shared Photos, loaded by the User's ID, by number; first pick wins. Its description is the new Admin setting `send_photo_tool_description` (Prompts page, with Memory retrieval / Photo viewing).
- Delivery: text, then the photo, then any sticker. Telegram refusing is logged and the text still goes; a sent photo is saved as an outgoing photo message "[photo: description]".
- Chat channel port gains `send_photo(chat_id, file_id)`; Telegram `sendPhoto`; fake records it and can fail.
- Persona Eval case: a struggling User with a Shared Photo gets no photo sent back.
