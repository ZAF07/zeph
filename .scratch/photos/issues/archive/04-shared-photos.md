# 04 — Shared Photos kept and shown on the Dashboard

Status: completed

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

- [x] Checked first: the 2026-11-13 photo file id above still downloads days later (date and result recorded) — checked the same day only (hours, not days); the days-later re-check moved to issue 05, see Comments
- [x] At Conversation end, picked photos become Shared Photos with a note; others aren't kept
- [x] With User Memory off, none are kept
- [x] Shared Photos survive Message Retention; Delete My Data and Account Deletion remove them
- [x] The Memories page shows each Shared Photo with its photo, description, note and date, and deletes one
- [x] An existing install loads the new memory processing prompt
- [x] Seam 2 tests cover picking, User Memory off and retention; seam 1 tests cover list, photo and delete endpoints and Delete My Data; seam 3 tests cover the Photos section
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/photos/issues/01-companion-sees-a-photo.md`

### 2026-11-13 — note from issue 03

- Each saved photo (`ChannelPhoto` in a message's `photos`) now holds its own `description`, so memory processing can pick Shared Photos by photo, including photos from an album, without reading them back out of the message text. Album messages read "[photo 1: …] [photo 2: …] caption".

## Comments

### 2026-11-13 — old file id check

- 2026-11-13 ~17:35 (+08): `getFile` then the file download for `AgACAgUAAxkDAAPzavaxvf82fkk6N0Dp5dgOOelpfO4AAn0VaxsYkrFXUsuQqSSQGPsBAAMCAAN4AAM9BA` worked: `ok: true`, `file_unique_id` `AQADfRVrGxiSsVd9`, 21,343 bytes, a JPEG.
- That file id was made earlier the same day, so this proves only that it lasts hours, not days. The "days later" re-check is moved to issue 05 (sending a Shared Photo back by its file id), which needs it anyway. Nothing here suggests ADR 0007 needs a different plan.

### 2026-11-13 — plan (branch `photos-04-shared-photos`)

- New `SharedPhoto` model and `shared_photos` table (migration 0018): User, Telegram ids, description, note, caption, sent at, Conversation (`SET NULL` when the Conversation goes, so rows outlive it). Migration 0018 also deletes the stored `memory_processing_prompt` so the new seed loads.
- `ChannelPhoto` gains `caption` (kept in the existing `photos` JSON); `PhotoService.read_message` sets it, as it sets the description.
- Memory processing (`core/post_conversation.py`) lists the viewed photos the User sent as "[1] description" under "Photos the person sent", and reads `photos_to_keep: [{photo, note}]` from the answer. `plan_new_shared_photos` skips unknown numbers, missing notes and repeats. The new Shared Photos go in `MemoryChanges.new_shared_photos`, saved in the same step as the summary and Memory Items.
- `UserMemoryRepository` gains list, get and delete for Shared Photos; `delete_data` deletes them; Account Deletion removes them through the `users` cascade.
- `PhotoService` gains `list_shared`, `delete_shared` and `shared_photo_image` (downloads through the chat channel, like sticker previews). Dashboard API: `GET /api/shared-photos`, `GET /api/shared-photos/{id}/image`, `DELETE /api/shared-photos/{id}`; Telegram ids are never sent to the browser.
- Memories page: a third tab, Photos (`SharedPhotosList`, `SharedPhotoPicture`), delete only.

### 2026-11-13 — evidence

- `make check` on the branch rebased on `origin/main`: ruff, ruff format, mypy pass; pytest 446 passed; web lint, prettier, typecheck pass; vitest 297 passed. `pnpm build` passes.
- Seam 2 `tests/test_shared_photos.py`: two photos (a cat with a caption, a receipt) and a processing answer keeping photo 1 make one Shared Photo with its description, note, caption and sent at, and the processing model was shown "[1] cat" and "[2] receipt"; wrongly named picks (unknown number, a string, `true`, no note, a repeat) are skipped; with User Memory off none are kept; after Message Retention deletes every message the Shared Photo is still listed.
- Seam 1 `tests/test_shared_photos.py`: the image is served through the backend from the chat channel's download (content and type); a failed download gives 404; delete gives 204, then 404; another User can't list, see or delete it; sign-in needed; an existing install migrated down to 0017 with an old prompt loads the new prompt after upgrading and seeding. `tests/test_data_deletion.py`: the User's data now includes a Shared Photo, and Delete My Data and Account Deletion leave no `shared_photos` rows. `tests/test_photos.py`: the saved message photo keeps its caption.
- Seam 3 `web/src/components/Memories.test.tsx` (5 new): the Photos tab shows each photo with image, description, note and date; a photo that can't load says so; deletes one; a failed delete keeps it and says so; empty state.
- Code review (`/code-review`, Standards and Spec in parallel): no rule breaks and nothing missing. Fixed: a JSON `true` was read as photo 1; `kept_photos` renamed `new_shared_photos`; the tab text promised "never screenshots, receipts or memes", now says Zeph tries to leave them out; a docstring re-wrapped. Not changed: list and delete stay in `PhotoService`, as the PRD says; the delete/empty-state code in the three Memories tabs is alike (possible shared hook later).
- `/run` (stack rebuilt from this branch on the existing database, real Telegram and DeepSeek): the install was on 0017 with the old prompt; after the restart it was on 0018 and the stored prompt asked for `photos_to_keep`. The house drawing (sent to the owner's chat to get a real file id) was posted to the webhook as a photo from the owner with the caption "my daughter drew our house for me, she's 6 🥹", then the weekend list photo with no caption. Both were described and answered. Conversation times shifted back 2 hours; the scheduler processed it, and the real model kept only the house drawing, with the caption, sent at, Conversation and the note "A drawing their six-year-old daughter made of their house — just the house, sun in the corner, door in the middle; they sent it with tears of pride, and it's the kind of thing that goes on the fridge." The weekend list (a notebook page) wasn't kept. Memories page (Playwright, signed-in plain User given a copy of that Shared Photo): the Photos tab showed the real image (640 px wide, downloaded through the backend), the date, the description and the note at 1280 px and 390 px, with no page errors; delete left the empty state, also after a reload. Cleaned up: the run's Clerk user, and on the owner's account the test Conversation, its summary, its Shared Photo and the made-up Memory Item it added. The house drawing image is still in the owner's Telegram chat.
- Not run: `make eval` (no Eval in this issue's criteria).

### Decisions

- Shared Photos belong to User Memory, so the repository methods live on `UserMemoryRepository` and are saved in the same step as the Conversation Summary. The photo service still owns listing, deleting and downloading them, as the PRD says.
- Only photos that were viewed and have a description are offered to memory processing. When Photo Viewing (issue 07) is off, photos aren't viewed, so none can be kept with no extra check.
- An album's caption is stored on each of its photos. If the album had a video or other file, the caption starts with its marker (e.g. "[video] our trip"), as the Companion read it.
- The same photo sent in two Conversations can be kept twice. The issue didn't ask for this to be prevented; revisit if it happens.
- Image endpoint gives 404 when Telegram can't serve the file, like sticker previews; the Dashboard shows "This photo can’t be shown right now" and keeps the description and note.
- The Photos section is a third tab on the Memories page, matching the other two; the design file has no Photos layout to follow.
- Migration 0018 resets the stored memory processing prompt, so any Admin edits to it are lost, as with 0012.

## Completion

- Completed: 2026-11-13
- Commit: <to be filled in after merge>
