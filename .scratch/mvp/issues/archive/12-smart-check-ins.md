# 12 — Smart Check-ins

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

Check-ins feel like a friend who knows how you've been. Before sending, the Check-in service reads the User's recent Conversation Summaries and Memory Items and decides either a Check-in Kind and message, or to skip with a reason (e.g. the User asked for space). A skip moves the next attempt to the following scheduled slot. After the Admin-set number of consecutive ignored Check-ins, the Companion sends one "would you like fewer?" message and pauses Check-ins. With User Memory off, only Check-in Kinds allowed without User Memory (casual hello) are used.

On the User's Check-ins page, skipped Check-ins appear in "Recent check-ins" as "Skipped — gave you some space" (never the internal reason), the Check-in Kinds are shown as a read-only "What Zeph might reach out about" list, and the ignore rule is explained.

Admins manage Check-in Kinds (name, description, allowed without User Memory) and see Check-in sends and skips with skip reasons, never message content.

## Design

- `docs/design/zeph-product.html`: Check-ins (skipped entries, "What Zeph might reach out about", ignore rule)
- `docs/design/zeph-admin.html`: Check-in Kinds, Check-in log

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [x] The Check-in service chooses a Check-in Kind using recent Conversation Summaries and Memory Items
- [x] The service can decide to skip; the reason is recorded and the next attempt moves to the following slot
- [x] After the configured number of consecutive ignored Check-ins, one "would you like fewer?" message is sent and Check-ins pause; a User reply resets the count
- [x] With User Memory off, only Check-in Kinds allowed without User Memory are chosen
- [x] The User's Check-ins page shows skips as "gave you some space", a read-only list of active Check-in Kinds, and a plain explanation of the ignore rule
- [x] Admins can add, edit and remove Check-in Kinds and set the ignore threshold
- [x] Admins can see Check-in sends and skips with reasons, never message text
- [x] Seam 2 tests with a fake chat model and clock cover: kind chosen and sent, skip recorded and rescheduled, ignore threshold → pause message, User Memory off → casual hello only
- [x] Seam 3 tests cover the admin Check-in pages and the User Check-ins page additions
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/04-admin-area-foundation.md`
- `.scratch/mvp/issues/11-basic-check-ins.md`

## Comments

**2026-11-12 — started on branch `feat/12-smart-check-ins`.** Plan:
- One Check-in model call per due User decides: it gets the Persona + Check-in prompt, the Check-in Kinds it may pick (only those allowed without User Memory when memory is off), the User's name and local time, their recent Check-in decisions and, with User Memory on, their Memory Items and recent Conversation Summaries. It answers JSON: send with a Kind and message, or skip with a reason. A bad answer (unknown or not-allowed Kind, no message, no JSON) sends nothing and is tried again next tick, like a model error today.
- `check_ins` rows become decisions: `outcome` (sent / skipped / asked_about_fewer), `skip_reason`, nullable `message`, and `sent_at` renamed `decided_at`. Skips and sends both set the next due time one frequency gap on.
- Ignored streak is worked out, not stored: the User's newest sent Check-ins with no reply, counting back until one was replied, the last "would you like fewer?" message, or the User's last Conversation started. At the Admin-set `check_in_ignore_threshold` (default 3) the Companion sends the Admin-set `check_in_fewer_message` (no model call), records it and pauses Check-ins until the User resumes. A reply to any Check-in breaks the streak.
- Old `check_in_prompt` (plain text answer) is replaced by a JSON one; migration 0012 removes the stored row so the new seed value loads.
- Admin API: CRUD `/api/admin/check-in-kinds` (with sends in the last 30 days), `GET /api/admin/check-ins?days=` (time, User, outcome, Kind, skip reason, reply; never the message). Threshold and message on Platform settings.
- User API: `GET /api/check-ins` adds the Kinds that may be sent to this User; recent entries carry an `outcome` and the new `skipped` status, never the reason.
- Dashboard: Check-in Kinds and Check-in log admin pages, Check-ins section on Platform settings, and on the Check-ins page skipped entries ("Skipped — gave you some space", date only), "What Zeph might reach out about" and the ignore rule line.
- Quiet hours, pause, no Telegram and mid-Conversation still hold a Check-in back each tick without a log entry; the log only shows the service's decisions.

**2026-11-12 — implemented, reviewed and verified.** Commits `6452635`, review fixes `0b444b1`, run fix `ba394e6` on `feat/12-smart-check-ins`.

Done and verified: every acceptance criterion. `make check` green (Python 268, web 220; ruff, ruff format, mypy, eslint, prettier, tsc clean). Migration 0012 ran on the existing database (0011 → 0012); the old Check-in prompt (never edited by an Admin) was replaced by the new JSON one, and `check_in_ignore_threshold` (3) and `check_in_fewer_message` seeded. Docker run with real Postgres, Clerk (dev), DeepSeek and Telegram:
- Real ticks on the owner account (11 Memory Items, 2 Conversation Summaries): DeepSeek chose "A casual hello" and wrote "hey, how's the week going? still riding that new-job high?" (from a Summary). Next due moved +24h.
- Skip: with a temporary Memory Item saying they asked for a quiet week, DeepSeek skipped: "They explicitly asked for a quiet week with no messages while grieving; this falls within that window." Nothing sent; next due +24h.
- A later tick sent "A follow-up" ("hey zaf, how'd the monstera settle in? and did the salary actually land…"), drawing on Summaries.
- Ignore threshold: with 3 unanswered sends in a row (one of them synthetic), the next tick sent the fewer message, with no model call, recorded it, and paused Check-ins until resumed.
- Dashboard in Chrome (Playwright), as a temporary Clerk Admin:
  - Check-ins page: "What Zeph might reach out about" lists the 4 Kinds (2 with User Memory off). Recent check-ins shows "Skipped — gave you some space · Mon 9 Nov", with no reason anywhere on the page. The ignore-rule line is shown. No sideways scroll at 390px.
  - Check-in Kinds: cards show "Sent N times in 30 days". Add, edit, a duplicate name refused with the backend's message, save survives reload, remove after confirming.
  - Check-in log: totals (Sent 5, Skipped 2, Replied to 20%, Paused by ignore rule 1). Rows show the real skip reason and "Ignore threshold reached — asked once about fewer". No message text. Sent/Skipped and user filters and the 30-day period work.
  - Platform settings: ignore threshold 3 → 4 survives reload, then set back to 3. Prompts & models shows the new Check-ins description.
- Found and fixed in /run: the log's Reply column said "Sent" for a send still in its reply window; it now says "Waiting".
- Clean-up: owner Check-ins back off and unpaused; the run's Check-ins, test Memory Item and test Kind deleted; the temporary User deleted from the database and Clerk; threshold back to 3.

Decisions:
- One Check-in model call per due User returns JSON: send (Kind by name + message) or skip (reason). An answer it can't use (no JSON, a Kind it wasn't offered, empty message or reason) sends nothing and is tried again next tick, like a model error.
- The model gets the Persona + `check_in_prompt`, the Kinds it may pick, the User's name and local time, their last 5 Check-in decisions and, with User Memory on, their Memory Items (active categories) and newest Conversation Summaries.
- User Memory off: only Kinds allowed without User Memory are offered, and no memories are given. The User's page lists only those Kinds too.
- `check_ins` rows are decisions: `outcome` (sent / skipped / asked_about_fewer), `skip_reason`, nullable `message`, `sent_at` renamed `decided_at`. Skips and sends both set the next due time one frequency gap on. Saving a decision writes only the next due time (and the pause for the fewer message), so a change the User makes during the model call is kept.
- The ignored count is worked out, not stored. It counts newest sent Check-ins with no reply, stopping at a replied one, the last fewer message, or Check-ins sent before the User last started a Conversation. So any message from the User resets it, not only a reply inside the window.
- At `check_in_ignore_threshold` (Admin-set, 1–10, default 3), the Companion sends `check_in_fewer_message` (Admin-set text, no model call), records it, and pauses Check-ins until the User resumes.
- Quiet hours, pause, no Telegram and mid-Conversation still hold a Check-in back each tick with no log entry. The log shows only the service's decisions.
- Admin API: CRUD `/api/admin/check-in-kinds` (name ≤ 80, description ≤ 500, unique name ignoring case) and `GET /api/admin/check-ins?days=` (never the message). User API: `kinds` on `GET /api/check-ins`; recent entries have `outcome`, `decided_at` and status `skipped`, and never the reason or message.

Caveats / follow-ups:
- Migration 0012 drops the stored `check_in_prompt` so the new one loads. Any Admin edit to it would have been lost; none existed here.
- A removed Kind leaves past Check-ins with no Kind; they show as "A check-in" to Users and "—" in the log.
- The fewer message says to turn Check-ins back on from the Dashboard; changing them by chat arrives in issue 17.
- Real Check-ins and the fewer message went to the owner's own Telegram; delivery was checked through the database and backend log, not by reading the chat.

Evidence: seam 1 `tests/test_admin_check_ins.py` (6), `tests/test_check_ins.py`; seam 2 `tests/test_check_in_sending.py` (21, incl. kind chosen from Summaries/Memory Items, skip recorded and rescheduled, threshold → fewer message and pause, reply resets, late message resets, memory off → only allowed Kinds, unusable answers retried, settings changed during the model call kept); seam 3 `web/src/components/CheckInsSettings.test.tsx`, `CheckInKindsManager.test.tsx` (7), `CheckInLog.test.tsx` (5), `PlatformSettingsForm.test.tsx`, `SidebarNav.test.tsx`, `web/src/lib/check-in-log.test.ts` (3), `check-ins.test.ts`.

## Completion

- Completed: 2026-11-12
- Commit: 6452635, review fixes 0b444b1, run fix ba394e6, archive 21c0474 (merged from `feat/12-smart-check-ins` in 2edb860)
