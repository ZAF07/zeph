# 03 — Zeph replies to a specific text

Status: ready-for-agent
Track: A
Blocked by: None - can start immediately

## Parent

`.scratch/natural-replies/PRD.md`

## What to build

When a User's Message has more than one thread ("work was rough" / "also mum called" / "oh and the cat's sick"), Zeph can send one of its short texts as a Telegram reply to the User text it answers, when that text isn't the latest. At most two per reply.

- Each saved User text keeps its chat channel message ID (new nullable column on the saved messages).
- The Reply is shown the Message's texts numbered (`[1]`, `[2]`, …). Its prompt says when to point and how: a part may start with `[re 2]`. `response_prompt` is reloaded from the seed by migration.
- Code strips the marker. A marker naming no text of this Message, or past the limit of two, is dropped and the part is sent normally.
- The chat channel port's `send_text` takes an optional ID to reply to. The Telegram adapter sends it as `reply_parameters` with `allow_sending_without_reply` on, so a deleted original never stops the text going out.
- Everything else about sending (typing pause, sticker, Shared Photo, start-over before the first part) is unchanged.

Note: issue 04 (track B) also adds a column to the saved messages and changes how the Reply sees the Message's texts. Whoever merges second renumbers their migration and merges the transcript change.

## Acceptance criteria

- [ ] A `[re N]` part goes out as a reply to the Message's Nth User text.
- [ ] A marker naming a text not in this Message, or a third marker, is dropped and that part is sent normally with no marker text.
- [ ] A single-thread Message's reply has no reply links (prompt guidance; checked in a `/run`).
- [ ] A text whose original can't be found by Telegram is still sent.
- [ ] Migration adds the message ID column without touching existing rows and reloads `response_prompt`.
- [ ] Tests through the webhook (`FakeChatChannel` sent texts), the migration and the Telegram adapter; all Python checks pass.
- [ ] `/run`: in a worktree, send a three-thread burst to the backend webhook and see a reply text attached to an earlier User text in the adapter's request.
- [ ] `docs/message-pipeline/README.md` decision 21 updated to "Built".

## Blocked by

None - can start immediately.

## Comments
