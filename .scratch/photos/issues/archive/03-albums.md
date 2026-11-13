# 03 — Albums get one reply

Status: completed

## Parent

`.scratch/photos/PRD.md`

## What to build

Several photos sent at once (a Telegram album) get one reply, like a friend would give.

- Photos with the same album id are collected for an Admin-set wait after the last one arrives (default 2 seconds), then handled as one message: the caption (from whichever photo has it) and each photo's description.
- At most an Admin-set number of photos are looked at (default 5); the Companion is told how many more there were and mentions it.
- The album counts as one message toward the Daily Message Limit, and the Safeguard reads all its descriptions together.

## Acceptance criteria

- [x] An album of three photos gets one reply that covers them, with the caption
- [x] An album over the cap describes only the first photos and the reply mentions the rest weren't looked at
- [x] An album counts as one message
- [x] Wait and cap are editable on the admin Settings page
- [x] Seam 1 tests cover the album, cap and message count
- [x] `make check` passes
- [x] Verified in the running app via `/run`

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

### 2026-11-13 — evidence

- `make check` (after the run fix): ruff, ruff format, mypy pass; pytest 436 passed; web lint, prettier, typecheck pass; vitest 292 passed.
- Seam 1 `tests/test_photos.py` (14 new): an album of three gets one reply reading "[photo 1: …] [photo 2: …] [photo 3: …] our trip", and the Safeguard reads the same text; nothing is answered until the wait ends, and each photo restarts the wait with `photo_album_wait_seconds`; over the cap only the first photos are looked at and the note says how many more there were (singular for one); an album counts as one message with every photo's tokens in Usage; a failed photo in an album is marked while the others are described; two albums at once get a reply each; a video in an album joins the one reply as "[video]" and keeps its caption; an album of only videos gets one unsupported reply (or one reply to its caption); photos are numbered in Telegram's order by message id; `ask_about_photo` lists each album photo by its own description, and photos saved before this fall back to the message text. `tests/test_admin_settings.py`: seeded values 2 and 5, out-of-range values refused. `tests/adapters/test_thread_timer.py` (4 new): runs once after the wait, a restart runs only the last, separate keys, a failure is logged. Vitest: the Photos section shows and saves both fields.
- `/run` (`make restart`, real Telegram download + DeepSeek, real thread timer): both settings were added on start. Three real Telegram photos (house drawing, weekend list, card mock-up) posted to the webhook at the same time and out of order as one album: one saved message with 3 photos numbered in sending order and the caption at the end; Daily usage `message_count` 18 → 19. The first reply only talked about the list (it had a Memory about it); a second album in a fresh Conversation got one reply covering all three photos. Admin Settings page (Playwright, signed-in Admin): both fields in the Photos section, edited to wait 3 / most 2, saved, kept after reload, no page errors. With the cap at 2 an album of 3 saved 2 photos with the note, `message_count` 21 → 22. The first note's wording made the reply ask for the "third photo" to be sent again; reworded to say it came through fine and wasn't looked at because only the first 2 are, then the reply said "I only see the first two of these". Settings restored to 2 / 5 through the page; the test Conversations and the run's Clerk user removed. The three test images sent to the owner's chat to get real file ids are still in that Telegram chat.
- Not run: `make eval` (no Eval in this issue's criteria; the reply prompt and Persona didn't change).

### Decisions

- Album items are collected in memory in the backend process and answered by a `Timer` port (`threading.Timer` adapter). Fine with the one backend process we run; several processes would need a shared store.
- A photo that arrives after its album's wait has ended starts a new album and gets its own reply. With the 2 second default this should be rare; raise the wait if it happens.
- Photos past the cap aren't described, so the Safeguard doesn't see them either. The issue asks for the cap; the PRD's "every photo is described for the Safeguard" was written for single photos. Revisit if Safeguard Evals show a gap.
- The Daily Message Limit is checked after the photos are described (as for single photos before), so a User over the limit can still cost up to `photo_album_max_photos` looks per album.
- A video or other file in an album joins the album's one reply as a marker ("[video]"); an album of only such files gets one unsupported reply.
- The note for photos past the cap is fixed wording in `core/photos.py`, not an Admin setting; the issue only asked for the wait and the cap to be editable.
- `ChannelPhoto.description` is kept in the existing `photos` JSON (no migration), ready for Shared Photos in issue 04.
- The thread timer's "restarted just as it ended" case is fixed by checking the timer is still the newest for its key; there is no test for that timing.


## Completion

- Completed: 2026-11-13
- Commit: 564b9cb "Photos issue 03: albums get one reply. The webhook reads Telegram's media_group_id as the photo's album id…", review fixes c8cc6d1 "Photos issue 03 review fixes: a video or other file sent in an album joins the album's one reply as "[video]" and keeps its caption…", run fix 356e3b6 "Photos issue 03 run fix: the note for album photos past the cap says they came through fine…", archive 495c203 "Photos issue 03 done: archive issue with test, run and review evidence…" (merged from `photos-03-albums` in 305c2eb "Merge Photos issue 03: albums get one reply…")
