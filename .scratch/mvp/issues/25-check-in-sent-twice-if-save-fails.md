# 25 — A Check-in can be sent twice if saving it fails

Status: ready-for-agent

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

- [ ] A Check-in and the "fewer?" message are saved, with the next due time moved, before they are sent
- [ ] A failed save sends nothing; the next tick tries again (seam 2: two ticks, one message)
- [ ] When Telegram refuses the send, the booked Check-in is removed and the User's settings are put back; the next try is 15 minutes later
- [ ] When the send result is unknown (timeout, connection error), the booking is kept and counts as sent; it is not sent again
- [ ] When the User has blocked the bot, it is recorded as a Skipped Check-in with an Admin-only reason and the next try is a full frequency gap later; same for "fewer?"
- [ ] The Telegram adapter tells a clear refusal, a blocked bot and an unknown result apart, through the `ChatChannel` port
- [ ] A Shared Photo that fails after the message leaves the Check-in sent with no Shared Photo
- [ ] Tests cover all of the above (seam 2, and the adapter's error mapping)
- [ ] `make check` passes (ruff, ruff format, mypy, pytest, and the web checks)
- [ ] Verified with `/run`: a refused send, a blocked User and a failed save each behave as above in the running stack
