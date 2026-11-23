# 03 — Zeph replies to a specific text

Status: completed
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

- [x] A `[re N]` part goes out as a reply to the Message's Nth User text.
- [x] A marker naming a text not in this Message, or a third marker, is dropped and that part is sent normally with no marker text.
- [x] A single-thread Message's reply has no reply links (prompt guidance; checked in a `/run`).
- [x] A text whose original can't be found by Telegram is still sent.
- [x] Migration adds the message ID column without touching existing rows and reloads `response_prompt`.
- [x] Tests through the webhook (`FakeChatChannel` sent texts), the migration and the Telegram adapter; all Python checks pass.
- [x] `/run`: in a worktree, send a three-thread burst to the backend webhook and see a reply text attached to an earlier User text in the adapter's request.
- [x] `docs/message-pipeline/README.md` decision 21 updated to "Built".

## Blocked by

None - can start immediately.

## Comments

**Done, 23 Nov 2026.** Evidence per criterion:

- `[re N]` goes out as a reply to the Nth text: `test_a_marked_part_goes_out_as_a_reply_to_that_text_of_the_message`; `/run` burst "got the job offer!!" / "sister's wedding… gift, any ideas?" / "how was your day lol": the real Telegram adapter's `sendMessage` for the gift answer carried `"reply_parameters": {"message_id": 502, "allow_sending_without_reply": true}` (502 = the User's 2nd text). The marker never reached the User or the saved messages.
- Bad or third marker dropped, part sent normally: `test_a_marker_naming_no_text_of_the_message_is_dropped` (`[re 7]`, `[re 0]`), `test_a_third_marker_is_dropped_and_its_part_sent_normally`, `test_a_marker_naming_the_latest_text_is_dropped`, `test_a_marker_in_a_reply_to_an_earlier_message_points_at_nothing`.
- Single-thread Message has no links: `test_a_single_text_messages_reply_has_no_reply_links`; `/run` one long text (3 parts) and a one-thread burst of three texts (2 parts): no `reply_parameters` on any request.
- Sent even if the original can't be found: `test_a_text_replying_to_a_message_is_sent_even_if_the_original_is_gone`; the `/run` request above carries `allow_sending_without_reply: true`.
- Migration: `tests/test_chat_message_ids_migration.py` (down to 0076 and back with saved messages, all NULL; stored `response_prompt` removed so it reloads). 0077 applied on the worktree stack's start; the live `response_prompt` contains `[re N]`; `/run` saved User texts with IDs 501–503, Zeph's with none.
- Tests and checks: `ruff check`, `ruff format --check`, `mypy src` clean; `pytest` 1647 passed.
- `/run` in the worktree: real app built by `build_production_app` in the backend container, real Postgres and DeepSeek. The only change was that the real `TelegramChatChannel` got a recording HTTP transport, so the Bot API requests were seen and nothing went to Telegram.
- Decision 21 in `docs/message-pipeline/README.md` is marked built, with a note.

Decisions and caveats:

- A Message of one text is shown to the Reply unnumbered; with more than one text, each is `[n] …` (after any Replied-to Text note from issue 04).
- Code also drops a marker that names the latest text. The spec says "when that text isn't the latest", so a stray `[re 1]` on a one-text Message can't make a link.
- A part that is only a marker is left out. Markers allow case and inner spaces (`[RE 2]`, `[ re 2 ]`), but only at the start of a part.
- Migration 0077 reloads `response_prompt` from the seed, as the issue asks (like 0067/0073), so an Admin's edit to it is replaced.
- A real deleted original wasn't tried against Telegram (a worktree can't reach it). This relies on Telegram's `allow_sending_without_reply`, and the request was checked.
- In the first `/run` burst (work / mum / cat) the model answered all three together, with no link. That fits the prompt: it links only when a text answers one earlier thread.

## Completion

- Completed: 2026-11-23
- Commit: <filled in after merge>
