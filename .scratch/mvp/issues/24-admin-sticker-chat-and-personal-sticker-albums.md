# 24 — Admins chat in stickers, and each User gets a personal sticker album

Status: needs-triage

## Parent

`.scratch/mvp/PRD.md` (follows on from `issues/archive/10-stickers.md`)

## Before deciding on a solution

Run `/grill-with-docs` on this issue first. The owner wants to grill the idea with the docs before a solution is picked, so don't plan or build anything here until that is done.

## Today

- Every sticker an Admin sends the Companion is added to the Sticker Library and never answered, so Admins can't chat in stickers.
- Stickers a User sends are read through their emoji and answered, but never kept.
- The Companion only sends stickers from the one shared Sticker Library.

## What the owner wants

### Admins

- Admins can chat in stickers like anyone else. A sticker they send is answered, not added to the library.
- To add stickers, an Admin says so in the chat ("add this sticker", "add this sticker set"), then sends the sticker or stickers.
- Admins can still add stickers from the admin Dashboard.
- Stickers added these ways are global: the Companion can send them to any User.

### Users

- Each User gets their own personal sticker album.
- The Companion saves stickers a User sends into that User's album.
- The Companion can reply with stickers from the User's own album, so its sticker replies feel personal to them.
- A core service decides which stickers a User sends are worth saving to their album and which to ignore.

## Open questions for the grilling

- How does the Companion tell "add this sticker" apart from a normal sticker in chat? How long does "adding mode" last, and how does it end?
- Does a User's album sticker need a "when to use" note like global stickers? Who or what writes it?
- What makes a sticker worth saving? Seen often, sent with feeling, fits the Persona?
- When replying, how does the Companion choose between a global sticker and one from the User's album?
- Can Users see or remove their album? Can Admins see it on the per-User panel?
- Does Delete My Data clear the album? Account Deletion should.
- Should this be a Feature that can be switched on or off, for everyone or per User?
- New glossary terms (for example "Personal Sticker Album"), and does "Sticker Library" change meaning?

## Comments
