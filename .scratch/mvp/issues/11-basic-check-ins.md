# 11 — Basic Check-ins

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

Users can opt in to Check-ins, and the Companion messages them first. Adds a Check-ins step to onboarding (off by default; frequency and quiet hours when on) and the same settings on the preferences page. On each scheduler tick, the Check-in service finds Users who are due (opted in, frequency elapsed, outside quiet hours in their time zone) and sends a casual-hello Check-in written by the LLM. A User replying to a Check-in starts a normal Conversation. Users can also pause Check-ins for a day, a week or until they resume, without losing their settings. The Check-ins page shows the settings, the pause control and a "Recent check-ins" list (sent, replied or no reply). It never shows a promised next time — the Companion decides when to reach out. Check-in Kinds are seeded from data files (casual hello, follow-up, present-moment prompt, thought to reflect on); this slice uses only casual hello.

## Design

- `docs/design/zeph-product.html`: Check-ins (settings, pause, Recent check-ins), Onboarding (Check-ins step)

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [ ] Onboarding has a Check-ins step: off by default; frequency and quiet hours when turned on
- [ ] The Check-ins page lets the User change frequency and quiet hours, or turn Check-ins off
- [ ] Users can pause Check-ins for a day, a week or until they resume; no Check-in is sent while paused, and settings are kept
- [ ] The Check-ins page lists recent Check-ins (sent, replied / no reply) and never shows a next Check-in time
- [ ] A scheduler tick sends a casual-hello Check-in to Users who are due, and never during quiet hours in the User's time zone
- [ ] Each sent Check-in is recorded and the next due time is set
- [ ] A reply to a Check-in starts a Conversation that is handled like any other
- [ ] Check-in Kinds are seeded from data files
- [ ] Seam 2 tests with a fake clock cover: due → sent, quiet hours → not sent, time zone respected, Check-ins off → not sent, paused → not sent, pause ends → sent again, reply → Conversation
- [ ] Seam 3 tests cover the onboarding step and preferences settings
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/03-onboarding.md`
- `.scratch/mvp/issues/06-user-memory.md`

## Comments

**2026-11-12 — started on branch `feat/11-basic-check-ins`.** Plan:
- User gets Check-in settings: on/off (off by default), frequency (once a week / a few times a week / most days), quiet hours (from, until; local time), paused (for a day, a week, or until resumed; a timed pause ends by itself) and next due time. Turning Check-ins on or changing the frequency sets the next due time to one frequency gap from now. Hours per frequency are a seeded setting.
- Onboarding takes the Check-in answers; `GET/PUT /api/check-ins` reads and changes settings (plus pause/resume) and lists recent Check-ins. The response never has a next due time.
- New `check_in_kinds` table seeded from `seed/check_in_kinds.yaml` (only when empty), and a `check_ins` table (User, Kind, message, sent at, replied at).
- Check-in service on each tick: Users with Check-ins on, a Telegram Connection, due, not paused, outside quiet hours in their time zone and with no open Conversation get a casual hello written by the LLM (Persona + Check-in prompt and model from settings). It is sent, recorded, and the next due time is set.
- A reply: the User's first message after a Check-in starts a new Conversation that begins with the Check-in text, so the reply has context; the Check-in is marked replied.
- Dashboard: Check-ins step in onboarding, a Check-ins page (switch, frequency, quiet hours, time zone, pause, Recent check-ins) and a sidebar link. Issue 12 parts (skips, Kinds list, ignore rule) and issue 17 parts ("changed in chat", "just tell Zeph") are left out.
