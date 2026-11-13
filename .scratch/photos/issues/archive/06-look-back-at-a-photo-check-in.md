# 06 — "Look back at a photo" Check-in

Status: completed

## Parent

`.scratch/photos/PRD.md`

## What to build

A new Check-in Kind that reaches out about one of the User's Shared Photos ("saw this again, how's the monstera doing?").

- A seeded Check-in Kind "look back at a photo", not allowed without User Memory. Admins can edit or turn it off like other Kinds.
- The Check-in decision sees the User's Shared Photo descriptions. When it picks this Kind, it names one Shared Photo, which is sent with the Check-in message.
- If the photo can't be sent, the Check-in message still goes out and the error is logged.

## Acceptance criteria

- [x] A User with Shared Photos can get this Check-in, with one of their own Shared Photos and a short message
- [x] A User with User Memory off, or no Shared Photos, never gets it
- [x] Admins see and can edit or turn off the Kind; existing installs get it
- [x] Seam 2 tests cover sending, User Memory off, no Shared Photos and a failed photo send
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/photos/issues/05-send-photo-back.md`

## Comments

### 2026-11-13 — plan (branch `photos-06-look-back-check-in`)

- Check-in Kinds get a fixed flag `sends_shared_photo` (not editable by Admins). The seed file gets a fifth Kind, "A look back at a photo", with the flag on and not allowed without User Memory.
- Migration 0020: adds the flag, and `check_ins.shared_photo_id` (set null if the photo is deleted). On an existing install (Kinds already there) it adds the new Kind last, unless a Kind with that name exists. A fresh install gets it from the seed file.
- The Check-in decision is offered the photo Kind only when User Memory works and the User has Shared Photos. Then it also sees the numbered Shared Photos (date, description, note) and must name one as `"photo": <number>` when it picks that Kind; a missing or wrong number is an answer we can't use (tried again next tick, like other bad answers). The ask for the number sits next to the photo list, in code, so the stored Check-in prompt doesn't need a reset.
- Sending: text first, then the photo by its file id. If Telegram refuses, the text still went, the error is logged, and the Check-in is saved without the photo.
- A reply to that Check-in starts its Conversation with the text and then "[You sent them back their own photo…]", like a reply that sent a photo.
- Admins: the Kind can be edited and removed like others; it can't be allowed without User Memory (422). The admin card shows that it sends a Shared Photo and hides the User Memory switch.

### 2026-11-13 — evidence

- `make check` on the branch rebased on `origin/main` (5c6cd2d): ruff, ruff format, mypy pass; pytest 504 passed; web lint, prettier, typecheck pass; vitest 300 passed. `pnpm build` passes (with `.env` loaded).
- Seam 2 `tests/test_look_back_check_in.py` (16 tests, through `scheduler.tick()`): the named Shared Photo goes after the message by its file id, the decision sees the photos numbered with date, description and note; a reply's Conversation starts with the message and then "[You sent them back their own photo…]"; no Shared Photos → the Kind isn't offered; User Memory off → neither the Kind nor the photos are offered; a missing, out-of-range, string or `true` photo number sends nothing and is tried again next tick; a photo number with another Kind is ignored; Telegram refusing → the message still goes, "Could not send the Check-in's Shared Photo" is logged, nothing is saved as sent; Admins see the Kind with `sends_shared_photo`, can edit (still sends its photo under a new name) and remove it, and get 422 for allowing it without User Memory; the User's Check-ins page lists it only with User Memory on; migration: an existing install gets it last, a fresh install gets all five from the seed. Updated older tests for the fifth Kind. Vitest: the admin card says "Sends a Shared Photo" and has no memory switch.
- `/run` (worktree stack, real DeepSeek and real Telegram; the owner linked to their own chat in the worktree database):
  - Fresh database: five Kinds, the photo Kind last. `make db-copy` from the main stack (at 0019, four Kinds) then the backend start ran 0020: the photo Kind added last, `sends_shared_photo` true.
  - The owner got one Shared Photo with the real weekend-list file id (made 2026-11-13; `getFile` and the download still worked at 20:15, same day). With the seeded description, DeepSeek chose "A follow-up" and wrote about the monstera and Gran from the photo's description, without the photo. With the Kind's description set for the run to "Choose this Kind this time", it chose "A look back at a photo", named the photo, and the real photo went by `sendPhoto` after "Found myself thinking about that weekend list…"; saved with its `shared_photo_id`.
  - A reply posted to the worktree webhook started a Conversation with the Check-in text, then the "[You sent them back their own photo…]" photo message, and got a fitting reply.
  - With the file id broken, the text went, the log showed "Could not send the Check-in's Shared Photo" with Telegram's 400, and the Check-in was saved without a photo.
  - With User Memory off (and the "choose this" description still in place), it sent "A casual hello" with no photo and no mention of the list.
  - Admin Check-in Kinds page (Playwright, signed-in Admin, 1280 px): the photo Kind card shows "Sends a Shared Photo" with no switch; a description edit saved and stayed after reload, then the original was put back; no page errors. Cleaned up: the run's Clerk user deleted, the Kind's description restored; the worktree database is removed at teardown.
- Code review (`/code-review`, Standards and Spec in parallel): no hard rule breaks; nothing missing. Fixed: the photo is sent before the `CheckIn` record is built, not inside it; `number` renamed `photo_number`. Not changed: see Decisions.

### Decisions

- The photo Kind is marked by a fixed `sends_shared_photo` flag, not by its name, so Admins can rename it. Admins can't set the flag; a Kind they add never sends a photo.
- "Turn it off" means Remove, like other Kinds. A removed photo Kind can't be added back from the admin area (a new Kind never gets the flag). Acceptable for now; a restore needs a migration or the seed on an empty table.
- The photo Kind is offered only when User Memory works and the User has at least one Shared Photo. The User's own Check-ins page lists it whenever User Memory is on (the Kinds they could get), even with no Shared Photos yet.
- The ask for `"photo": <number>` sits beside the numbered photo list in the decision's input (in code, using the Kind's current name), so the stored Check-in prompt needs no reset and Admin edits to it are kept.
- All the User's Shared Photos are listed to the decision, with no cap. Fine at today's sizes; cap it if Users keep many.
- With the seeded description, the real model chose a follow-up about the photo rather than the photo Kind in the one natural try. That's the model's choice working as meant ("now and then"); Admins can tune it through the Kind's description.
- Not changed from review: `sends_shared_photo` is checked in a few places in one flow (fine for one Kind); the User Memory check is called more than once per decision, as before this change; the migration repeats the seed's name and description so it stays frozen; `describe_check_in`'s argument list.
- Seen in `/run`, not from this change: the "Could not send…" error logs include the full Telegram bot token in the request URL (from httpx's error message in the existing Telegram adapter). Worth filing as a bug.
- Photo Viewing (issue 07) doesn't exist yet; it must also stop this Kind being offered when off.

## Completion

- Completed: 2026-11-13
- Commit: to be filled in after merge
