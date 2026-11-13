# 24 — Admins chat in stickers, and add stickers in chat only when they say so

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md` (follows on from `issues/archive/10-stickers.md`). Grilled on 2026-11-13; the User side was split out into `issues/30-personal-stickers.md`.

## Today

Every sticker an Admin sends the Companion is added to the Sticker Library and never answered (`src/companion/core/incoming_messages.py`, the Admin sticker branch in `handle`), so Admins can't chat in stickers.

## What to build

Outside adding mode an Admin is just a User: their stickers are answered as "[sticker: 😂]". Admins add stickers to the Sticker Library in chat in two ways, and still on the Dashboard as today.

### 1. Adding mode, through a chat tool

- The Admin says it in plain words ("I want to add some stickers", "add these sticker sets"). Response composition offers Admins only a tool (e.g. `start_adding_stickers`), as ADR 0006 does for settings. The Safeguard still runs first. The Companion replies with something like "Send them over 👍".
- The tool takes one choice: **single stickers** or **whole sets**.
  - Single: each sticker sent is added.
  - Whole sets: each sticker sent adds every sticker in its set (reuse the set import). A sticker with no set is added on its own.
- While the mode is on, each sticker gets a ✅ reaction and no text reply. It isn't answered and is never kept as a Personal Sticker.
- The mode ends on the Admin's first message that isn't a sticker, or after a quiet gap (new Admin setting, 5 minutes to start). That message is answered as normal, and the Companion confirms what it added, e.g. "Added 33 stickers from 1 set (2 were already there)". It also reminds the Admin to add "when to use" notes on the Dashboard. After the quiet gap, stickers are back to normal chat.

### 2. Reply to a sticker

- An Admin replies "add this" (or "add this set") to a sticker in the chat, and that sticker (or its set) is added. No mode needed. The webhook must start passing along the sticker being replied to.

### Same for both ways

- Stickers already in the library are skipped and keep their notes.
- Stickers added in chat have no note, so they show "Needs a note" on the Sticker Library page and aren't sent until an Admin writes one. The Companion doesn't draft notes for global stickers.
- The Sticker Library page's "Listening for stickers from @…" label is replaced with a short explanation of both chat ways to add.
- Non-Admins never get the tool, and "add this" from them is just chat.

## Design

- `docs/design/zeph-admin.html`: Sticker Library (label change only)

## Acceptance criteria

- [ ] An Admin's sticker outside adding mode is answered like any User's and isn't added to the library
- [ ] An Admin can start adding mode in plain words, for single stickers or whole sets; a non-Admin can't
- [ ] In adding mode each sticker gets a ✅ reaction and is added (or its whole set is); duplicates are skipped and keep their notes
- [ ] Adding mode ends on the first non-sticker message (answered as normal, with a summary of what was added) or after the Admin-set quiet gap
- [ ] Replying "add this" / "add this set" to a sticker adds it / its set, for Admins only
- [ ] Sticker Library page explains the chat ways to add
- [ ] Tests at seam 1 (and seam 3 for the label); `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

None.

## Comments

**2026-11-13 — grilled.** Decisions:
- Adding is started with an LLM tool (ADR 0006 pattern), not a slash command. Replying "add this" to a sticker is kept as a second way, because sometimes it's handier.
- Mode ends on first non-sticker message or a quiet gap; ✅ reaction per sticker, one summary at the end.
- One choice in the tool: single stickers or whole sets.
- Global stickers keep Admin-written notes only. No vision call to draft notes.
- Outside adding mode, an Admin is just a User (their stickers can become their own Personal Stickers, see issue 30).

**2026-11-13 — started on branch `mvp-24-admin-stickers-in-chat`.** Plan:
- New core module `sticker_adding.py`: each Admin's adding mode lives in memory (choice, tally, chat). It holds the `start_adding_stickers` tool (offered to Admins only), the reply-"add this" path, the summary message and the quiet-gap timer (the same Timer albums use).
- `IncomingMessageHandler`: an Admin's sticker is chat unless adding mode is on. In the mode it is added (or its set) and gets a reaction, nothing else. Any other message ends the mode: summary first, then answered as normal. An Admin's "add this" / "add this set" reply to a sticker adds it and gets the summary, without a reply from the model.
- Webhook passes `message_id` for stickers and texts, and the sticker being replied to. Chat channel port gets `react`.
- Settings: `sticker_adding_quiet_gap_minutes` (5, on Platform settings), `sticker_adding_summary_reply`. The old per-sticker `sticker_added_reply` / `sticker_already_in_library_reply` are dropped from the seed.
- Telegram only allows reactions from a fixed emoji list, and ✅ isn't on it, so the reaction is 👍.
