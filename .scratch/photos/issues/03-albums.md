# 03 — Albums get one reply

Status: ready-for-agent

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
