# 02 — One Day Summary per day, carrying feeling as well as facts

Status: ready-for-agent
Lane: B
Blocked by: None - can start immediately

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

Conversation Summaries become **Day Summaries**: one per User per day, in the User's time zone. Each time a Conversation ends, the day's Summary is rewritten from all of that day's messages, never from the old Summary. A Conversation that runs past midnight belongs to the day it started.

The memory processing prompt asks for the facts (who, what, numbers, decisions, what Zeph advised and how the User answered) and the feeling (how they felt and why, what it meant to them, how their mood moved and what moved it), so a look back months later still makes sense.

Everything that used Conversation Summaries uses Day Summaries: the newest few go into every reply; older ones are found by meaning, each with its date; Check-ins and the Portrait read them as before. The Dashboard's past-Conversations list shows one entry per day, deletable; deleting one rewrites the Portrait as today. Delete My Data and Account Deletion remove them. Existing Summaries from the same day are joined into one by migration, with no model rewrite (the platform isn't live).

Glossary term: **Day Summary** (already in `CONTEXT.md`).

User stories covered: 45, 46, 47, 48, 49, 50.

## Acceptance criteria

- [ ] Two Conversations on the same day leave exactly one Day Summary, rewritten from both Conversations' messages after the second ends
- [ ] A Conversation starting at 23:50 and ending at 00:30 (User's time zone) lands in the earlier day
- [ ] The memory processing call is given all of the day's messages, and its prompt asks for facts and feelings as above
- [ ] Replies, look-ups by meaning, Check-ins and the Portrait read Day Summaries, each with its date
- [ ] The Dashboard lists one Summary per day; deleting one removes it and rewrites the Portrait
- [ ] The migration joins existing same-day Summaries into one per day
- [ ] Delete My Data and Account Deletion remove Day Summaries
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

None - can start immediately

## Comments
