# 02 — Failed Check-in decisions back off

Status: needs-triage

> **Owner: run `/grill-with-docs` before picking this up.** See `.scratch/check-in-job/PRD.md` for the findings and options. Open questions for the grill: how long the backoff is, how many failures before giving up, and what the Skipped Check-in reason says to Admins.

## Parent

`.scratch/check-in-job/PRD.md`

## What to build

Today a Check-in decision that fails before it is saved (the model's answer can't be used, or the call fails) is tried again on every tick, forever, and each try is a paid model call. Instead, a failed decision moves the User's Due Time back by a short wait. After a few failures in a row, the Companion records a Skipped Check-in with a reason Admins see in the Check-in Log, and the next Due Time follows as after any skip. A Check in Now that fails the same way is shown to the Admin as failed instead of retrying forever.

## Acceptance criteria

- [ ] A failed decision is not tried again until the backoff wait has passed.
- [ ] After the set number of failures in a row, a Skipped Check-in is logged with its reason and the rhythm carries on.
- [ ] A successful decision resets the failure count.
- [ ] Tests cover backoff, giving up, and reset.
- [ ] A `/run` with a model that returns bad answers shows the backoff and then the skip in the Check-in Log.

## Blocked by

None - can start immediately

## Comments
