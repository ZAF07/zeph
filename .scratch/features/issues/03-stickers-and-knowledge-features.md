# 03 — Stickers and Knowledge as Features

Status: ready-for-agent

## Parent

`.scratch/features/PRD.md`

## What to build

Stickers and Knowledge join the Feature list, so Admins can switch them for everyone (and per User once issue 02 is in).

- Stickers: the reply is offered the sticker tool only when Stickers works for the User. Incoming stickers are still read through their emoji, and Admins can still add stickers by sending them.
- Knowledge: Knowledge retrieval is skipped when Knowledge doesn't work for the User, so no passages go into the reply.
- Both appear on the admin Features page (and in the per-User panel) with descriptions, and in the "not available on your account" note when off.

## Acceptance criteria

- [ ] With Stickers off, replies get no sticker tool and no sticker is sent; incoming stickers still read as their emoji
- [ ] With Knowledge off, no Knowledge passages go into the reply
- [ ] Both show on the Features page with their switch and last change, and turning them back on restores them
- [ ] Seam 1 tests cover both on and off; seam 3 tests cover the new rows
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/features/issues/01-features-and-web-search-switch.md`
