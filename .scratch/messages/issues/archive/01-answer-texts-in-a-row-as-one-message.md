# 01 — Answer texts sent in a row as one Message

Status: completed

## Parent

Split out of the Understanding grilling (`.scratch/understanding/issues/archive/01-understanding-before-reply.md`, 14 Nov 2026). Blocks `.scratch/understanding/issues/04-understanding-call-with-seeded-needs.md`.

## What to build

People often send 2–3 short texts in a row. Today each text gets its own reply, one after another; only Albums are grouped. Make the **Message** (see `CONTEXT.md`) the unit the Companion answers: it waits a few seconds (Admin setting) after the last text, then answers everything sent before the pause with one reply, which may still go out as several short texts. Reuse the Album wait idea, and fold Albums into the same rule.

- The Safeguard still checks each text as it arrives, without waiting: a crisis gets the Crisis Reply straight away and the rest of the group isn't answered normally.
- A Message counts as one toward the Daily Message Limit, like an Album.
- A text that arrives while a reply is being written starts a new Message (answered after the current one), as the per-User order works today.
- The wait uses the existing Timer port; making it work across several backend processes stays in `.scratch/scaling/issues/01-run-more-than-one-backend.md`.

## Acceptance criteria

- [x] Three texts sent within the wait get one reply, and the reply call sees all three as the latest Message
- [x] A text after the wait starts a new Message
- [x] The wait is an Admin setting on the Settings page, seeded with a sensible default
- [x] A crisis text inside a group gets the Crisis Reply at once, not after the wait
- [x] A grouped Message counts once toward the Daily Message Limit
- [x] Albums still work as today (one reply, one count, first few photos looked at)
- [x] Tests at the webhook seam with the fake timer; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [x] `/run`: three texts posted to the worktree webhook in quick succession get one reply

## Blocked by

None - can start immediately.

## Comments

### Plan (14 Nov 2026, branch `messages-01-group-texts`)

- Split the ReplyGate in two: `screen` runs per text as it arrives (save it, Safeguard, Crisis Reply), `check` runs once per Message (Delete My Data, Daily Message Limit).
- `IncomingMessageHandler` keeps one pending Message per User. Each text (or single photo, sticker, captioned file) is screened at once under the User's turn lock, then the per-User wait restarts. Album items join the pending Message unscreened and are described and screened together when the wait ends, as today.
- When the wait ends: pop the pending Message under the turn lock, screen any Albums, then run the reply (Delete My Data, limit, compose, deliver) once. A crisis drops the pending Message.
- The reply call and the memory/Knowledge lookups read the trailing run of the User's texts as one latest Message (consecutive incoming messages are merged into one line).
- One setting `message_wait_seconds` ("Message wait", Conversations section, default 4) replaces `photo_album_wait_seconds`; migration 0025 removes the old row.
- Tests: `send_to_webhook` posts and then ends the wait (a User who pauses); a new `post_to_webhook` posts without ending it, for grouping tests.

### Evidence (14 Nov 2026)

- Three texts in the wait get one reply that sees all three as the latest Message: `tests/test_messages.py::test_texts_sent_in_a_row_get_one_reply_that_sees_them_as_one_message` (reply call's last line is `hey\nrough day\nmy boss yelled at me`).
- A text after the wait starts a new Message: `test_a_text_after_the_wait_starts_a_new_message`; a text sent while a reply is written is answered after it: `test_a_text_sent_while_a_reply_is_written_starts_a_new_message_answered_after`.
- Admin setting: `message_wait_seconds` ("Message wait", Conversations section, seeded 4, 1–30); `test_the_wait_is_the_admins_message_wait_setting`, `tests/test_admin_settings.py::test_the_message_wait_is_editable_with_a_seeded_value_of_a_few_seconds`, `web/src/components/PlatformSettingsForm.test.tsx` ("shows and saves the message wait in its Conversations section"). Migration 0025 removes the old `photo_album_wait_seconds` row.
- Crisis inside a group gets the Crisis Reply at once and the rest isn't answered: `test_a_crisis_text_gets_the_crisis_reply_at_once_and_the_rest_is_not_answered`; each text is checked on arrival: `test_the_safeguard_checks_each_text_as_it_arrives_without_waiting`.
- Counts once: `test_a_message_of_several_texts_counts_once_toward_the_daily_limit`.
- Albums as today: every test in `tests/test_photos.py` passes (one reply, one count, photo cap); two Albums together are now one Message (`test_two_albums_sent_together_are_one_message_with_one_reply`); text + Album together: `test_a_text_and_an_album_sent_together_get_one_reply`.
- Checks: `pytest` 749 passed; `ruff check`, `ruff format --check`, `mypy` clean; web `pnpm lint`, `format:check`, `typecheck`, `test` (323) pass.
- `/run` (worktree stack, rebuilt after review fixes): the real app built as in `build_production_app` inside the backend container, with only the Telegram channel swapped for a recording one (fake chat IDs can't receive Telegram sends). Three texts posted to `/telegram/webhook` at +1.1s, +2.1s, +2.9s → nothing sent during the wait, then one reply (two short texts) answering all three; three incoming rows saved; `daily_usage.message_count = 1`.
- `/code-review`: fixed a failed check leaving the rest of the Message to be answered, and a slow Safeguard check letting the wait split a Message (both with tests).

### Caveats

- A text that arrives while a reply is being written (crisis included) is checked after that reply is sent, as before this change.
- Delete My Data is settled against the whole Message: the confirmation word plus another text in the same wait cancels the request instead of confirming it.
- Albums are saved when the wait ends, so "Album, then text" is saved as "text, then Album". A crisis drops held Album photos without saving them.
- The Safeguard now reads the User's texts in a row as one latest line.

## Completion

- Completed: 2026-11-14
- Commit: <to be filled in after merge>
