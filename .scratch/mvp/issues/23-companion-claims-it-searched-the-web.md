# 23 — The Companion can say it searched the web when it couldn't

Status: ready-for-agent

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

- [ ] Once the User's Web Search Limit is reached, the reply prompt carries `reply_web_search_limit_note` and no web tools
- [ ] With Web Search off for the User, the limit note is not added (the not-available note covers it)
- [ ] The note shows on the Response composition card on Prompts & models, and a saved change is used in the next reply
- [ ] Tests cover the above
- [ ] Checked in the running app: with the limit reached (shift usage, don't wait), asking "who won the match last night?" gets a reply that says it can't check and doesn't claim it searched
- [ ] `make check` passes (pytest, ruff, ruff format, mypy, plus the web checks)
