# 04 — Check-in polish: Check in Now

Status: completed

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

- [x] Selecting Users and pressing Check in now shows each one's result: requested, or refused and why (`test_each_selected_user_gets_their_result_and_only_requested_ones_wait`; `CheckInSchedule.test.tsx` "asks for a Check in Now for the selected Users and shows each result"; /run: "1 of 2 requested · Pia Run: Requested · Noah Run: Refused — no Telegram Connection")
- [x] A requested User gets a Check-in on the next tick even when paused, in Quiet Hours, within the half-gap, with the Feature off, over today's message limit, or past the Ignore Threshold (end-to-end tests: `test_a_paused_user_gets_the_check_in_on_the_next_tick_and_stays_paused`, `test_quiet_hours_and_the_half_gap_do_not_hold_a_check_in_now_back`, `test_the_check_ins_feature_off_for_the_user_does_not_hold_it_back`, `test_todays_message_limit_used_up_does_not_skip_it`, `test_past_the_ignore_threshold_it_asks_the_model_not_about_fewer`)
- [x] The Check-in model can still skip, and the skip is logged with the requesting Admin (`test_the_check_in_model_can_still_skip_and_the_skip_names_the_admin`)
- [x] Users not opted in, or with no Telegram Connection, are refused, and nothing is sent (`test_each_selected_user_gets_their_result_and_only_requested_ones_wait`, `test_a_user_who_has_not_finished_onboarding_is_refused`; refused Users get no write and no log row)
- [x] The next Due Time is one frequency gap after the decision. The pause and settings are unchanged (paused and skip tests assert `next_due_at == now + 1 day`, pause end and frequency unchanged; /run: decided 14:11:06, next due 14:11:06 next day, still paused until 23 Nov)
- [x] The Check-in Log shows which Admin asked. The Schedule shows waiting requests (`requested_by` in the log API, `check_in_now_waiting` on Schedule rows; `CheckInLog.test.tsx`, `CheckInSchedule.test.tsx`; /run: "Sent · Asked for by Run Admin", "Check in Now waiting" pill)
- [x] Tick reads stay flat as due and requested Users grow (`test_tick_reads_stay_the_same_as_due_and_requested_users_grow`: SELECTs by table identical for 5+5 and 15+15, every requested User actually decided)
- [x] Non-Admins are refused (`test_non_admins_are_refused_check_in_now`: 403, nothing requested)
- [x] Component tests cover selection, the action and the per-User results (`CheckInSchedule.test.tsx` +5: select and request, whole page, row click, waiting pill, failure; `CheckInLog.test.tsx` +1)
- [x] All backend and web checks pass (backend: ruff, ruff format, mypy src, pytest 1153 passed; web: lint, format:check, typecheck, 454 tests passed)
- [x] Verified with `/run-dashboard` and a webhook post: request a Check in Now for a paused User and see it sent on the next tick (see Comments)

## Blocked by

- `.scratch/check-in-polish/issues/03-check-in-schedule-and-admin-setting-changes.md`

## Notes for parallel work

Changes the same Check-in decision and tick code as track A. Rebase on whatever has merged, and renumber migrations if they clash.

## Comments

### 2026-11-16 — plan (branch `check-in-polish-04-check-in-now`)

