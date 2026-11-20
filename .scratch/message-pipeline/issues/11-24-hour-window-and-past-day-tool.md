# 11 — Every reply sees the last 24 hours, and can read a past day

Status: in-progress
Lane: A or B
Blocked by: 05

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

- **The 24-hour window:** the Understanding, the Reply Plan and the Reply see every message from the last 24 hours (Admin-set hours, with a hint) across Conversations, word for word, not only the current Conversation. On a very heavy day the oldest part is replaced by its Day Summary, past an Admin-set cap. A new Conversation within the window sees the previous one's messages, and its last Reply Plan's where-we-are line once 07 is in.
- **The past-day tool:** the Reply Plan has a tool to read a past day's messages (by date, the User's own, within Message Retention), for when a Day Summary isn't detailed enough. Beyond retention it says there are none, and Zeph answers from the Day Summary without claiming exact words.
- The Conversation and its quiet gap keep their meaning for Check-ins, per-Conversation limits and learning.

Can be picked up by either lane once 05 is in.

User stories covered: 33, 34, 35, 36, 58.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- The window hours and the heavy-day cap are ordinary field rows with hints, as in the "Field rows" sample in `AdminPersona`. No new parts.
- **Model call trace** (reference `AdminModelCallTrace`): the Reply Plan step lists `past_day` under "Tools called", and an Admin's own trace shows the call and its result ("14 messages from 12 Nov") in Content.
- **Shared reference.** `AdminModelCallTrace` also draws 05, 07, 09 and 14. Build your part. The full PASS is due on whichever of those issues lands last; until then, record under Comments which parts still differ and which issue owns them.

## Acceptance criteria

- [ ] A reply in a new Conversation 20 minutes after the last one is given the previous Conversation's messages
- [ ] A message at 00:10 sees messages from 23:50 the day before
- [ ] Messages older than the window aren't given; past the heavy-day cap, the oldest are replaced by the Day Summary
- [ ] The Reply Plan can call the past-day tool and gets that day's messages; for a day past retention it gets none
- [ ] The tool call shows in the Model Call Log like other tool calls
- [ ] The window hours and cap are Admin-editable with hints
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] The new field rows match the field-row sample in `AdminPersona`; the `past_day` call in the trace matches `AdminModelCallTrace` (full PASS if this is the last issue on it, otherwise the remaining differences are recorded under Comments)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Web checks pass, if web code changed: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 05 — The Reply Plan takes over deciding; the Understanding only reads (`.scratch/message-pipeline/issues/05-reply-plan-takes-over-deciding.md`)

## Comments

### Plan (20 Nov 2026, branch `mp-11-24h-window-past-day`)

- New `core/recent_messages.py` (named **Recent Messages**, since "reply window" already means a Check-in's reply window in `CONTEXT.md`): `RecentMessagesReader.read(snapshot, conversation_id)` loads every message the User and Zeph sent in the last `recent_messages_hours` (one query across Conversations, new repository method `list_user_messages_between`). Past `recent_messages_cap` messages, the oldest are left out and the Day Summaries of their days stand in.
- `ReplyService` reads them once and hands it to the Understanding, the Reply Plan and the Reply. Transcripts mark where a later Conversation started. The Reply Plan also sees the previous Conversation's last where-we-are line. Earlier Understandings and Reply Plans stay per Conversation.
- The Reply Plan is offered a `past_day` tool (`core/past_day.py`): a date → that day's messages (User's time zone), or none beyond Message Retention with a note to use the Day Summary and not claim exact words. The tool call lands in the Model Call Log as other tool calls do. Added after the live run: code hands what the tool read to the Reply at level 4.
- Two settings, seeded from YAML (no migration needed): `recent_messages_hours` (24) and `recent_messages_cap` (400), with hints, as field rows in the "Conversations" section of the Platform settings page.
