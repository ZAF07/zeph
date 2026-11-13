# 03 — Albums get one reply

Status: in-progress

## Parent

`.scratch/photos/PRD.md`

## What to build

Several photos sent at once (a Telegram album) get one reply, like a friend would give.

- Photos with the same album id are collected for an Admin-set wait after the last one arrives (default 2 seconds), then handled as one message: the caption (from whichever photo has it) and each photo's description.
- At most an Admin-set number of photos are looked at (default 5); the Companion is told how many more there were and mentions it.
- The album counts as one message toward the Daily Message Limit, and the Safeguard reads all its descriptions together.

## Acceptance criteria

- [ ] An album of three photos gets one reply that covers them, with the caption
- [ ] An album over the cap describes only the first photos and the reply mentions the rest weren't looked at
- [ ] An album counts as one message
- [ ] Wait and cap are editable on the admin Settings page
- [ ] Seam 1 tests cover the album, cap and message count
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/photos/issues/01-companion-sees-a-photo.md`

## Comments

### 2026-11-13 — note from issue 02

- `PhotoTools.offer` (`core/photos.py`) lists each viewed photo with its whole message text. In an album every photo would get the same line, so give each photo its own description in the tool list (and `PhotoService.read_message` takes one photo today).

### 2026-11-13 — plan (branch `photos-03-albums`)

- The webhook reads Telegram's `media_group_id` as the photo's `album_id` on `IncomingMessage`.
- New `Timer` port: `start(key, seconds, work)` runs work after a wait, and starting the same key again restarts the wait. Real adapter uses `threading.Timer`; the fake lets tests fire it by hand.
- `IncomingMessageHandler` collects album photos by sender and album id; each photo restarts the wait (`photo_album_wait_seconds`, default 2). When it ends, the album is answered as one turn under the User's turn lock, so it counts once and the Safeguard reads it all.
- `PhotoService.read_message(user, photos, caption)` looks at up to `photo_album_max_photos` (default 5), writes "[photo 1: …] [photo 2: …] caption" (one photo stays "[photo: …] caption") and adds a note saying how many more weren't looked at.
- `ChannelPhoto` gains `description` (kept in the existing `photos` JSON, no migration); `ask_about_photo` lists each photo by its own description, falling back to the message text for photos saved before this.
- Both settings are whole numbers on the admin Settings page, Photos section.
