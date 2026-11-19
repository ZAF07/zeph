# 17 — Check-in Log: the paused reason uses the Ignore Threshold

Status: ready-for-agent

## Parent

`.scratch/redesign/PRD.md` (follow-up to `.scratch/redesign/issues/archive/10-admin-users-and-check-in-log.md`)

## What to build

Issue 10 shows paused rows with the drawn words "Three in a row went unanswered". The number is the Ignore Threshold, an Admin setting (`check_in_ignore_threshold`, 3 now), so the words go wrong when it changes. Zaf (2026-11-19): read the number from the setting, so the text says "Five in a row went unanswered" when it is 5. This needs one extra settings call on the Check-in Log page.

## Acceptance criteria

- [ ] Paused rows say "<N> in a row went unanswered", with N from the Ignore Threshold setting.
- [ ] The log still shows when the settings can't load (paused rows then say something true without a number).
- [ ] AdminCheckInLog and M-AdminCheckInLog still match by parts as in issue 10 ("Three" with the fixture at 3).
- [ ] Checks pass, and a `/run` with the setting changed shows the new number.

## Blocked by

None.

## Comments
