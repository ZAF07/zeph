# 02 — Per-User Feature switches and the Admin Features panel

Status: completed

## Parent

`.scratch/features/PRD.md`

## What to build

Admins can set any Feature to default, on or off for one User, shown with Web Search.

- Per-User switch storage: a row only when it isn't "default" (on/off, changed by, changed at); setting back to default removes it.
- The rule: the per-User switch if on or off, otherwise the switch for everyone. Per-User "on" gives a User a Feature that is off for everyone.
- Each row on the admin Users page gets a Features button that opens a panel: one row per Feature with default/on/off, whether it works for that User right now, why ("Off: turned off for everyone", "Off: turned off for this User", "On: turned on for this User"), and the last change. Keep the panel uncluttered.
- Delete My Data keeps per-User switches; Account Deletion removes them.

## Acceptance criteria

- [x] An Admin can set Web Search to default, on or off for one User from the Users page panel
- [x] Per-User off stops Web Search for that User only; per-User on gives it to that User while it is off for everyone; default follows the switch for everyone
- [x] The panel shows whether each Feature works now, the reason and the last change (who, when)
- [x] Delete My Data keeps the User's switches; Account Deletion removes them
- [x] Non-Admins can't call the per-User endpoints
- [x] Seam 1 tests cover the rule, reasons, last change and deletion cases; seam 3 tests cover the panel
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/features/issues/01-features-and-web-search-switch.md`

## Comments

**2026-11-13 — implemented, reviewed and verified** on branch `feat/features-02-per-user-switches`.

Done and verified: every acceptance criterion. `make check` green (exit 0: Python 356 passed; web 280 passed; ruff, ruff format, mypy, eslint, prettier, tsc clean).

Docker run with real Postgres, Clerk (dev), DeepSeek and Tavily, signed in as a temporary Clerk test Admin:
- Migration 0016 ran on the real install: `user_feature_switches` with a cascading `user_id` and `changed_by` set to null on delete.
- Users page → Features on the owner's row → panel "Features for zaf": Web Search, Default pressed, "On: on for everyone", no page errors.
- Off for the owner only → "Off: turned off for this User", "Changed 13 Nov, 13:00 by run-check-…"; row stored with who and when. Message to the webhook as the owner's Telegram account ("look up who won the Ballon d'Or") → no search (count 5 → 5); reply said web search isn't on their account.
- Off for everyone from the Features page, then On for the owner → "On: turned on for this User". A direct ask to search → 1 search (5 → 6), real answer with source. (The first ask after the earlier "not available" replies didn't search: the tools were offered, which was confirmed by asking the running backend's `FeatureService` (works=True) and seeing the limit was 10 with 1 used, but the model followed its own earlier replies.)
- Back to Default → "Off: turned off for everyone", no last change shown, row removed; next ask → no search (6 → 6).
- Delete My Data from Account & privacy (test Admin set to Off for itself first) → "Your data has been deleted", switch row kept. Delete my account → `DELETE /api/me` 204, user gone, switch rows for that id 0.
- Plain User: `/admin/users` sent to `/`; `GET`/`PUT /api/admin/users/{id}/features…` → 403/403. No token → 401.
- 390px: panel fits, no sideways scroll. No backend errors in the logs.
- Clean-up: both test Users deleted from the database and Clerk (plus one Clerk test user left by a timed-out first session attempt); Web Search reset to on with no recorded change; no per-User rows left. The test messages and replies stay in the owner's own Conversation.

Decisions:
- `user_feature_switches` (user_id, feature, is_on, changed_by, changed_at), a row only when the switch isn't "default". Setting Default removes the row, so a Default row shows no last change (who set it back to Default isn't kept), as the storage rule says.
- `FeatureService.statuses_for(user_id)` and `set_for_user(user_id, feature, switch, admin)`; `works_for`/`unavailable_for` go through the rule (`status_for`), so Web Search tools and the not-available note follow the per-User switch. Unknown User → `UserNotFoundError` → 404.
- Reasons: `on_for_everyone` ("On: on for everyone"), `on_for_user`, `off_for_everyone`, `off_for_user`. "The User turned it off" comes with User Memory and Check-ins (issue 04).
- Admin API: `GET /api/admin/users/{id}/features`, `PUT /api/admin/users/{id}/features/{feature}` with `{"switch": "default"|"on"|"off"}`; unknown Feature or switch → 422.
- Panel: a dialog from a Features button on each Users row; Default/On/Off buttons save at once; a failed change shows an alert and keeps the switch; Escape or Close closes it. `lastChangeNote` moved to `web/src/lib/features.ts` so the Features page and the panel share it.
- Users table: the two row buttons are stacked and the User cell has a minimum width, so the extra button doesn't squeeze names; `relative` on the scroll box stops the sr-only "Actions" label from making the whole page scroll sideways at 390px (that problem was already there before this change).

Review (`/code-review`): Standards had no hard violations; fixed the not-found error to pass the id, put the user check in one `_require_user`, and renamed `everyone`/`for_user` to `everyone_switch`/`user_switch`. Left: a bool `is_on` in storage, a shared "last change" type, and a shared pill-button component (minor or wider than this issue). Spec found nothing wrong; added a test that Delete My Data in chat keeps the switches.

Evidence: seam 1 `tests/test_features.py` (9 new: default follows everyone with reasons; off for one User stops Web Search tools for them only, with who/when; on for one User while off for everyone; back to default follows everyone and forgets the change; only Admins; unknown User/Feature/switch refused; Delete My Data on the Dashboard and in chat keeps switches; Account Deletion removes them). Seam 3 `web/src/components/UserFeaturesPanel.test.tsx` (9: switches and status, each reason, who/when, turning off, failed change, Try again, Close/Escape), `AdminUsers.test.tsx` (Features button opens the panel), `web/src/lib/features.test.ts` (3).

## Completion

- Completed: 2026-11-13
- Commit: <to be filled in after merge>
