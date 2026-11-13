# 25 — A Check-in can be sent twice if saving it fails

Status: needs-triage

## Parent

`.scratch/mvp/PRD.md` (a caveat left in `issues/archive/11-basic-check-ins.md`, still true after issue 12)

## Before deciding on a solution

Run `/grill-with-docs` on this issue first. The user wants to grill the problem with the docs before a solution is picked, so don't start on a fix until that is done.

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

## Acceptance criteria

- [ ] A failed save after a send no longer causes the Check-in or the "fewer?" message to be sent again
- [ ] What happens when the send itself fails is decided and covered
- [ ] Tests cover the fixed behaviour (seam 2)
- [ ] `make check` passes (ruff, ruff format, mypy, pytest, and the web checks)
