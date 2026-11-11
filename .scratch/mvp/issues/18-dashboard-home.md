# 18 — Dashboard home

Status: ready-for-agent

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

- [ ] Home shows the Telegram card in both states, with the not-connected state leading to Connect Telegram
- [ ] Home shows Check-in status (on / paused until / off) and the last Check-in sent, with no next time
- [ ] Home shows Goals Memory Items and the most recent Memory Items, each linking to the Memories page
- [ ] With User Memory off, the memory sections say so instead of showing empty lists
- [ ] The AI notice is visible
- [ ] Data comes from the backend through the API client; one home endpoint or existing endpoints, no business logic in the Dashboard
- [ ] Seam 1 tests cover any new endpoint; seam 3 tests cover each card's states
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/06-user-memory.md`
- `.scratch/mvp/issues/11-basic-check-ins.md`
