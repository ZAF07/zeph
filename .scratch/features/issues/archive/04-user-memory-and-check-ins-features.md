# 04 — User Memory and Check-ins as Features

Status: completed

## Parent

`.scratch/features/PRD.md`

## What to build

User Memory and Check-ins join the Feature list. These two also have the User's own switch, so a Feature works only when the Admin side allows it and the User has it on.

- An Admin "off" never changes the User's own choice; when the Admin side turns back on, the User's own setting applies again.
- User Memory off by an Admin behaves exactly like the User turning it off: memory retrieval, memory processing at Conversation end and Check-in choice keep and use nothing. Nothing is deleted, and the User can still see and delete their memories on the Dashboard.
- Check-ins off by an Admin: none are decided or sent.
- On the Dashboard, a switch whose Admin side is off shows "Not available on your account" and is disabled. The User API refuses changes to it and changes nothing. The statuses come from the backend; the Dashboard holds no rule.

## Acceptance criteria

- [x] With User Memory off by an Admin, nothing new is kept or used, existing memories stay viewable and deletable, and the User's own switch is unchanged
- [x] With Check-ins off by an Admin, no Check-in is sent and the User's Check-in settings are unchanged
- [x] Turning the Admin side back on restores the User's own choice
- [x] The Dashboard shows "Not available on your account" with the switch disabled, and the API refuses the change
- [x] The per-User panel shows "Off: the User turned it off" when only the User's switch is off
- [x] Seam 1 tests cover the API and memory retrieval; seam 2 tests cover memory processing and Check-ins; seam 3 tests cover the disabled switches
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/features/issues/02-per-user-feature-switches.md`

## Comments

**2026-11-13: implemented, reviewed and verified** on branch `feat/features-04-user-memory-and-check-ins`.

Done and verified: every acceptance criterion. `make check` passed on the final code (exit 0). Python: 370 passed. Web: 287 passed. ruff, ruff format, mypy, eslint, prettier and tsc were clean.

Docker run with real Postgres and Clerk (dev), signed in as a temporary Clerk test Admin. The Companion-side checks used a probe inside the backend container, built from the real repositories and services. The probe used a recording chat model and a recording channel, so nothing went to DeepSeek or Telegram.
- Users page → Features on the test User's row → set User Memory and Check-ins to Off. Both showed "Off: turned off for this User" with who and when.
- Memories, Account & privacy and Check-ins pages: the switch was disabled, still showed the User's own choice (on), and read "Not available on your account". Memories showed "Memory isn't available on your account… Nothing has been deleted." Check-ins showed "Check-ins aren't available on your account… Your settings are kept." The Home Check-ins card showed "Off · Not available on your account".
- `PATCH /api/me {user_memory_enabled:false}` and `PATCH /api/check-ins {enabled:false}` → 403 "Not available on your account". `GET` afterwards: the User's own switches were still on, with `available: false`.
- Probe while off: works user_memory=False, check_ins=False, and the User's own switches were still True.
  - Memory retrieval left out the User's Memory Item.
  - Check-in Kinds were limited to the 2 allowed without User Memory.
  - Check-in at 12:00 UTC: 0 model calls, nothing sent.
  - Conversation-end processing: 0 model calls, 0 summaries.
- Back to Default → the panel showed "On: on for everyone", and the User's own choices still applied (both on, available).
  - Probe: retrieval included the Memory Item and all 4 Kinds came back.
  - Check-in at 12:00 UTC: 1 model call, the message was sent to the recording channel.
- The User turned Memory off themselves on the Memories page ("Memory paused"). The panel showed "User Memory · Off: the User turned it off". It was turned back on afterwards.
- At 390px the Memories page with the not-available note had no sideways scroll (scrollWidth 390). No page errors and no backend errors in the logs.
- Clean-up: deleted the test User from Clerk and the database (its Telegram Connection, probe Memory Item, Conversation, Check-in and Feature switches went with it). Confirmed 0 rows left. No real Users were touched.

Decisions:
- Each Feature status now has `available` (the Admin side allows it). `works` is `available` plus, for User Memory and Check-ins, the User's own switch being on. Reasons, in order: off for this User, off for everyone, `turned_off_by_user` ("Off: the User turned it off").
- The "not available on your account" note in replies lists only Features the Admin side has off, never ones the User turned off themselves.
- The Admin side only blocks changing the on/off switch (`UserService.update_preferences` and `CheckInService.change_settings` raise `FeatureNotAvailableError`, which the API turns into 403). Frequency, quiet hours and pausing can still be changed and are kept.
- The chat tool for turning User Memory on or off tells the model it isn't available, and changes nothing. Without this it would have crashed. The rest of Settings in Chat is issue 05.
- With Check-ins off by an Admin, the User stays due. A Check-in may go out on the first tick after the Admin side comes back on.
- `GET /api/me` has `user_memory_available`. `GET /api/check-ins` and the home `check_ins` have `available`. The Dashboard shares one `notAvailableText`.

Caveats, left for later:
- Answering onboarding again still sets the User's own User Memory and Check-ins choice while the Admin side is off. This is their own switch, and refusing it would block sign-up when a Feature is off for everyone. It changes nothing the Admin set.
- The Home Goals and Recently remembered sections still follow the User's own switch. Seeing their own data always works.

Review (`/code-review`):
- Standards: no hard violations.
- Spec: found the Home Check-ins card still showed Check-ins on, and the onboarding gap.
- Fixed: the Home card shows not available, one shared not-available text on the Dashboard, clearer `memoryUnavailable` in Memories, and the `me_response` name.
- Left: the `own_switch_on` if-cascade (only two Features), the repeated 403 handling, and repeated reads of the switches in Check-in sending (small cost).

Evidence:
- Seam 1 and seam 2: `tests/test_features.py`, 9 new tests.
  - Reasons when the User turned it off.
  - Reason order.
  - Memory not used and the own choice kept.
  - Memories still deletable.
  - API 403.
  - Chat refusal.
  - Conversation end keeps nothing.
  - No Check-ins until back on (and the home `available`).
  - Check-ins chosen without memory.
- Seam 3:
  - `Memories.test.tsx`, `AccountSettings.test.tsx`, `CheckInsSettings.test.tsx` and `DashboardHome.test.tsx`: disabled switch / not available.
  - `UserFeaturesPanel.test.tsx`: "Off: the User turned it off".

## Completion

- Completed: 2026-11-13
- Commit: b7af9cb "Features issue 04: User Memory and Check-ins join the Feature list…", review fixes 34e690a "Features issue 04 review fixes: Home Check-ins card shows \"Not available on your account\"…", archive 57014ae "Features issue 04 done: archive issue with run evidence…" (merged from `feat/features-04-user-memory-and-check-ins` in adf7e64 "Merge Features issue 04…"; `make check` green on main after the merge: Python 370 passed, web 287 passed)
