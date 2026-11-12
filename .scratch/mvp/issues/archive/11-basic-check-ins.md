# 11 — Basic Check-ins

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

Users can opt in to Check-ins, and the Companion messages them first. Adds a Check-ins step to onboarding (off by default; frequency and quiet hours when on) and the same settings on the preferences page. On each scheduler tick, the Check-in service finds Users who are due (opted in, frequency elapsed, outside quiet hours in their time zone) and sends a casual-hello Check-in written by the LLM. A User replying to a Check-in starts a normal Conversation. Users can also pause Check-ins for a day, a week or until they resume, without losing their settings. The Check-ins page shows the settings, the pause control and a "Recent check-ins" list (sent, replied or no reply). It never shows a promised next time — the Companion decides when to reach out. Check-in Kinds are seeded from data files (casual hello, follow-up, present-moment prompt, thought to reflect on); this slice uses only casual hello.

## Design

- `docs/design/zeph-product.html`: Check-ins (settings, pause, Recent check-ins), Onboarding (Check-ins step)

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [x] Onboarding has a Check-ins step: off by default; frequency and quiet hours when turned on
- [x] The Check-ins page lets the User change frequency and quiet hours, or turn Check-ins off
- [x] Users can pause Check-ins for a day, a week or until they resume; no Check-in is sent while paused, and settings are kept
- [x] The Check-ins page lists recent Check-ins (sent, replied / no reply) and never shows a next Check-in time
- [x] A scheduler tick sends a casual-hello Check-in to Users who are due, and never during quiet hours in the User's time zone
- [x] Each sent Check-in is recorded and the next due time is set
- [x] A reply to a Check-in starts a Conversation that is handled like any other
- [x] Check-in Kinds are seeded from data files
- [x] Seam 2 tests with a fake clock cover: due → sent, quiet hours → not sent, time zone respected, Check-ins off → not sent, paused → not sent, pause ends → sent again, reply → Conversation
- [x] Seam 3 tests cover the onboarding step and preferences settings
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/03-onboarding.md`
- `.scratch/mvp/issues/06-user-memory.md`

## Comments

**2026-11-12 — started on branch `feat/11-basic-check-ins`.** Plan:
- User gets Check-in settings: on/off (off by default), frequency (once a week / a few times a week / most days), quiet hours (from, until; local time), paused (for a day, a week, or until resumed; a timed pause ends by itself) and next due time. Turning Check-ins on or changing the frequency sets the next due time to one frequency gap from now. Hours per frequency are a seeded setting.
- Onboarding takes the Check-in answers; `GET/PATCH /api/check-ins` reads and changes settings and lists recent Check-ins, `PUT/DELETE /api/check-ins/pause` pauses and resumes. The response never has a next due time.
- New `check_in_kinds` table seeded from `seed/check_in_kinds.yaml` (only when empty), and a `check_ins` table (User, Kind, message, sent at, replied at).
- Check-in service on each tick: Users with Check-ins on, a Telegram Connection, due, not paused, outside quiet hours in their time zone and with no open Conversation get a casual hello written by the LLM (Persona + Check-in prompt and model from settings). It is sent, recorded, and the next due time is set.
- A reply: the User's first message after a Check-in starts a new Conversation that begins with the Check-in text, so the reply has context; the Check-in is marked replied.
- Dashboard: Check-ins step in onboarding, a Check-ins page (switch, frequency, quiet hours, time zone, pause, Recent check-ins) and a sidebar link. Issue 12 parts (skips, Kinds list, ignore rule) and issue 17 parts ("changed in chat", "just tell Zeph") are left out.

**2026-11-12 — implemented, reviewed and verified.** Commits `439bdce`, review fixes `2990fc1`, run fixes `6e2149f` on `feat/11-basic-check-ins`.

Done and verified: every acceptance criterion. `make check` green (Python 254, web 202; ruff, ruff format, mypy, eslint, prettier, tsc clean). Migration 0011 ran on the existing database; 4 Check-in Kinds seeded; the existing owner account defaulted to Check-ins off. Docker run with real Postgres, Clerk (dev), DeepSeek and Telegram:
- Dashboard in Chrome (Playwright) as a temporary Clerk User: onboarding step 4 "Should I check in?" off by default with no frequency or quiet hours shown; turned on, "Most days", From 21:30, saved. Check-ins page showed them; "Once a week" and Until 08:15 saved and survived a reload; "For a week" → "Paused until Thursday, 19 November." with Resume now; "Until I resume" → "Paused until you resume."; resume; switch off → "Check-ins are off…"; on again; sidebar link current; no sideways scroll at 390px; no next time anywhere.
- Real tick: owner account made due. While their last Conversation was still open nothing was sent; on the tick that ended it, DeepSeek wrote and Telegram sent "Hey zaf, how's your Thursday going?" (casual hello), recorded, next due +24h.
- Reply: a webhook update as the owner's Telegram ("pretty good actually!…") started a new Conversation beginning with the Check-in, marked it replied, and got a normal reply that used User Memory.
- Recent check-ins on the real page: that Check-in "Replied", an older one "No reply", no message text.
- Found and fixed in /run: quiet hours fields stretched tall in onboarding, cramped time fields and time zone on the Check-ins page, label alignment, wrapped frequency picker shape.
- Clean-up: owner Check-ins back off, test Check-ins and the test Conversation deleted, the temporary User deleted from the database and Clerk.

Decisions:
- Frequencies are "once a week", "a few times a week" and "most days", at most every 168, 56 and 24 hours (`check_in_hours_between` setting). Turning Check-ins on or changing the frequency sets the next due time one gap from now; each sent Check-in sets it one gap after sending. Turning them off clears the pause and the due time. Pausing turns them on. A timed pause ends by itself, so a Check-in goes on the next tick after it ends if one is due.
- Defaults: off, a few times a week, quiet 22:00–07:30. The Dashboard reads them from the backend.
- A Check-in is held back (tried again each tick) while the User is paused, in Quiet Hours, has no Telegram Connection, or is mid-Conversation.
- The Check-in model gets the Persona plus `check_in_prompt`, the Kind, the User's name and local time (`check_in_model`). Both are on Prompts & models as "Check-ins". This slice sends the first Kind allowed without User Memory (casual hello).
- Reply: the User's first message within `check_in_reply_window_hours` (24) of their newest Check-in starts a Conversation that begins with the Check-in text, and the Check-in is "Replied". Statuses: Sent (newest, window still open), Replied, No reply. The API never returns the message or a next time.
- New `check_in_kinds` table seeded from `seed/check_in_kinds.yaml` on first run only; `check_ins` table (User, Kind, message, sent at, replied at).

Caveats / follow-ups:
- The casual hello is "the first Kind allowed without User Memory". Once Admins can reorder Kinds (issue 12) that could be the present-moment pause; issue 12 replaces this choice with the LLM's anyway.
- A Check-in is sent before it is saved. If saving fails right after a send, the next tick sends it again (rare; logged).
- Check-ins fire on the first tick after Quiet Hours end, so with long quiet hours they tend to land at the same morning time. Issue 12's choosing/skipping may want some variety.
- The real Check-in and reply went to the owner's own Telegram; delivery was checked through the database and backend log (no errors), not by reading the chat. The test turn stays in the owner's LangGraph checkpoint thread.

Evidence: seam 1 `tests/test_check_ins.py` (8); seam 2 `tests/test_check_in_sending.py` (13); seed `tests/test_check_in_kinds_seed.py` (2); seam 3 `web/src/components/CheckInsSettings.test.tsx` (10), `OnboardingFlow.test.tsx` (Check-ins step), `web/src/lib/check-ins.test.ts` (4).

## Completion

- Completed: 2026-11-12
- Commit: 439bdce, review fixes 2990fc1, run fixes 6e2149f, archive f622b6e (merged from `feat/11-basic-check-ins` in 7e67bfa)
