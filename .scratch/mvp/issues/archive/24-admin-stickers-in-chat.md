# 24 — Admins chat in stickers, and add stickers in chat only when they say so

Status: completed

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

- [x] An Admin's sticker outside adding mode is answered like any User's and isn't added to the library
- [x] An Admin can start adding mode in plain words, for single stickers or whole sets; a non-Admin can't
- [x] In adding mode each sticker gets a 👍 reaction (Telegram refuses ✅) and is added (or its whole set is); duplicates are skipped and keep their notes
- [x] Adding mode ends on the first non-sticker message (answered as normal, with a summary of what was added) or after the Admin-set quiet gap
- [x] Replying "add this" / "add this set" to a sticker adds it / its set, for Admins only
- [x] Sticker Library page explains the chat ways to add
- [x] Tests at seam 1 (and seam 3 for the label); `make check` passes
- [x] Verified in the running app via `/run`

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

**2026-11-13 — implemented, reviewed and verified.** Commits `87c0601`, review fixes `19fcda6` on `mvp-24-admin-stickers-in-chat` (rebased onto main after issue 30 merged; conflicts were both-sides additions in `app.py`, `platform_settings.py`, `response_composition.py` and the Platform settings form).

Done and verified: every acceptance criterion. `make check` green after the rebase (see Completion). Real app in the worktree's Docker stack, real DeepSeek and Telegram. A test Admin was linked to the owner's Telegram in the worktree database only, and updates were posted to the worktree's webhook, so confirmations and reactions went to the owner's real chat:
- Telegram check: `setMessageReaction` with ✅ gave `400 REACTION_INVALID`; 👍 worked.
- Admin sticker outside adding mode: answered ("Ha, something got you…"), saved as "[sticker: 😂]", library still empty.
- "I want to add some sticker sets to the library": DeepSeek called the tool. A HotCherry sticker added all 34, a second HotCherry sticker added nothing new, an Animals sticker added all 50. No replies, no errors (a refused reaction would have logged one).
- With one HotCherry note written, a second round in whole-sets mode added UtyaDuck (40) and the summary "Added 40 stickers from 2 sets (34 were already there)…" was saved before the Admin's "perfect, done!", and the reply knew it ("Good, that's all sorted then."). The note was kept.
- Quiet gap set to 1 minute: after one sticker in single mode, the summary "Added 1 sticker…" arrived on its own and the next sticker was chat again.
- Reply "Add this! 👍" added 1 sticker; "add this set" added the whole 50-sticker Animals set; both with the summary and no model reply. With the role set to `user` (then restored), "add this" and asking to add stickers added nothing.
- Dashboard as the test Admin: Sticker Library "Send from your Telegram" tab shows the two-way explanation, no "Listening…" label, chat-added stickers show "Needs a note"; no sideways scroll at 390px. Platform settings shows "Sticker adding quiet gap" under Stickers.
- After the review fixes: "add this" then whole-sets mode added 1 and then 39 more ("1 was already there"), no errors.
- After the rebase onto main (with issue 30 and migration 0022): an Admin sticker outside the mode was answered ("👍"); single mode added 2 stickers with no replies; the summary was saved before "that's it" and the reply knew it; "add this set" added the other 38 ("2 were already there"); no errors.

Decisions:
- The reaction is 👍: Telegram only allows reactions from a fixed emoji list, and ✅ isn't on it.
- Adding mode lives in memory (a restart ends it). A sticker in the mode is never saved to the Conversation, so it is never answered or kept as a Personal Sticker.
- The summary ("Added 33 stickers from 1 set (2 were already there).") is sent and saved in the Admin's Conversation, so the next reply knows what was added. It is also sent when the quiet gap ends the mode, and after "add this". The note reminder (`sticker_adding_summary_reply`, with `{added}` and `{dashboard_url}`) is left out when nothing new was added. Nothing is sent if no sticker came in the mode.
- In whole-sets mode a set already added in this mode isn't looked up again; a sticker whose set can't be found is added on its own.
- "add this" is an exact phrase match (any case, punctuation or emoji): "add this", "add it", "add this sticker" for one; "add this set", "add the set", "add this whole set", "add the whole set" for the set. Other replies to a sticker are just chat.
- The tool is offered to Admins whether or not Stickers works for them. Its description says adding is always off while a reply is written, and to call it every time.
- New Admin setting `sticker_adding_quiet_gap_minutes` (5, 1–60) under Stickers on Platform settings. `sticker_added_reply` and `sticker_already_in_library_reply` are gone from the seed; rows already in a database stay, unused.
- New chat channel port method `react`; the webhook now passes `message_id` for texts and stickers and the sticker a text replies to. `ConversationService.deliver_notice` sends and saves a message the Companion wasn't asked to write.

Caveats:
- DeepSeek sometimes says adding is on without calling the tool, so the stickers are just chat. In a long Conversation full of earlier adding talk this happened often; after the description said adding is always off and to call it every time, 3 of 3 clear asks in fresh Conversations started the mode. After asking "single or whole sets?" it once took a sticker as the answer without calling the tool. Worth an eval (issue 15).
- When the quiet gap ends the mode, the summary arrives on its own, and a later reply sometimes still sounds as if adding were on.
- The confirmations and reactions went to the owner's real Telegram; they were checked through the database and backend logs, not by reading the chat.

`/code-review`: Standards had no hard violations; Spec found nothing missing. Fixed: a refused reaction is now logged, not raised (test added); the sticker is added and reacted to inside the lock, so the summary can't come before a reaction; the "add this" check (with its Admin check) moved into `StickerAdding`, so the handler no longer has its own Admin check; a `StickerTally` type split from `AddingMode`. Left as is: the summary after the quiet gap and after "add this" (otherwise the Admin never learns what was added); one lock held during Telegram calls (only Admins in adding mode wait on it); the timer's summary and a new message can't both take the mode.

Evidence: seam 1 `tests/test_sticker_adding.py` (16), `tests/test_features.py::test_with_stickers_off_admins_still_add_stickers_in_chat`; adapter `tests/adapters/test_telegram_chat_channel.py::test_a_reaction_is_put_on_a_message_by_its_id`; seam 3 `web/src/components/StickerLibrary.test.tsx`, `web/src/components/PlatformSettingsForm.test.tsx`.

## Completion

- Completed: 2026-11-13
- Checks: `make check` after the rebase: ruff, ruff format, mypy clean; pytest 571 passed; eslint, prettier, tsc clean; vitest 315 passed.
- Commit: 87c0601 "Admins chat in stickers and add them in chat through a tool or by replying "add this"", review fixes 19fcda6 "Review fixes for issue 24: log a refused sticker reaction, react inside the adding lock, move the "add this" check into StickerAdding", archive <archive commit> on branch `mvp-24-admin-stickers-in-chat` (merged into main in <merge commit>)
