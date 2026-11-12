# 09 — Web search

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

The Companion can search the web and fetch pages when the conversation needs it. Introduces the web search port (Tavily adapter). Search and page fetch are tools the model may call during response composition. The tool instructions forbid personal details in queries, and the Companion mentions sources when it uses web information. Admins can turn web search on or off and set a per-User daily web search limit.

## Acceptance criteria

- [x] Response composition can call web search and page fetch tools; results reach the reply
- [x] Tool instructions say queries must never contain the User's personal details
- [x] Replies that use web information mention where it came from
- [x] With web search off, the tools are not offered to the model
- [x] Once a User hits the daily web search limit, the tools are not offered for that User until the next day
- [x] Seam 1 tests with a fake web search adapter cover: tool call → result used, toggle off, daily limit reached
- [x] A separate contract test checks the Tavily adapter against the real API
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/04-admin-area-foundation.md`

## Comments

**2026-11-12 — started on branch `feat/09-web-search`.** Plan: `WebSearch` port (search, fetch page) with a Tavily adapter over httpx (`WEB_SEARCH_ADAPTER=tavily`); `ChatModel.generate` takes optional tools and the DeepSeek adapter runs the tool-call loop; core `WebSearchTools` offers `web_search` and `fetch_page` only when `web_search_enabled` is on and the User is under `web_search_daily_limit` for their local day; each tool call counts as one web search, claimed atomically in a new `daily_usage` table (issue 13 adds the other columns). Tool descriptions and reply instructions are seeded settings (ADR-0004). Platform settings page gets the Web search section from the design.

**2026-11-12 — implemented, reviewed and verified.** Commits `562151d`, `c33429a` on `feat/09-web-search`.

Done and verified: every acceptance criterion. `make check` green (Python 207, web 175; ruff, ruff format, mypy, eslint, prettier, tsc clean). `make contract` 6 passed, including real Tavily search + page read and DeepSeek calling an offered tool. Docker run with real DeepSeek and Tavily, messages posted to the webhook as the owner's connected Telegram account (Asia/Singapore):
- Asked for a book's year: a search was made and counted in `daily_usage` for 2026-11-12 (the User's local day), and the reply was correct (1975).
- Asked about mindfulness events in Singapore this month: 2 more searches, and the reply named its sources (joyfulgarden.sg, Brahm Centre, Art of Living, Kadampa centre).
- Limit set to 4 at count 4: no search, and the reply still went.
- Web search off with limit 10: no search, and the reply still went.
- Both settings were restored to their seeded values afterwards.
- `deepseek-reasoner` also handles the tools (checked directly against the API).

Decisions:
- Each `web_search` or `fetch_page` call counts as one web search, claimed in one step in the new `daily_usage` table (user, day, web_search_count). Issue 13 adds the other usage columns. The day is the User's own day (their time zone, UTC if none).
- A claim is made before the call, so a failed search still counts.
- Tool descriptions, reply instructions and a source reminder at the end of each tool result are seeded settings: `web_search_tool_description`, `page_fetch_tool_description`, `reply_web_search_instructions`, `web_result_source_reminder`. The reminder was added because the reply instructions alone didn't make DeepSeek name its sources.
- Admin-editable: `web_search_enabled` (new on/off setting kind) and `web_search_daily_limit` (0–1000, default 10), in a Web search section on Platform settings; the limit row shows only while web search is on.
- `ChatModel.generate` takes optional tools. The DeepSeek adapter runs the tool loop: at most 4 rounds, then it must answer without tools. Broken tool arguments are sent back so the model retries.
- `TAVILY_API_KEY` is now required; `WEB_SEARCH_ADAPTER=tavily`.

Caveats / follow-ups:
- With web search off, DeepSeek once claimed "I tried" to search. That is an honesty slip in the model's wording, not a real search. It may be worth a line in the response prompt.
- No signed-in browser check of the Platform settings Web search section; it is covered by seam 3 tests only.
- The queries actually sent to Tavily aren't logged (on purpose, for privacy), so the no-personal-details rule is checked through the tool description and the eval suite (issue 15), not by reading live queries.
- Tool-result messages for the model (limit reached, search failed, etc.) and the caps (6,000 page characters, 5 results, 4 tool rounds) are in code, not settings.
- If an Admin turns web search off in the middle of a reply, that reply can still finish its searches.

Evidence: seam 1 `tests/test_web_search.py` (9), `tests/test_admin_settings.py` (web search settings), `tests/test_config.py`; adapters `tests/adapters/test_deepseek_chat_model.py` (tool loop, 5), `tests/adapters/test_tavily_web_search.py` (3); contract `test_tavily_searches_the_web_and_reads_a_page`, `test_deepseek_calls_an_offered_tool_and_uses_its_result`; seam 3 `web/src/components/PlatformSettingsForm.test.tsx` (3 new).

## Completion

- Completed: 2026-11-12
- Commit: 562151d, review fixes c33429a (merged from `feat/09-web-search` in <merge commit>)