- **Models:** `CheckInNowRequest` (requested by, requested at) on `CheckInSettings.check_in_now`; `CheckIn.requested_by`; `CheckInLogEntry.requested_by_name`; `CheckInNowResult` (requested / not opted in / no Telegram Connection).
- **Migration** `0048`: `users.check_in_now_requested_by` + `check_in_now_requested_at`, `check_ins.requested_by` (both FKs `ON DELETE SET NULL`). "Waiting" is judged by `requested_at`, so a deleted Admin doesn't drop the request.
- **Request:** `CheckInScheduleService.check_in_now(user_ids, admin)`: bulk read of Users and Telegram Connections, one bulk write for the requested ones (request + Due Time now, held-back cleared). Unknown User → 404, nothing saved.
- **Tick:** `list_due_users` also loads opted-in, onboarded Users with a request waiting, whatever the Feature switch. `decide_check_in` for a request: only no Telegram Connection (held back, request stays), mid-Conversation (waits as today; issue 05 weaves it in) and no Kind stop it; otherwise `AskModel` with next Due Time "now + gap" either way and the requesting Admin.
- **After:** `check_ins.add` clears the request (any decision); a refused send puts it back. Turning Check-ins off drops it.
- **API:** `POST /api/admin/check-in-schedule/check-in-now` `{user_ids}` → per-User result; Schedule rows gain `check_in_now_waiting`; log entries gain `requested_by`.
- **Web:** row checkboxes + "Check in now" on the Schedule with per-User results; "Check in Now waiting" on the row; "Asked for by <Admin>" in the Check-in Log.

### 2026-11-16 — code review and decisions

- **Fixed from review:** a decision cleared any Check in Now, so one asked for while the tick was already deciding a scheduled Check-in was lost. Now `check_ins.add` clears only the request the decision was made for (`test_a_check_in_now_asked_while_a_scheduled_one_is_decided_still_waits`). Users who haven't finished onboarding are refused as not opted in, since the tick never loads them. Renamed the results state.
- **Kept on purpose:** `decide_check_in_now` repeats the two short "no Telegram Connection" and "mid-Conversation" checks; pulling them out read worse and lost type narrowing. Selection stays inside `CheckInSchedule` (no separate hook) while it's this small.
- **Defaults chosen:** any unknown User id → 404 and nothing saved. While a request waits, a settings change keeps the User due now; turning Check-ins off drops it. A refused send puts the request back to wait. No Kind to send holds it back with the request kept. A request makes the User due now, and the tick still respects the Due Time, so a refused send waits the retry gap instead of retrying every minute.
- Mid-Conversation it waits as a normal Check-in would (issue 05 makes it woven in).

### 2026-11-16 — /run-dashboard (worktree stack, ports 3020/8020)

- Seeded Pia (opted in, Telegram connected with a fake chat, paused a week, mid-Conversation, 22:08 her time so also in Quiet Hours) and Noah (opted in, no Telegram Connection) with SQL. Signed in an Admin named "Run Admin".
- On `/admin/check-in-schedule` I ticked both and pressed **Check in now**: "Check in now: 1 of 2 requested · Pia Run: Requested — goes out on the next tick · Noah Run: Refused — no Telegram Connection". Pia's row showed "due now · Check in Now waiting"; no page errors.
- The real scheduler's next tick loaded Pia despite the pause and Quiet Hours and held her back only as `in_conversation`, request still waiting, requester Run Admin, no Check-in logged.
- A fake chat can't receive sends in a worktree, so I stopped the backend and ran the real app in the backend container with only the chat channel swapped for a recording one and the scheduler ticked by hand: a webhook post from Pia got Zeph's reply; tick 1 sent nothing (mid-Conversation, request waiting); after moving the Conversation's last message back 30 min, tick 2 sent "hey — monday night, and you're on my mind…" to Pia's chat. Afterwards: still paused until 23 Nov, request cleared, next Due Time exactly one day after the decision.
- Back on the real backend, `/admin/check-in-log` showed "Pia Run · Sent · Asked for by Run Admin · A casual hello", and the Schedule row no longer said waiting. 390 px: no page errors.
- Removed both seeded Users and the Clerk test user.

## Completion

- Completed: 2026-11-16
- Commits: `0bc7d59` (backend: request, tick and decision, log and Schedule API, migration 0048), `0a7e8b6` (Dashboard: selection, Check in now, results, waiting pill, "Asked for by" in the log), `ba71d15` (review fixes), `7d02ff9` (test fake), `db772b7` (archive, CONTEXT.md); merged to main in `c9f0478`
