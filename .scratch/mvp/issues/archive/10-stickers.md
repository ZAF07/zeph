# 10 — Stickers

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

The Companion can send and understand stickers. Admins build the Sticker Library by sending stickers to the Companion from their own connected Telegram account, or by entering a sticker set name, and add a "when to use" note to each; they can remove stickers. Response composition may add one optional sticker, picked from the Sticker Library; the Persona says to use them occasionally. Incoming stickers reach the Companion as their emoji (e.g. "[sticker: 😂]"). Voice notes, photos and other unsupported types get an in-character "can't do that yet, can you type it?" reply.

## Design

- `docs/design/zeph-admin.html`: Sticker Library

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [x] An Admin sending a sticker to the Companion from their connected Telegram account adds it to the Sticker Library; a non-Admin doing the same does not
- [x] Admins can add stickers by sticker set name, edit the "when to use" note and remove stickers
- [x] Replies can include one sticker from the Sticker Library; the Crisis Reply never does
- [x] Incoming stickers are understood through their emoji
- [x] Voice notes and photos get the in-character unsupported reply (wording from settings)
- [x] Seam 1 tests cover: sticker sent from library, incoming sticker → emoji in prompt, unsupported type reply, Admin vs non-Admin sticker capture
- [x] Seam 3 tests cover the admin Sticker Library page
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/04-admin-area-foundation.md`

## Comments

**2026-11-12 — started on branch `feat/10-stickers`.** Plan:
- `IncomingMessage` gets a kind (text, sticker, unsupported). The Telegram webhook reads stickers (emoji, file IDs, set name); photos, voice notes and other types are unsupported, with any caption kept.
- A sticker from an Admin's connected Telegram account goes into the Sticker Library (once per sticker) and the Admin gets a short confirmation; it is not answered as a chat message. A User's sticker reaches the Companion as "[sticker: 😂]". An unsupported message gets `unsupported_message_reply`; if it has a caption, the caption is answered as "[photo] caption" so the Safeguard still checks it.
- New `stickers` table; admin API to list, import a set by name, edit the "when to use" note, remove, and show a sticker's image.
- Response composition offers a `send_sticker` tool listing only stickers that have a note; at most one per reply, sent after the text and saved as "[sticker: 🌱]". The Crisis Reply path never composes, so it never has a sticker.
- Chat channel port: `send_sticker`, `get_sticker_set`, `get_sticker_image` (Telegram adapter).
- Dashboard: Sticker Library page from the design and a sidebar link.

**2026-11-12 — implemented, reviewed and verified.** Commits `a3f505b`, `badee03` on `feat/10-stickers`.

Done and verified: every acceptance criterion. `make check` green (Python 231, web 187; ruff, ruff format, mypy, eslint, prettier, tsc clean). Migration 0010 ran on the existing database. Docker run with real Telegram and DeepSeek, updates posted to the webhook as the owner's connected Telegram account:
- Admin sent a real HotCherry 😂 sticker: added to the library once (set name, image), with the "added" reply; sent again: not added twice.
- With a note on it, DeepSeek sent the 😂 sticker after its text for "I GOT THE JOB!!!", saved as "[sticker: 😂]", and didn't send one on the next reply. Earlier light messages got no sticker, as the tool says to use them rarely.
- Owner's role set to `user` for the test (then restored): a 😘 sticker reached DeepSeek as "[sticker: 😘]" and was not added; a voice note and a photo got the unsupported reply and saved nothing; a captioned photo was answered as "[photo] my new monstera plant, finally repotted".
- Admin API as a temporary Clerk test Admin (approved by the owner, deleted afterwards): plain User 403; import "Animals" added 50, again 0; unknown set 404 with its name; blank 422; note saved trimmed; real WebP images for a still sticker and an animated set's thumbnail; remove 204 then 404.
- Dashboard `/admin/stickers` in Chrome, signed in as that Admin: real sticker images in a square grid, "Needs a note" pills, a note saved on leaving the field ("Saved", pill gone), Remove (50 → 49), unknown set error, HotCherry import "Added 33 stickers…" (82), Telegram tab shows the Connect Telegram link for an account without Telegram, no sideways scroll at 390px.
- Test stickers and the test user were removed afterwards.

Decisions:
- Every sticker an Admin sends from their connected Telegram goes into the Sticker Library and gets a confirmation; it is never answered as a chat message, so Admins can't chat in stickers. A non-Admin's sticker is answered as "[sticker: 😂]" ("[sticker]" without an emoji).
- The sticker is a `send_sticker` tool in response composition. Only stickers with a "when to use" note are listed (by number, with emoji and note). At most one per reply, sent after the text, saved as an outgoing sticker message. A reply can be just a sticker. The Crisis Reply path never composes, so it never has one.
- Voice notes, photos, video, files, GIFs, audio, location, contacts, polls, dice and stories are unsupported: `unsupported_message_reply`, nothing saved. With a caption, the caption is answered as "[photo] caption", so the Safeguard still checks it. Telegram service messages (pinned message etc.) are ignored.
- Set import adds every sticker without a note and skips ones already there (by Telegram's unique ID), keeping their notes. Remove deletes the row (no `active` flag). Notes are trimmed, at most 500 characters.
- Images: a still sticker is its own image; an animated or video sticker uses its thumbnail; the backend downloads it from Telegram for the Dashboard. If that fails, the card shows the emoji.
- Seeded settings: `unsupported_message_reply`, `sticker_added_reply`, `sticker_already_in_library_reply`, `sticker_tool_description`, plus a Persona line about occasional stickers. None are on a Dashboard page yet.
- Chat channel port: `send_sticker`, `get_sticker_set`, `get_sticker_image`.

Caveats / follow-ups:
- The new Persona line only reaches new installs: seeding never overwrites an existing `persona`, so this install's Persona doesn't mention stickers. The sticker tool description still says to use them rarely. The owner can add the line on the Persona page.
- "Listening for stickers from @…" is a label: the page doesn't refresh itself; the Admin refreshes to see a sticker they just sent.
- The confirmation and unsupported replies went to the owner's real Telegram; their delivery was checked only through the backend log (no errors), not by reading the chat.
- Tool-result messages for the model ("already picked", "no such number", "will be sent") are in code, like web search's.
- For "[photo] my new monstera…", DeepSeek answered as if fine without saying it can't see the photo. Worth an eval (issue 15).

Evidence: seam 1 `tests/test_stickers.py` (19); adapter `tests/adapters/test_telegram_chat_channel.py` (5 new); contract `test_telegram_says_an_unknown_sticker_set_does_not_exist`; seam 3 `web/src/components/StickerLibrary.test.tsx` (12), `SidebarNav.test.tsx`.

## Completion

- Completed: 2026-11-12
- Commit: a3f505b, review fixes badee03, archive 319354f (merged from `feat/10-stickers` in 18c5c3f)
