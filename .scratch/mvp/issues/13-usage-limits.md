# 13 — Usage limits

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

Keep costs in check. Each User has an Admin-set daily message limit (default generous, e.g. 200). Over the limit, the Companion replies in character ("I'm wiped for today, talk tomorrow?") instead of composing a reply. The Safeguard still runs first, so a crisis always gets the Crisis Reply. Token usage, message count and web search count are recorded per User per day and shown in the admin area.

## Design

- `docs/design/zeph-admin.html`: Usage, Platform settings (daily message limit)

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [ ] Over the daily message limit, the User gets the in-character limit reply (wording from settings) and no reply is composed
- [ ] The Safeguard runs before the limit check; a crisis over the limit still gets the Crisis Reply
- [ ] Tokens in/out, message count and web search count are recorded per User per day
- [ ] Admins can set the daily message limit and see usage per User per day
- [ ] Seam 1 tests cover: under limit → reply, over limit → limit reply, over limit + crisis → Crisis Reply, usage recorded
- [ ] Seam 3 tests cover the admin usage page
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/04-admin-area-foundation.md`
