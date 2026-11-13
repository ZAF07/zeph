# 25 — A Check-in can be sent twice if saving it fails

Status: completed

## Parent

`.scratch/mvp/PRD.md` (a caveat left in `issues/archive/11-basic-check-ins.md`, still true after issue 12)

## Symptom

When a User is due a Check-in, the scheduler sends the Telegram message **first** and saves the Check-in **second**. The save also moves the User's next due time forward.

If the save fails right after the send (for example, the database drops at that moment):

- the User has the message on Telegram, but no Check-in is saved
- the next due time doesn't move, so the next tick (60 seconds later) sends **another** Check-in
- this repeats on every tick until a save works

The "would you like fewer?" message has the same problem. It is sent first, and the save is what pauses Check-ins, so a failed save could mean it is sent again and again.

- **Expected:** a User never gets the same Check-in (or the "fewer?" message) more than once.
- **Actual:** a failed save after a send leads to repeat sends. The error is caught and logged as "Could not decide on a Check-in", and the loop moves on to the next User.

This is rare, but the user wants it dealt with now rather than after it happens in a real run.

## Repro

Not seen in a real run. It can be shown in a seam 2 test (the scheduler tick with FakeClock): make `check_ins.add` raise once after `send_text`, run two ticks, and see two messages sent.

## Suspected location

- `src/companion/core/check_ins.py`, `CheckInService._send_if_due`: `send_text` is called, then `check_ins.add`.
- `src/companion/core/check_ins.py`, `CheckInService._ask_about_fewer`: same order.
- `src/companion/core/check_ins.py`, `CheckInService.send_due`: catches the error per User and logs it.

## Decisions (from /grill-with-docs, 2026-11-13)

1. **Book first, send, undo on a clear refusal.** For both a Check-in and the "fewer?" message: save the Check-in and move the next due time (and, for "fewer?", the pause) first, then send. A failed save means nothing was sent, so the next tick simply tries again.
2. **Undo only when Telegram clearly refused.** If Telegram answered with an error, delete the booked Check-in and put the User's settings back as they were. If the result is unknown (timeout, dropped connection), keep the booking: it counts as sent, since it may have arrived. Never sent twice beats never missed.
3. **Retry a refusal 15 minutes later**, a constant in code, not on the next tick. The retry goes through the normal due checks (Feature, pause, quiet hours, open Conversation), so it still respects them. This keeps Check-in model calls low during a Telegram outage.
4. **Blocked bot counts as a Skipped Check-in.** When Telegram says the User blocked the bot (403 "bot was blocked by the user"), don't undo: record a Skipped Check-in with an Admin-only reason (e.g. "User has blocked the Companion on Telegram") and wait a full frequency gap, so it fixes itself once they unblock. Same for the "fewer?" message. Glossary updated: a Skipped Check-in is one the Companion chose not to send, or couldn't because the User blocked it.
5. **The only gap left:** if a refused send's undo also fails, that one Check-in is missed (logged), never repeated.
6. **A Shared Photo that fails after the message** stays as now: the message counts as sent, and the booked Check-in is updated to have no Shared Photo.
7. **Usage stays as it is.** Check-ins never count toward the Daily Message Limit (it counts only messages the User sends). Their tokens still show in the Admins' Usage, which limits nothing.

Rejected: send first and retry the save (a repeat is still possible); undo on any failure (a slow Telegram causes a repeat); retry on every tick (about 1,440 model calls a day for a blocked User).

## Acceptance criteria

