# 13 — Usage limits

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

Keep costs in check. Each User has an Admin-set daily message limit (default generous, e.g. 200). Over the limit, the Companion replies in character ("I'm wiped for today, talk tomorrow?") instead of composing a reply. The Safeguard still runs first, so a crisis always gets the Crisis Reply. Token usage, message count and web search count are recorded per User per day and shown in the admin area.

## Design

- `docs/design/zeph-admin.html`: Usage, Platform settings (daily message limit)

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [x] Over the daily message limit, the User gets the in-character limit reply (wording from settings) and no reply is composed
- [x] The Safeguard runs before the limit check; a crisis over the limit still gets the Crisis Reply
- [x] Tokens in/out, message count and web search count are recorded per User per day
- [x] Admins can set the daily message limit and see usage per User per day
- [x] Seam 1 tests cover: under limit → reply, over limit → limit reply, over limit + crisis → Crisis Reply, usage recorded
- [x] Seam 3 tests cover the admin usage page
- [x] `make check` passes
- [x] Verified in the running app via `/run`

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

**2026-11-12 — implemented and reviewed; `/run` half done.** Commits `407d410`, review fixes `f01c727`. `make check` green (Python 283, web 230).
- Review fixes: "Today" is each User's own day; "limit reached" is stored when a message or web search is actually turned away (not judged by today's limits on the Dashboard); one shared claim helper and one User's-day helper.
- `/run` so far (Docker, real Postgres, DeepSeek, Telegram, owner account): migration 0012 → 0013 ran and seeded both settings. Under the limit, 3 real replies; 3 messages recorded with 8,456 tokens in and 140 out. Limit set to 3: the next message got the limit reply with no reply composed (only Safeguard tokens added), count stayed 3, limit reached set. A crisis-worded message over the limit got the Crisis Reply with Singapore Helplines and a Safeguard Event. No backend errors. Clean-up: the run's Conversation (12 messages) and Safeguard Event deleted, limit back to 200; today's usage row kept.
- Still to check: the Admin Usage page and Platform settings in the browser. Making a temporary Clerk Admin was blocked by the permission check, so this waits on the owner.
- Filed separately: `.scratch/knowledge-editing/issues/05-flaky-knowledge-document-view-test.md` (seen once during `make check-web`).

**2026-11-12 — implemented, reviewed and verified.** Commits `407d410`, review fixes `f01c727` on `feat/13-usage-limits`.

Done and verified: every acceptance criterion. `make check` green (Python 283, web 230; ruff, ruff format, mypy, eslint, prettier, tsc clean). Docker run with real Postgres, Clerk (dev), DeepSeek and Telegram, on the owner account:
- Migration 0013 ran on the existing database (0012 → 0013), seeded `daily_message_limit` (200) and `daily_limit_reply`, and kept the day's existing web search count.
- Under the limit: 3 real DeepSeek replies; the row showed 3 messages, 8,456 tokens in, 140 out.
- Over the limit (set to 3): the limit reply was sent at once and nothing was composed. Only the Safeguard's tokens were added (+620 in, +1 out), the count stayed 3, and limit reached was set.
- A crisis-worded message over the limit got the Crisis Reply with Singapore Helplines and a Safeguard Event, and did not count toward the limit.
- No errors in the backend log.
- Dashboard in Chrome (Playwright) as a temporary Clerk Admin:
  - Usage: Today cards 9,747 / 148 / 3 / 4; the row shows "Message limit reached"; the caption shows the current limits; the footnote is present.
  - Last 7 days reloads with "· last 7 days" labels. Download CSV saved `usage-last-7-days.csv` with the right row.
  - At 390px there is no sideways page scroll; the table scrolls in its own box.
  - Usage is in the admin sidebar.
  - Platform settings: daily message limit 200 → 150 survives reload, then set back to 200. 0 is refused with the backend's message. The limit-reached reply shows under Wording.
- Clean-up: the run's Conversation (12 messages) and Safeguard Event deleted so they don't reach User Memory; limit back to 200; the temporary User deleted from the database and from Clerk. Today's real usage row kept.

Decisions:
- The day is the User's own day (their time zone, else UTC), for counting and for the report. "Today" on the Usage page is each User's own today.
- Only messages that reach the Companion count. Crisis messages never count ("Safety replies never count toward it"). Over-limit messages are not counted either, so Messages stops at the limit, as in the design. Admin stickers and caption-less voice notes or photos skip the reply flow and don't count.
- Reply flow: record → Safeguard → crisis gets the Crisis Reply; otherwise the message is counted in one step only if under the limit (like web searches); over the limit the Admin-set `daily_limit_reply` is sent at once and saved to the Conversation.
- Tokens are DeepSeek's own counts from each response (`usage_metadata`), added up across tool rounds. They are stored per User per day for every model call made for a User: Safeguard, memory retrieval, reply, post-conversation processing and Check-ins. The chat model port now returns `ModelAnswer` (text, tokens in, tokens out). A core `UsageRecordingChatModel` takes the User and records the tokens.
- "Message limit reached" / "Search limit reached" are stored when the limit actually turns something away, so they stay true for that day even if an Admin changes the limit later.
- `daily_message_limit` is 1–10,000 (0 would block everyone). The plan said 0–10000; 1 is on purpose.
- Admin API: `GET /api/admin/usage?days=` (1–365, default 7) returns rows (day, User, counts, tokens, limits reached) and the current limits. The Dashboard works out the totals for display and builds the CSV in the browser.

Caveats / follow-ups:
- Stored tokens won't exactly match DeepSeek's bill: a model call that fails is not counted, and cached input tokens (cheaper) aren't stored apart.
- A message counted toward the limit whose reply then fails still uses up one of the day's messages.
- Users over the limit still get Check-ins (the spec says nothing on this).
- Saving a setting as the temporary Admin then deleting them leaves "Using the starting values" on Platform settings (`updated_by` becomes empty).
- Seen during checks: a flaky Dashboard test, filed as `.scratch/knowledge-editing/issues/05-flaky-knowledge-document-view-test.md`.

Evidence: seam 1 `tests/test_usage_limits.py` (13: under limit → reply; over limit → limit reply, nothing composed; over limit + crisis → Crisis Reply; crisis not counted; resets on the User's next day; messages, tokens and web searches recorded; Check-in tokens recorded; period and limits; Admins only; settings ranges; each User's own day; limit reached only when something was turned away), `tests/adapters/test_deepseek_chat_model.py` (tokens added across tool rounds; none when missing); seam 3 `web/src/components/AdminUsage.test.tsx` (5), `web/src/lib/usage.test.ts` (4), `PlatformSettingsForm.test.tsx`, `SidebarNav.test.tsx`.

## Completion

- Completed: 2026-11-12
- Commit: 407d410, review fixes f01c727, archive be43fec (merged from `feat/13-usage-limits` in 3c8efd7)
