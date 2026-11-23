# 04 — Zeph reads Replied-to Texts

Status: ready-for-agent
Track: B
Blocked by: None - can start immediately

## Parent

`.scratch/natural-replies/PRD.md`

## What to build

When a User swipes to reply to an earlier text, Zeph's or their own, however old, Zeph sees what they're replying to.

- `IncomingMessage` gains a **Replied-to Text**: who sent it (User or Companion), when, its kind (text, photo, sticker, other) and what it said: the highlighted part (`quote`) if any, otherwise the text or caption, cut to ~500 characters. `replied_sticker` keeps working as today.
- The Telegram adapter reads it from `reply_to_message` (the sender's `is_bot` decides User or Companion) and the update's `quote`, for text, sticker and photo messages. It never looks up our saved messages, so it works after Message Retention.
- Each saved User text keeps its Replied-to Text (new nullable JSON column on the saved messages). Delete My Data and Message Retention remove it with the text.
- Transcript lines show it, e.g. `User (replying to Zeph's text from 3 Nov, "have you told your mum about the job yet?"): not yet, scared tbh`, or "their own text" for the User's own. A reply to a Check-in reads as a reply to Zeph's text. The Understanding, Reply Plan, Reply and Recent Messages see it; the Model Call Log shows it wherever it already shows content (ADR-0010).
- **First, check** where transcript lines are built. The PRD assumes one shared place; if the Understanding, Reply Plan and Reply build their own, change each (the Safeguard is issue 05).

Note: issue 03 (track A) also adds a column to the saved messages and changes how the Reply sees the Message's texts. Whoever merges second renumbers their migration and merges the transcript change.

## Acceptance criteria

- [ ] A reply to Zeph's text reaches the Understanding, Reply Plan and Reply with who, when and what it said.
- [ ] A reply to the User's own text reads as their own text.
- [ ] A highlighted part is shown instead of the full text; a long text is cut to ~500 characters.
- [ ] A reply to a photo or sticker says so, with any caption.
- [ ] Several texts in one Message, each replying to a different text, each show their own link.
- [ ] Later replies in the Conversation and the Recent Messages still see the link.
- [ ] Replies to stickers keep working as today.
- [ ] Migration adds the column without touching existing rows; Delete My Data removes it.
- [ ] Tests through the webhook (fake chat model prompts), the Telegram adapter (new helper in `tests/telegram_helpers.py` for a reply update, with and without `quote`) and the migration; all Python checks pass.
- [ ] `/run`: in a worktree, post a reply update to the backend webhook and see the Replied-to Text in the Model Call Log or trace for the Understanding and Reply.
- [ ] `docs/message-pipeline/README.md` decision 20 note says what is built.

## Blocked by

None - can start immediately.

## Comments