- [x] A Check-in and the "fewer?" message are saved, with the next due time moved, before they are sent
- [x] A failed save sends nothing; the next tick tries again (seam 2: two ticks, one message)
- [x] When Telegram refuses the send, the booked Check-in is removed and the User's settings are put back; the next try is 15 minutes later
- [x] When the send result is unknown (timeout, connection error), the booking is kept and counts as sent; it is not sent again
- [x] When the User has blocked the bot, it is recorded as a Skipped Check-in with an Admin-only reason and the next try is a full frequency gap later; same for "fewer?"
- [x] The Telegram adapter tells a clear refusal, a blocked bot and an unknown result apart, through the `ChatChannel` port
- [x] A Shared Photo that fails after the message leaves the Check-in sent with no Shared Photo
- [x] Tests cover all of the above (seam 2, and the adapter's error mapping)
- [x] `make check` passes (ruff, ruff format, mypy, pytest, and the web checks)
- [x] Verified with `/run`: a refused send, a blocked User and a failed save each behave as above in the running stack

## Comments

**2026-11-13 — done on branch `mvp-25-check-in-sent-twice`.** What changed and the evidence:
- Book first: `CheckInService._save_then_send` (`core/check_ins.py`) saves the Check-in with the next due time (and, for "fewer?", the pause) through `check_ins.add`, then sends. Both a Check-in and "fewer?" go through it. Tests (`tests/test_check_in_send_failures.py`): `test_a_failed_save_sends_nothing_and_the_next_tick_tries_again` (two ticks, one message), `test_a_failed_save_of_would_you_like_fewer_sends_nothing_and_tries_again`.
- Refused: Telegram's `MessageRefusedError` → `check_ins.undo_add` deletes the booking and sets the next due time 15 minutes on (`REFUSED_CHECK_IN_RETRY_GAP`), ending the pause only if the booking started one, so a pause the User set meanwhile is kept. Tests: `test_a_refused_check_in_is_taken_back_and_tried_again_15_minutes_later`, `test_a_refused_would_you_like_fewer_is_taken_back_and_tried_again_later`, `test_a_pause_set_while_the_model_decides_survives_a_refused_send` (red before the review fix, green after).
- Unknown result (timeout, 5xx, no answer): the booking is kept and counts as sent, logged "Could not tell if a Check-in arrived; it counts as sent". Test: `test_a_send_with_an_unknown_result_counts_as_sent_and_is_not_sent_again`.
- Blocked: `ChatBlockedError` → the booking is swapped for a Skipped Check-in with the Admin-only reason "User has blocked the Companion on Telegram", the next try a full frequency gap later, with no pause. Tests: `test_a_user_who_blocked_the_companion_gets_a_skipped_check_in_and_a_full_gap` (reason checked in the Admin log API), `test_would_you_like_fewer_to_a_user_who_blocked_the_companion_is_skipped`.
- Undo fails: the booking stays and the error is logged, so the Check-in is missed, never repeated. Test: `test_a_refused_check_in_whose_undo_fails_is_missed_not_sent_again`.
- Port and adapter: `MessageRefusedError` and `ChatBlockedError` live in `core/ports.py` and are listed on `ChatChannel.send_text`. `to_telegram_api_error` returns `TelegramBlockedError` for any 403 and `TelegramRefusedError` for other 4xx answers; 5xx and no answer stay plain `TelegramApiError` (unknown). Tests in `tests/adapters/test_telegram_chat_channel.py`: 403 blocked and 403 deactivated, then 400, 429, 502 and a read timeout.
- Shared Photo: the booking holds the photo; if sending the photo fails, `check_ins.remove_shared_photo` clears it and the Check-in stays sent. Test: `tests/test_look_back_check_in.py::test_a_failed_photo_send_still_sends_the_message_and_logs_the_error` (the reply history has no photo).
- Checks: `make check` passed: ruff, ruff format, mypy (94 files), pytest 571 passed, ESLint, Prettier, tsc, Vitest 314 passed.
- `/run` (worktree stack, `make db-copy`, a fake Telegram link with chat id 1, real DeepSeek and the real Telegram API):
  - Refused: Telegram answered 400 "chat not found" and the log showed "The chat channel refused a Check-in…". 0 Check-ins were saved, the next due time moved to +15 min (14:24 → 14:39) and the User wasn't paused. This was checked again after the review fixes (14:34 → 14:49).
  - Failed save: a Postgres trigger made the Check-in insert fail. The ticks at 14:25 and 14:26 logged "Could not decide on a Check-in" with no send attempted, and the due time didn't move. With the trigger dropped, the 14:27 tick saved and then sent (refused again, as expected for chat id 1).
  - Blocked: Telegram only says "blocked" for a real person who blocked the bot, so the real `CheckInService`, Postgres repositories, DeepSeek model and `TelegramChatChannel` ran in the backend container, with only the HTTP layer answering 403. Results:
    - A Check-in to a User who blocked the bot became a Skipped row with the reason and no Kind or message, the next due time moved a full gap (+2d 8h) and the User wasn't paused.
    - "Fewer?" behaved the same, also for 403 "user is deactivated" after the review fixes.
    - A read timeout kept a sent Check-in and logged the "counts as sent" line.
- Code review (Standards and Spec): no hard Standards breaches. Fixed:
  - Undo used to write the pause from the start-of-tick copy of the User, so a pause set during the model call could be lost. It now changes only the next due time and the pause the booking started.
  - Permanent 403s (deactivated, kicked) would have been retried every 15 minutes (about 96 model calls a day), so every 403 now takes the blocked path.
  - Added the undo-fails test, and the docstring now says "retry gap" instead of a hard-coded 15 minutes.
  - Left as is: the explicit `message` argument (`CheckIn.message` is optional), and the two short undo branches.

Caveats:
- Any 403 counts as blocked, not only "bot was blocked by the user" (Decision 4 named just that one). A deactivated User is also logged with the reason "User has blocked the Companion on Telegram", the closest reason Admins have.
- A 400 such as "chat not found" is still a refusal retried every 15 minutes. That only happens if a Telegram link points at a chat that no longer exists.
- When the text's result is unknown, the Shared Photo is still sent, since the Check-in counts as sent.
- If clearing the Shared Photo after a failed photo send also fails, the Check-in keeps a photo that wasn't sent. This is logged, not a repeat send.
