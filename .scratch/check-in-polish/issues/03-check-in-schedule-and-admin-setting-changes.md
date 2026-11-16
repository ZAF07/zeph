# 03 — Check-in polish: Check-in Schedule page and Admin Setting Changes

Status: ready-for-agent

Track: B (Admin side). Runs alongside track A (issues 01, 02).

## Parent

`.scratch/check-in-polish/PRD.md`

## What to build

A new admin **Check-in Schedule** page where Admins see every opted-in User's Check-in state and can change their Check-in settings for them.

- **Held-back reason.** When a tick holds a User back, it saves the reason, and the time until when it's known, in the same bulk write as the Due Time. Any decision (sent, skipped, ask about fewer) clears it. No history is kept.
- **Schedule (admin API and page),** searchable by name or email and paged. Each row has:
  - name and email
  - Due Time, shown as "in 3 h · Tue 10:00 their time", or "due now"
  - Check-in Frequency, Quiet Hours and pause (and until when)
  - whether the Check-ins Feature works for them
  - held back now: the reason and until when (e.g. "Quiet Hours, until 07:30")

  No message content anywhere.
- **Admin Setting Change.** Clicking a row opens a side panel where the Admin changes the User's frequency and Quiet Hours, or pauses (a day, a week, until resumed) and resumes them.
  - These are the User's **real** settings, changed through the same Check-in service rules the User's own changes use (e.g. changing Quiet Hours that hold a Check-in back decides it again straight away).
  - Each changed setting is marked "changed by an Admin", stored like the existing chat marks.
  - The User's own change (Dashboard or chat) clears the admin mark. A chat change sets the chat mark instead.
  - Admins **can't** opt a User in or out. Stopping Check-ins for a User is the existing per-User Feature switch.
- **User side:** the User's Check-ins page shows "Changed by an Admin" next to each marked setting.
- **Admin nav** gains the page, next to Check-in Log and Check-in Kinds. Build it from `docs/design/zeph-admin.html` table and side-panel patterns (skip anything tagged "Later"). All calls go through the API client (ADR-0012).

Terms: Admin Setting Change, Held-back Check-in, Due Time (`CONTEXT.md`).

## Acceptance criteria

- [ ] The Schedule lists only opted-in Users, with Due Time, settings, Feature status and current held-back reason and until, searchable and paged.
- [ ] Held-back reasons appear for paused, Quiet Hours, no Telegram Connection, today's message limit used up and no Kind to send, and clear once the Check-in is decided.
- [ ] Schedule reads stay bulk: no per-User queries (test that read counts don't grow with Users).
- [ ] An Admin can change a User's frequency and Quiet Hours, and pause or resume them. The User's real settings change, and the rules match the User's own changes.
- [ ] The User's Check-ins page shows "Changed by an Admin". The User changing it back clears the mark, on the Dashboard and in chat.
- [ ] There's no way for an Admin to turn a User's Check-ins switch on or off.
- [ ] Non-Admins get refused by the new endpoints.
- [ ] Component tests cover the Schedule table, the side panel and the "Changed by an Admin" mark.
- [ ] All backend and web checks pass.
- [ ] Verified with `/run-dashboard` as a signed-in Admin: see the Schedule, change a User's settings, see the mark as that User.

## Blocked by

None - can start immediately.

## Notes for parallel work

Track A (issue 02) adds a "waiting to be woven in" held-back state. Leave room for more reasons. Track A also changes the Check-in decision and tick code and adds migrations. Whichever merges second rebases, and renumbers its migration if they clash.

## Comments
