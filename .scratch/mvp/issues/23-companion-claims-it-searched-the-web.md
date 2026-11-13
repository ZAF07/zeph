# 23 — The Companion can say it searched the web when it couldn't

Status: needs-triage

## Parent

`.scratch/mvp/PRD.md` (found during the /run check in `issues/archive/09-web-search.md`)

## Before deciding on a solution

Run `/grill-with-docs` on this issue first. The user wants to grill the problem with the docs before a solution is picked, so don't start on the fix below until that is done.

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

## Suspected location

- `src/companion/core/web_search.py`: `WebSearchTools.offer` returns `WebSearchOffer(tools=[], instructions="")` when web search doesn't work for the User or the limit is reached.

## Possible fix (not decided)

Add a seeded setting, for example "You can't look things up on the web right now. Don't say you searched.", and put it in the reply prompt whenever the web tools aren't offered. Settle this in the grilling first.

## Acceptance criteria

- [ ] When web tools aren't offered (Feature off, or the limit reached), the Companion doesn't claim to have searched
- [ ] A test covers the fixed behaviour
- [ ] Checked in the running app with web search off
- [ ] `make check` passes (pytest, ruff, ruff format, mypy, plus the web checks)
