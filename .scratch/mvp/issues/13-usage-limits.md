# 13 — Usage limits

Status: in-progress

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

## Comments

**2026-11-12 — started on branch `feat/13-usage-limits`.** Plan:
- `daily_usage` (today: web searches only) gains `message_count`, `tokens_in`, `tokens_out` (migration 0013). The day is the User's own day, as for the Web Search Limit.
- New settings `daily_message_limit` (default 200, 0–10000) and `daily_limit_reply` (in-character wording), both on Platform settings.
- Reply flow: record message → Safeguard → crisis gets the Crisis Reply (not counted, as the design says "Safety replies never count") → otherwise count the message in one step only if under the limit (like web searches) → over the limit: the limit reply is sent and saved, nothing is composed.
- Tokens: the chat model port returns the text with tokens in/out. A core `UsageRecordingChatModel` wraps it, takes the User and adds their tokens to today's row, so every model call for a User counts (Safeguard, memory retrieval, reply, post-conversation, Check-ins), as the design's footnote says.
- Admin API: `GET /api/admin/usage?days=1|7|30` → rows (day, User, messages, tokens in/out, web searches), totals for the period, and the current limits.
- Dashboard: Admin Usage page (period select, 4 totals, table with "Message limit reached" / "Search limit reached", Download CSV made in the browser), Usage in the admin sidebar, daily message limit and limit-reached reply on Platform settings.
