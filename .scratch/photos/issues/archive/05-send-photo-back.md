# 05 — Send a Shared Photo back

Status: completed

## Parent

`.scratch/photos/PRD.md`

## What to build

The Companion can now and then send a User's own Shared Photo back, the way a friend brings up an old memory.

- The reply sees descriptions of the User's relevant Shared Photos, picked the same way relevant Memory Items are, so it can bring them up in words too.
- The reply is offered a `send_photo` tool when the User has Shared Photos in use. It sends only that User's own Shared Photos, at most one per reply, after the text (like stickers), using Telegram's file id.
- The tool's description is an Admin-managed setting: use it rarely and never when the User is struggling.
- If Telegram refuses the photo, the text reply still goes out and the error is logged.

## Acceptance criteria

- [x] The reply can mention a relevant Shared Photo and send it back, at most one per reply
- [x] A Shared Photo of another User can never be sent, even if the model asks for it
- [x] With User Memory off, no Shared Photos are shown to the reply and the tool isn't offered
- [x] A failed send still delivers the text
- [x] The tool description is editable on the admin Prompts page
- [x] Seam 1 tests cover sending, the one-per-reply rule, other Users' photos and failure; adapter test for Telegram send photo
- [x] A Persona Eval: a struggling User with Shared Photos gets no photo sent back (`make eval`)
- [x] `make check` passes
- [x] Verified in the running app via `/run`

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

### 2026-11-13 — evidence

- `make check` on the branch rebased on `origin/main` (12da532): ruff, ruff format, mypy pass; pytest 485 passed; web lint, prettier, typecheck pass; vitest 299 passed. `pnpm build` passes.
- Seam 1 `tests/test_send_photo_back.py` (8 tests): when the picker picks "Shared Photos" the reply's instructions hold the photo's description and note, the `send_photo` tool lists it as "1. …" under the Admin description, and the photo goes after the text by its file id and is in the next reply's history; not picked → not shown, no tool; two picks → only the first is sent, the second is told "already", and the photo comes before a sticker; another User's photo isn't listed and asking for number 2, its ID or its file id sends nothing; User Memory off → no picking call, nothing shown, no tool; Telegram refusing → the text still goes, "Could not send a Shared Photo" is logged, nothing saved; edited tool and group descriptions are used and listed on the Photo viewing and Memory retrieval cards. Adapter `tests/adapters/test_telegram_chat_channel.py`: `sendPhoto` with `{chat_id, photo: file_id}`; a 400 raises. Loader tests in `tests/test_eval_helpers.py`.
- `make eval` (real DeepSeek): Safeguard 32/32, Persona 21/21 (new case `struggling-with-shared-photos` passes `no_photo_when_struggling`), Knowledge 8/8, Photo descriptions 1/1, Settings 11/12. The one miss, `moved-to-london` (no time zone tool called), has no Shared Photos so `send_photo` is never offered; it passed 3 of 3 reruns, so it's model flakiness. The new case first passed without the tool ever being offered (the picker didn't pick the photo for "mum's back in hospital"), so the case now mentions the photo and the eval fails if `send_photo` was never offered; then it passed 3 of 3 runs with the tool on offer.
- `/run` (worktree stack, real DeepSeek and real Telegram, posting to the worktree webhook as the owner, whose chat received the replies): a connected owner with one Shared Photo using the real weekend-list file id (made 2026-11-13). A happy message about the list got a reply with no photo (the seeded description says "rarely"). With the tool description set for the run to "always send", "remember my weekend list?" got text, then the real photo via `sendPhoto`, saved as an outgoing photo message; no errors. With the file id broken, the text still went out and the log showed "Could not send a Shared Photo" with Telegram's 400. With User Memory off no photo was sent, but the model typed the saved "[photo: …]" marker back as text; the saved note was changed (see Decisions), and after a rebuild the same steps sent the photo with memory on and, with memory off, sent nothing and copied nothing (2 tries). Admin Prompts page (Playwright, signed-in Admin, 1280 px): the Photo viewing card shows "send_photo tool description" and the Memory retrieval card "Shared Photos description for memory retrieval"; an edit saved, stayed after reload, and the original was put back; no page errors. Cleaned up: the setting reset to its seed, the run's Clerk user deleted.
- Code review (`/code-review`, Standards and Spec in parallel): no hard rule breaks; nothing missing. Fixed: the Photo viewing card test checks both extra prompts again; the `add_shared_photo` helper documents its arguments. Not changed: see Decisions.

### Decisions

- "Picked the same way relevant Memory Items are": Shared Photos are one more pickable group, "Shared Photos", in the existing picking call (described by a new Admin setting, `shared_photos_memory_description`). When picked, all the User's Shared Photos go in, as all items of a picked category do. No prompt change, so no migration.
- The `send_photo` tool is offered only when that group is picked, so the reply sees and can send only photos that fit the message. If the picking call fails, no photo is offered for that reply.
- A sent photo is saved as "[You sent them back their own photo with the send_photo tool. It shows: …]", not "[photo: …]". With "[photo: …]" the model copied it out as text 1 of 4 times in a probe (and once in the real run); this wording, 0 of 4.
- When the tool isn't offered on a later turn (e.g. User Memory turned off mid-Conversation), the model sometimes says it can't send photos and "shouldn't have pretended earlier". Rare; not changed.
- The eval client now uses `CompanionTestClient`: since aa8ef25 `connect_telegram` needs it, so every Persona Eval failed at sign-up on main. Fixed here as it blocked this issue's eval.
- Not changed from review: model-facing short texts (tool replies, section headers) stay in code like the sticker and memory ones; `SendPhotoChoice` mirrors `StickerChoice`; an Admin Memory Category literally named "Shared Photos" would be picked together with the group.
- Photo Viewing (issue 07) doesn't exist yet; it must also stop Shared Photos being shown and sent when off.

## Completion

- Completed: 2026-11-13
- Commit: fc4d015 "Photos issue 05: the Companion can send a User's own Shared Photo back", review fixes ae1e3c8 "Photos issue 05 review fixes: the Photo viewing card test checks both extra prompts in order again, and the add_shared_photo test helper documents its arguments", archive in the commit "Photos issue 05 done: archive issue with test, eval, run and review evidence" on branch `photos-05-send-photo-back`
