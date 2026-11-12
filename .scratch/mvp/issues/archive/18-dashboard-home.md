# 18 — Dashboard home

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

The page a User lands on after onboarding, built only from data that already exists. It follows the Dashboard home screen of the product design, minus anything tagged "Later".

- Telegram card: connected (handle, time of last Conversation) or not connected (a strong "Connect Telegram" card, since the Companion can't reach the User without it — ADR-0001).
- Check-ins card: on, paused until a date, or off, plus the last Check-in sent. Never a promised next time.
- "What you're working toward": the User's Memory Items in the Goals category, read-only, linking to the Memories page.
- "Recently remembered": the latest few Memory Items with category and date.
- The AI notice and a line that Zeph doesn't count streaks or time spent.

"A thought to sit with" is out of scope (Later).

## Design

- `docs/design/zeph-product.html`: Dashboard home

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [x] Home shows the Telegram card in both states, with the not-connected state leading to Connect Telegram
- [x] Home shows Check-in status (on / paused until / off) and the last Check-in sent, with no next time
- [x] Home shows Goals Memory Items and the most recent Memory Items, each linking to the Memories page
- [x] With User Memory off, the memory sections say so instead of showing empty lists
- [x] The AI notice is visible
- [x] Data comes from the backend through the API client; one home endpoint or existing endpoints, no business logic in the Dashboard
- [x] Seam 1 tests cover any new endpoint; seam 3 tests cover each card's states
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/06-user-memory.md`
- `.scratch/mvp/issues/11-basic-check-ins.md`

## Comments

**2026-11-12 — implemented, reviewed and verified** on branch `dashboard-home`.

Done and verified: every acceptance criterion. `make check` green (Python 342, web 263; ruff, ruff format, mypy, eslint, prettier, tsc clean).

Docker run with real Postgres and Clerk (dev), signed in as a temporary Clerk test User:
- New User: dark "Zeph can't reach you yet." card with Connect Telegram, no "Talk to Zeph" button, Check-ins "Off · Zeph only replies when you message" with no last Check-in, "Nothing here yet" under Goals, "No memories yet…" under Recently remembered.
- With a made-up Telegram Connection (`@maya_run`), a Conversation 40 minutes ago, six Memory Items, Check-ins on and two Check-ins (sent and replied 3 days ago, skipped 1 day ago), all seeded in the database: "Good evening, Maya.", "Talk to Zeph" → `https://t.me/<bot>`, "Connected as @maya_run", "Last Conversation today at 10:40 pm." (Singapore time), "On · A few times a week, at most", "Never between 10:00 pm and 7:30 am", "Last Check-in: a casual hello, Mon 9 Nov · you replied" (the skipped one is not shown as last). Goals showed the two Goals items newest first with "From a conversation · date"; Recently remembered showed the three newest with "Category · date". Footer showed the streaks line and the AI notice. "See in Memories" went to `/memories`. At 390px there was no sideways scroll.
- Paused for a week with User Memory off: "Paused · until Thursday, 19 November", last Check-in still shown, both memory sections showed the "Memory is paused…" note instead of lists. After the review fix, a pause marked as changed in chat showed "Changed in chat · 12 Nov" under it.
- The Check-ins page ("Paused until Thursday, 19 November.") and Memories page ("From a conversation · 13 Oct") still render after their helpers moved. No page errors anywhere.
- Clean-up: seeded rows and temporary Users deleted from the database and Clerk.

Decisions:
- One endpoint, `GET /api/home`, backed by core `HomeService` (`core/home.py`). It returns the Telegram Connection, the last Conversation's newest message time, the Check-in status (with `pause_changed_in_chat_at`) and the last Check-in sent, Goals and the 3 newest Memory Items (by `updated_at`, with category name), and the short AI notice (`ai_notice_short`). Never a next Check-in time.
- With User Memory off, the backend returns no Memory Items and the page shows a "Memory is paused" note in both sections.
- The Goals section reads the Memory Category named by a new platform setting `home_goals_memory_category` (default `Goals`). Renaming a category updates it, like the onboarding category settings.
- "Last Check-in sent" is the newest Check-in that wasn't skipped (an "asked if you'd like fewer" message counts), looking back over the newest 100 (`CheckInService.last_sent`).
- Greeting (morning / afternoon / evening) and date use the User's time zone. "Talk to Zeph" only shows when Telegram is connected.
- "Manage connection" goes to `/connect-telegram`, which shows the connected state; there is no Telegram section on Account and privacy yet.
- `TelegramStatusCard` was replaced by the home cards and deleted. `memorySourceLabel` moved to `lib/memories.ts`; `dateParts` moved to `lib/dates.ts`; `pauseEndText` and `formatTimeOfDay` were split out of the Check-in helpers.

Caveats / follow-ups:
- No "Support resources" link next to the AI notice: there's no User page for it yet.
- The `/connect-telegram` page heading still says "Connect Telegram" when you arrive there from "Manage connection".
- If the newest 100 Check-in decisions were all skipped, home says "No Check-ins sent yet." even if an older one was sent.
- "A thought to sit with" is not built (Later).

Evidence: seam 1 `tests/test_dashboard_home.py` (9: new User not connected and nothing remembered; Telegram Connection and last Conversation; Goals and newest Memory Items with category; User Memory off; Goals follow a renamed category; last Check-in sent, skipped ignored, no next time; paused until with no chat mark; paused in chat shows the mark; needs a signed-in User); seam 3 `web/src/components/DashboardHome.test.tsx` (10: greeting and connected Telegram; not connected leads to Connect Telegram; Check-ins on; paused with Changed in chat caption; off; Goals and recent items link to Memories; empty states; Memory paused note; AI notice and streaks line; Try again); `web/src/lib/home.test.ts` (6) and `web/src/lib/check-ins.test.ts` (2 new).

## Completion

- Completed: 2026-11-12
- Commit: 0f6b371, review fixes 2fcb896, archive c9f231e (merged from `dashboard-home` in 5aad78b)
