# 04 — Check-in polish: Check in Now

Status: ready-for-agent

Track: B (Admin side).

## Parent

`.scratch/check-in-polish/PRD.md`

## What to build

On the Check-in Schedule, an Admin selects Users and presses **Check in now**. Each selected User gets a Check-in on the next tick.

- **Request (admin API):** takes a list of User ids and returns a result for each:
  - **requested**: saved on the User along with the requesting Admin, and the Due Time is set to now
  - **refused: not opted in**
  - **refused: no Telegram Connection**

  The page shows each result. Refused attempts aren't logged.
- **Tick:** it loads Users who are due *or* have a Check in Now waiting, including those with the Check-ins Feature off, in the same bulk read.
- **For a User with a Check in Now waiting,** the decision goes past:
  - the Feature switch
  - the pause
  - Quiet Hours
  - the half-gap minimum
  - the Daily Message Limit skip
  - the Ignore Threshold "would you like fewer?" step

  It goes straight to the Check-in model, which may still send or skip.
  - If the User has since lost their Telegram Connection, it is held back with that reason and the request stays.
  - Mid-Conversation it waits as a normal Check-in would. Issue 05 makes it woven in.
- **After the decision:**
  - The saved Check-in records the requesting Admin.
  - The request is cleared on any decision.
  - The next Due Time is "decided at + frequency gap".
  - Pause and other settings are left as they were.
- **Check-in Log** shows "asked for by <Admin name>". The Schedule shows a waiting request, so an Admin doesn't press it twice.

Terms: Check in Now, Check-in Log (`CONTEXT.md`).

## Acceptance criteria

- [ ] Selecting Users and pressing Check in now shows each one's result: requested, or refused and why.
- [ ] A requested User gets a Check-in on the next tick even when paused, in Quiet Hours, within the half-gap, with the Feature off, over today's message limit, or past the Ignore Threshold (end-to-end tests).
- [ ] The Check-in model can still skip, and the skip is logged with the requesting Admin.
- [ ] Users not opted in, or with no Telegram Connection, are refused, and nothing is sent.
- [ ] The next Due Time is one frequency gap after the decision. The pause and settings are unchanged.
- [ ] The Check-in Log shows which Admin asked. The Schedule shows waiting requests.
- [ ] Tick reads stay flat as due and requested Users grow.
- [ ] Non-Admins are refused.
- [ ] Component tests cover selection, the action and the per-User results.
- [ ] All backend and web checks pass.
- [ ] Verified with `/run-dashboard` and a webhook post: request a Check in Now for a paused User and see it sent on the next tick.

## Blocked by

- `.scratch/check-in-polish/issues/03-check-in-schedule-and-admin-setting-changes.md`

## Notes for parallel work

Changes the same Check-in decision and tick code as track A. Rebase on whatever has merged, and renumber migrations if they clash.

## Comments
