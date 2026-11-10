# 10 — Stickers

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

The Companion can send and understand stickers. Admins build the Sticker Library by sending stickers to the Companion from their own connected Telegram account, or by entering a sticker set name, and add a "when to use" note to each; they can remove stickers. Response composition may add one optional sticker, picked from the Sticker Library; the Persona says to use them occasionally. Incoming stickers reach the Companion as their emoji (e.g. "[sticker: 😂]"). Voice notes, photos and other unsupported types get an in-character "can't do that yet, can you type it?" reply.

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
