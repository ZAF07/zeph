# 02 — One Day Summary per day, carrying feeling as well as facts

Status: completed
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

- [x] Two Conversations on the same day leave exactly one Day Summary, rewritten from both Conversations' messages after the second ends
- [x] A Conversation starting at 23:50 and ending at 00:30 (User's time zone) lands in the earlier day
- [x] The memory processing call is given all of the day's messages, and its prompt asks for facts and feelings as above
- [x] Replies, look-ups by meaning, Check-ins and the Portrait read Day Summaries, each with its date
- [x] The Dashboard lists one Summary per day; deleting one removes it and rewrites the Portrait
- [x] The migration joins existing same-day Summaries into one per day
- [x] Delete My Data and Account Deletion remove Day Summaries
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

None - can start immediately

## Comments

### Run check, 19 Nov 2026 (worktree stack, copy of the main database)

- **Migration on real data:** main held 17 per-Conversation Summaries over 9 days (Asia/Singapore). After `make db-copy` and a restart, `alembic_version` = 0064, `conversation_summaries` is gone, and `day_summaries` has exactly 9 rows, one per day. 13 Nov, which had 3 Summaries, became one row with the mood arc "testing and playful, then neutral and task-focused, then excited but prickly and frustrated". `memory_processing_prompt` reloaded with the new seed text.
- **Two Conversations on one day / past midnight:** I inserted two ended, unprocessed Conversations for the owner. M started 23:50 SGT on 18 Nov with a text at 00:25 on 19 Nov. S started 21:00 SGT on 19 Nov. The running scheduler processed both with the real model.
  - Both Day Summaries kept their IDs (b508f50f… for 18 Nov, 02e61e01… for 19 Nov), and there are still 9 rows.
  - 18 Nov was rewritten from the whole of 18 Nov and now ends with the rent text ("asks to meet halfway at $100, a bit calmer").
  - 19 Nov was rewritten from the afternoon's real Conversation and S ("told their sister Lena about quitting… felt much lighter").
- **What the call was given** (Model Call Log, owner's own trace, full content):
  - M's call had "Earlier today, for the Day Summary only" holding 18 Nov's Conversations (5,784 chars, no 19 Nov text), with M under "The Conversation that just ended".
  - S's call had the afternoon PM Conversation as earlier (9,776 chars, no rent text) and S as just ended.
  - The Summaries carry facts and feelings, e.g. the 18 Nov mood: "weary and tender early, … briefly miffed when Zeph over-planned, then calm and settled after deciding how to negotiate the rent".
- **Reads with dates:** I ran the real `MemoryRetrieval` and the Check-in memory text in the backend container on the owner.
  - Reply: "Recent days, newest first: - 19 Nov 2026 … - 18 Nov 2026 … - 17 Nov 2026".
  - A look-up phrase found "Older days that may matter: - 15 Nov 2026 …", a day the migration joined from two Summaries, found through its averaged embedding.
  - The Check-in memory had the same three dated days.
  - The Portrait call at Conversation end had "Recent days, newest first:\n- 19 Nov 2026: …".
  - The full reply over Telegram wasn't driven: worktree fake chats stop at show_typing.
- **Dashboard** (plain User session, two Day Summaries seeded by SQL): the Summaries tab listed one card per day ("19 Nov", "18 Nov"). Clicking "Delete summary from 18 Nov" removed it (`DELETE /api/day-summaries/… 204`). The User's Portrait was rewritten within a minute (15:24:25) and no longer mentions the rent from the deleted day.
- **Delete My Data** (Account page, browser): `DELETE /api/me/data 204`; Day Summaries for the User went from 1 to 0, and the User was kept. **Account Deletion** (browser): a Day Summary was seeded, then "Permanently delete account" ran (`DELETE /api/me 204`); the User and their Day Summaries are both 0. The browser is back on /sign-in.
- **Checks:** `uv run pytest` 1343 passed; `ruff check`, `ruff format --check` and `mypy src` are clean; `pnpm lint`, `format:check` and `typecheck` are clean, and `pnpm test` gave 865 passed. Migration 0064 is the only migration on 0063 (main hasn't moved).
- **Docs:** README step a. has a "Built" note, the Status line and the prompts tables are updated, and the CONTEXT _Avoid_ line is fixed.

### Caveats / follow-ups for the owner

- The Dashboard Copy still calls the tab "Conversation Summaries", and its lead line says "After each Conversation". I left it so the pixel-tested design doesn't move. Worth a small Copy + design issue.
- A deleted Day Summary comes back if the User talks again that same day: the next Conversation end rewrites it from all of the day's messages, as the design says. If deleting should keep that day forgotten, it needs a decision.
- Code review: the Standards review found no rule breaks. I fixed its smells: clearer names, one helper for the day so far, and one calendar day format. I also fixed the Spec finding: a later or still-open Conversation is no longer passed in as "earlier today". DST at midnight in a few zones is not handled (low risk).

## Completion

- Completed: 2026-11-19
- Commit: <to be filled in after merge>
