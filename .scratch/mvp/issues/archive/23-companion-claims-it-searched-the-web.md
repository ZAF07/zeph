# 23 — The Companion can say it searched the web when it couldn't

Status: completed

## Parent

`.scratch/mvp/PRD.md` (found during the /run check in `issues/archive/09-web-search.md`)

## Symptom

Sometimes the Companion has no web tools for a reply:

- the Web Search Feature is off for the User (for everyone, or just for them), or
- the User has hit their Web Search Limit for the day.

In those cases the reply gets no web tools and no web instructions. Nothing tells the model it can't look things up.

- **Expected:** the Companion says plainly that it can't check, or answers from what it knows. It never claims to have searched.
- **Actual:** it once said it "tried" to search, even though no search was made. The User is told something untrue.

There is no crash and no error log.

## Repro

Not deterministic, because it depends on what the model says. It was seen once in the issue 09 /run check:

1. Turn web search off (now done through Features, for everyone or for one User).
2. Ask the Companion over Telegram something that needs current facts, e.g. "who won the match last night?".
3. The reply says it tried to search. No search was counted and no search reached Tavily.

The same is probably true once the daily limit is reached, but that hasn't been seen.

## What changed since this was filed

Features issue 03 added the not-available note (`reply_features_unavailable_note`, `FeatureService.unavailable_note`). When Admins turn Web Search off, the reply prompt now says it isn't available and not to pretend to do it. So the **Feature-off case is covered**. The **Web Search Limit case is not**: `WebSearchTools.offer` (`src/companion/core/web_search.py`) returns no tools and `instructions=""`, and nothing else tells the model.

## Decisions (grilling, 2026-11-13)

- **Scope: the Web Search Limit case only.** Leave the Feature-off note as is, unless the /run check shows the Companion still claims to search there.
- **Be open about it.** When a lookup would have helped, the Companion tells the User plainly it can't look things up again until tomorrow, answers from what it knows and says it may be out of date. It never says or suggests it searched. (Glossary: Web Search Limit, updated.)
- **One new seeded setting, `reply_web_search_limit_note`.** `offer` returns it as `instructions` (with no tools) when the limit is reached. When the Feature is off it still returns `""`, so the two notes never both show up. No hardcoded text (ADR 0004).
- **Admins can edit it:** add it to `EDITABLE_SETTINGS` and to the Response composition card's `extra_prompt_keys` in `src/companion/core/platform_settings.py`. Label: "Web Search Limit reached note". The Prompts & models page shows extra prompts generically, so no frontend change.
- Seed wording:

  > You've used all your web lookups for today, so you can't search or read pages again until tomorrow. If the person asks about something you'd need to look up, tell them plainly and kindly that you can't check right now, then answer from what you know and say it may be out of date. Never say or suggest that you searched or tried to.

- Making the other hidden reply notes editable is split out to `issues/29-admins-edit-reply-prompt-notes.md`.

## Acceptance criteria

- [x] Once the User's Web Search Limit is reached, the reply prompt carries `reply_web_search_limit_note` and no web tools
- [x] With Web Search off for the User, the limit note is not added (the not-available note covers it)
- [x] The note shows on the Response composition card on Prompts & models, and a saved change is used in the next reply
- [x] Tests cover the above
- [x] Checked in the running app: with the limit reached (shift usage, don't wait), asking "who won the match last night?" gets a reply that says it can't check and doesn't claim it searched
- [x] `make check` passes (pytest, ruff, ruff format, mypy, plus the web checks)

## Comments

### 2026-11-13 — implemented

- `WebSearchTools.offer` (`src/companion/core/web_search.py`) now checks the Feature first and returns `""` when Web Search is off. Once the Web Search Limit is reached it returns no tools and `reply_web_search_limit_note` as the instructions. New seeded setting in `src/companion/seed/platform_settings.yaml`, with the wording from Decisions. It is Admin-editable (`EDITABLE_SETTINGS`, label "Web Search Limit reached note", max 2,000 chars) and listed in the Response composition card's `extra_prompt_keys` (`src/companion/core/platform_settings.py`). Seeding uses `on_conflict_do_nothing`, so existing databases get the key on startup. No migration and no frontend change.
- Tests (`tests/test_web_search.py`): the daily-limit test checks the note shows at the limit and for the rest of that local day, that the normal web instructions are gone, and that the note is gone the next day. New tests: Web Search off with the limit reached gets the not-available note and not the limit note; an Admin-edited note is used in the next reply and is listed under Response composition; the seed wording says it can't check until tomorrow and never to claim a search.
- `make check`, after rebasing on origin/main: ruff, ruff format and mypy clean; pytest 488 passed; web lint, format, typecheck and vitest 299 passed.
- `/run` (worktree stack, real DeepSeek and Tavily). A test User with fake Telegram ids, web searches for today shifted to the limit (10). Telegram can't deliver to a fake chat, and the main DB's real Telegram ids weren't read, so the reply was driven through the real app (`build_production_app`, posted to `/telegram/webhook`) with only the chat channel swapped for one that records. Taps on the chat model and web search showed what each reply got.
  - At the limit, 4 asks ("who won the match last night?", Arsenal score, Singapore weather, election news): every reply prompt had the limit note, no web tools and no web instructions, and no search reached Tavily. Every reply said plainly it couldn't check (e.g. "I can't look it up right now either, I've used up my web checks for today… from memory, though it might be outdated"). None claimed to have searched.
  - Control, under the limit: the web tools and instructions were offered, one real search was made and counted, and the reply named its sources.
  - Web Search off and the limit reached, 2 asks: only the not-available note was in the prompt (never both). Both replies said they can't look things up and didn't claim a search. The Feature-off note needed no change.
  - Admin Prompts & models page (Playwright, signed-in Admin, 1280 px): the Response composition card shows "Web Search Limit reached note" with the seed text. An edit saved and stayed after reload, the next reply's prompt carried the edited text, and the original was put back through the page (the DB confirms no edit is left). No page errors. Cleaned up: the run's Clerk user was deleted and the Feature turned back on.
- Code review (`/code-review`, Standards and Spec in parallel): no hard rule breaks, nothing missing, no scope creep. Fixed: the Feature check now runs before the usage count and other setting reads; the Feature-off test checks for the not-available note's own text. Not changed: the test that checks seed wording (same as `tests/test_features.py`); the edited-note test also checks the card listing (one Admin flow); the two side-by-side `WebSearchOffer(tools=[], …)` returns.
- If the limit is reached partway through a reply, that reply's prompt is already built, so it doesn't get the note. The in-reply guard still refuses the search ("No more web searches today"), so that's fine.


## Completion

- Completed: 2026-11-13
- Commit: 0198efe "Tell the Companion it can't search once the Web Search Limit is reached", review fixes 2e7c207 "Check the Feature before counting web searches; name the not-available note in its test", archive 4c98e80 "MVP issue 23 done: archive issue with test, run and review evidence" (merged from `mvp-23-web-search-limit-note` in 0c55315 "Merge MVP issue 23: once a User reaches their Web Search Limit, the reply gets the new Admin-editable reply_web_search_limit_note…")
