# 04 — Zeph reads Replied-to Texts

Status: completed
Track: B
Blocked by: None - can start immediately

## Parent

`.scratch/natural-replies/archive/PRD.md`

## What to build

When a User swipes to reply to an earlier text, Zeph's or their own, however old, Zeph sees what they're replying to.

- `IncomingMessage` gains a **Replied-to Text**: who sent it (User or Companion), when, its kind (text, photo, sticker, other) and what it said: the highlighted part (`quote`) if any, otherwise the text or caption, cut to ~500 characters. `replied_sticker` keeps working as today.
- The Telegram adapter reads it from `reply_to_message` (the sender's `is_bot` decides User or Companion) and the update's `quote`, for text, sticker and photo messages. It never looks up our saved messages, so it works after Message Retention.
- Each saved User text keeps its Replied-to Text (new nullable JSON column on the saved messages). Delete My Data and Message Retention remove it with the text.
- Transcript lines show it, e.g. `User (replying to Zeph's text from 3 Nov, "have you told your mum about the job yet?"): not yet, scared tbh`, or "their own text" for the User's own. A reply to a Check-in reads as a reply to Zeph's text. The Understanding, Reply Plan, Reply and Recent Messages see it; the Model Call Log shows it wherever it already shows content (ADR-0010).
- **First, check** where transcript lines are built. The PRD assumes one shared place; if the Understanding, Reply Plan and Reply build their own, change each (the Safeguard is issue 05).

Note: issue 03 (track A) also adds a column to the saved messages and changes how the Reply sees the Message's texts. Whoever merges second renumbers their migration and merges the transcript change.

## Acceptance criteria

- [x] A reply to Zeph's text reaches the Understanding, Reply Plan and Reply with who, when and what it said.
- [x] A reply to the User's own text reads as their own text.
- [x] A highlighted part is shown instead of the full text; a long text is cut to ~500 characters.
- [x] A reply to a photo or sticker says so, with any caption.
- [x] Several texts in one Message, each replying to a different text, each show their own link.
- [x] Later replies in the Conversation and the Recent Messages still see the link.
- [x] Replies to stickers keep working as today.
- [x] Migration adds the column without touching existing rows; Delete My Data removes it.
- [x] Tests through the webhook (fake chat model prompts), the Telegram adapter (new helper in `tests/telegram_helpers.py` for a reply update, with and without `quote`) and the migration; all Python checks pass.
- [x] `/run`: in a worktree, post a reply update to the backend webhook and see the Replied-to Text in the Model Call Log or trace for the Understanding and Reply.
- [x] `docs/message-pipeline/README.md` decision 20 note says what is built.

## Blocked by

None - can start immediately.

## Comments

**Done, 23 Nov 2026.** Evidence per criterion:

- Reply to Zeph's text reaches Understanding, Reply Plan, Reply: `test_a_reply_to_zephs_text_reaches_the_understanding_reply_plan_and_reply`; `/run` Model Call Log shows `(replying to the Companion's text from 3 Nov 2025, "have you told your mum about the job yet?") not yet, scared tbh` in all three (and "your text" in the Reply). Real DeepSeek reply followed on from it.
- Own text: `test_a_reply_to_the_users_own_text_reads_as_their_own_text`; `/run` shows "their own text".
- Highlighted part / cut: adapter tests; `/run` shows only "also mum called" from a longer text, and a 900-character text cut to 500 + "…".
- Photo / sticker: `test_a_reply_to_a_photo_or_sticker_says_so_with_any_caption`; `/run` shows `their own photo … "my cat"` and `the Companion's sticker … "🤗"`.
- Several texts, own links: `test_each_text_of_a_message_shows_the_text_it_replies_to`; `/run` Message of three texts each with its own note.
- Later replies and Recent Messages: `test_later_replies_in_the_conversation_still_see_the_link`, `test_a_new_conversation_still_sees_the_link_in_the_recent_messages`; `/run` second Message's Understanding shows the first Message's link under "Earlier messages, across Conversations", and the Reply's history too.
- Stickers as today: `tests/test_sticker_adding.py` (16 pass); `/run` as an Admin, "add this" replying to a sticker added it to the library (the rerun answered "1 was already there").
- Migration and Delete My Data: `test_the_migration_adds_the_column_and_keeps_existing_messages_as_they_were` (real Postgres, down to 0073 and back up with saved messages); 0074 applied on the worktree stack's start; `/run` Delete My Data took rows with a Replied-to Text from 4 to 0 (204).
- Tests and checks: `ruff check`, `ruff format --check`, `mypy` clean; `pytest` 1570 passed.
- `/run` in the worktree: real backend app and Postgres, real chat model, chat channel swapped for a recording one so nothing went to Telegram (webhook registration off, no ngrok).
- Decision 20 note in `docs/message-pipeline/README.md` says what is built.

Decisions and caveats:

- Line format is `Person: (replying to the Companion's text from 3 Nov 2025, "…") not yet`, the same note in every transcript; the Reply's own history says "your text". A reply to a Check-in is a reply to the Companion's text (sender is the bot).
- The Safeguard already sees the note through the shared `to_chat_history`; its tests and the crisis case stay with issue 05.
- Conversation-end steps (Life Threads, Patterns, Curiosities, Move Outcomes, Personal Stickers, Day Summary) also see the note, with the day in UTC since they don't pass a time zone. Small follow-up if it matters.
- In the `/run`, Zeph made up a detail ("the ear tuft") about the User's old photo it had only the caption of. A reply to an old photo gives no image, so the Reply may invent details; worth a prompt line later.

## Completion

- Completed: 2026-11-23
- Commit: 05d0766 (merge of 8783ec2 "Natural replies 04: Zeph reads Replied-to Texts", f99ce41 "Natural replies 04: review fixes", bc5c82e "updated tasks status")
