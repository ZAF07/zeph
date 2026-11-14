# 03 — Say the Delete My Data word must be sent on its own

Status: completed

## Parent

Follow-up to `.scratch/messages/issues/archive/01-answer-texts-in-a-row-as-one-message.md` (14 Nov 2026). Texts sent in a row are now one Message, so "DELETE" followed by another text within the Message wait doesn't confirm Delete My Data; it cancels the request. That's the safe way to fail, but the User isn't told why.

## What to build

No change to when data is deleted:

- When the User asks to delete their data in chat, the Companion asks them to send the confirmation word on its own, with nothing after it.
- When a Message has the word as one of several texts, it still cancels, and the reply gets a new note (`reply_data_deletion_word_not_alone_note`, an Admin setting) telling it to say the word only counts when sent on its own and that they can ask again. Any other cancel keeps the existing note, so a User who just changed their mind isn't told about the word.
- The new note is a new setting, so seeding adds it to existing databases; no migration.

## Acceptance criteria

- [x] The ask-to-confirm text says to send the word on its own, with nothing after it
- [x] The word sent with other texts in one Message cancels and the reply gets the word-not-alone note, not the plain cancelled note
- [x] Any other cancel still gets only the plain cancelled note; the word alone still deletes
- [x] The new note is editable on the Admin reply-notes page, in the Settings in chat group
- [x] Tests at the webhook seam and the ReplyGate; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [x] `/run`: in the worktree's running backend, "DELETE" plus another text gets told why; "never mind" is not told about the word

## Comments

- First tried wording only, with one note telling the model "only if they sent the word with other text, say so". Live runs were unreliable (once it didn't explain; once it lectured a User who'd changed their mind), so the code now picks the note. Review (spec axis) caught that the single note was wrong for a plain change of mind.

### Evidence (14 Nov 2026)

- Ask text: `chat_settings.py` `_start_deleting_data` says "on its own, with nothing after it"; asserted in `tests/test_settings_via_chat.py::test_delete_my_data_in_chat_only_deletes_after_the_confirmation_word`, which also shows the word alone still deletes.
- Word with other texts: `test_the_word_with_another_text_in_one_message_cancels_and_says_why` (data kept, reply gets the word-not-alone note, not the plain one); `tests/test_reply_gate.py::test_the_word_sent_with_other_texts_gets_the_note_that_says_why`.
- Other cancels: `test_any_other_reply_cancels_delete_my_data` ("hmm, delete everything? no wait" gets only the plain note).
- Admin page: `tests/test_admin_settings.py::test_response_composition_shows_every_reply_note_in_its_group` lists the new note in Settings in chat.
- Checks: `pytest` 750 passed; `ruff check`, `ruff format --check`, `mypy` clean; web `pnpm test` 331 passed.
- `/run` (worktree backend, real app wiring and model, recording Telegram channel; User with a pending request set in SQL), two runs each:
  - "DELETE" + "oh and is it going to rain today?": nothing deleted, request cleared; replies "the delete word only counts when it's sent on its own, so nothing was deleted…" and "The DELETE word only works when you send it on its own, so nothing was deleted — ask again if you still want that.", then the rain answer.
  - "actually never mind, how was your day?": nothing deleted; replies "nothing got deleted, so you're all still here." and "Nothing was deleted — the request got cancelled before it went through.", no mention of the word.
  - An earlier run with "DELETE" + "bye for good" got the Crisis Reply: the Safeguard read it as a possible crisis, as its rule says to when unsure.
- `/code-review`: standards found no breaches; spec found the single note wrong for a plain change of mind, fixed as above.

## Completion

- Completed: 2026-11-14
- Commit: <to be filled in after merge>

## Blocked by

None - can start immediately.
