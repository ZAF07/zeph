# 10 — Stickers

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

The Companion can send and understand stickers. Admins build the Sticker Library by sending stickers to the Companion from their own connected Telegram account, or by entering a sticker set name, and add a "when to use" note to each; they can remove stickers. Response composition may add one optional sticker, picked from the Sticker Library; the Persona says to use them occasionally. Incoming stickers reach the Companion as their emoji (e.g. "[sticker: 😂]"). Voice notes, photos and other unsupported types get an in-character "can't do that yet, can you type it?" reply.

## Design

- `docs/design/zeph-admin.html`: Sticker Library

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [ ] An Admin sending a sticker to the Companion from their connected Telegram account adds it to the Sticker Library; a non-Admin doing the same does not
- [ ] Admins can add stickers by sticker set name, edit the "when to use" note and remove stickers
- [ ] Replies can include one sticker from the Sticker Library; the Crisis Reply never does
- [ ] Incoming stickers are understood through their emoji
- [ ] Voice notes and photos get the in-character unsupported reply (wording from settings)
- [ ] Seam 1 tests cover: sticker sent from library, incoming sticker → emoji in prompt, unsupported type reply, Admin vs non-Admin sticker capture
- [ ] Seam 3 tests cover the admin Sticker Library page
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

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
