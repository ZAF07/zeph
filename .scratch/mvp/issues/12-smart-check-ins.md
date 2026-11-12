# 12 — Smart Check-ins

Status: ready-for-agent

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

- [ ] The Check-in service chooses a Check-in Kind using recent Conversation Summaries and Memory Items
- [ ] The service can decide to skip; the reason is recorded and the next attempt moves to the following slot
- [ ] After the configured number of consecutive ignored Check-ins, one "would you like fewer?" message is sent and Check-ins pause; a User reply resets the count
- [ ] With User Memory off, only Check-in Kinds allowed without User Memory are chosen
- [ ] The User's Check-ins page shows skips as "gave you some space", a read-only list of active Check-in Kinds, and a plain explanation of the ignore rule
- [ ] Admins can add, edit and remove Check-in Kinds and set the ignore threshold
- [ ] Admins can see Check-in sends and skips with reasons, never message text
- [ ] Seam 2 tests with a fake chat model and clock cover: kind chosen and sent, skip recorded and rescheduled, ignore threshold → pause message, User Memory off → casual hello only
- [ ] Seam 3 tests cover the admin Check-in pages and the User Check-ins page additions
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

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
