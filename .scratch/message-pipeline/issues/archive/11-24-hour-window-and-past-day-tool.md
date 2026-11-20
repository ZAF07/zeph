# 11 — Every reply sees the last 24 hours, and can read a past day

Status: completed
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

- [x] A reply in a new Conversation 20 minutes after the last one is given the previous Conversation's messages
- [x] A message at 00:10 sees messages from 23:50 the day before
- [x] Messages older than the window aren't given; past the heavy-day cap, the oldest are replaced by the Day Summary
- [x] The Reply Plan can call the past-day tool and gets that day's messages; for a day past retention it gets none
- [x] The tool call shows in the Model Call Log like other tool calls
- [x] The window hours and cap are Admin-editable with hints
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] The new field rows match the field-row sample in `AdminPersona`; the `past_day` call in the trace matches `AdminModelCallTrace` (full PASS if this is the last issue on it, otherwise the remaining differences are recorded under Comments)
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Web checks pass, if web code changed: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 05 — The Reply Plan takes over deciding; the Understanding only reads (`.scratch/message-pipeline/issues/05-reply-plan-takes-over-deciding.md`)

## Comments

### Plan (20 Nov 2026, branch `mp-11-24h-window-past-day`)

- New `core/recent_messages.py` (named **Recent Messages**, since "reply window" already means a Check-in's reply window in `CONTEXT.md`): `RecentMessagesReader.read(snapshot, conversation_id)` loads every message the User and Zeph sent in the last `recent_messages_hours` (one query across Conversations, new repository method `list_user_messages_between`). Past `recent_messages_cap` messages, the oldest are left out and the Day Summaries of their days stand in.
- `ReplyService` reads them once and hands it to the Understanding, the Reply Plan and the Reply. Transcripts mark where a later Conversation started. The Reply Plan also sees the previous Conversation's last where-we-are line. Earlier Understandings and Reply Plans stay per Conversation.
- The Reply Plan is offered a `past_day` tool (`core/past_day.py`): a date → that day's messages (User's time zone), or none beyond Message Retention with a note to use the Day Summary and not claim exact words. The tool call lands in the Model Call Log as other tool calls do. Added after the live run: code hands what the tool read to the Reply at level 4.
- Two settings, seeded from YAML (no migration needed): `recent_messages_hours` (24) and `recent_messages_cap` (400), with hints, as field rows in the "Conversations" section of the Platform settings page.

### Evidence (20 Nov 2026, after rebasing on `origin/main` 3ce16ff, which brought in issue 09)

Live runs used real DeepSeek and Postgres inside the worktree's backend container, with only the Telegram channel swapped for a recording one and the scheduler ticked by hand (fake chat IDs can't reach Telegram). Seeded User (Admin, Asia/Singapore) with past Conversations 5 days, 40 days, 25 hours and 23 hours earlier. Times were moved back in the database instead of waiting.

- **New Conversation 20 minutes later sees the previous one:** `test_a_new_conversation_20_minutes_later_sees_the_previous_ones_messages`. Live: the open Conversation's times were moved back 20 minutes and a tick ended and processed it. "back. sorry, where were we?" then had the previous Conversation's messages in the Understanding, Reply Plan and Reply (True for all three), a "--- New Conversation" line in the first two, and "Where the previous Conversation was when it ended: …" in the Reply Plan. Zeph answered "We were on the savings half — did the cost list happen at all…", picking up where it stopped.
- **00:10 sees 23:50 the day before:** `test_a_message_at_00_10_sees_the_messages_from_23_50_the_day_before` (Singapore time). Live: a text from 23 hours earlier, on 19 Nov local, reached all three steps on 20 Nov (True ×3).
- **Older than the window not given; past the cap the Day Summary stands in:** `test_messages_older_than_the_admin_set_window_are_not_given`, `test_past_the_cap_the_oldest_messages_are_replaced_by_their_day_summary`. Live: the 25-hour-old text ("Pickle") reached none of the three steps (False ×3). With `recent_messages_cap` set to 4, yesterday's text was left out (False ×3) and that day's Day Summary stood in (True ×3). The cap was put back to 400.
- **Past-day tool within and past retention:** `test_the_reply_plan_reads_a_past_days_messages_with_the_past_day_tool`, `test_the_past_day_tool_gives_no_messages_for_a_day_past_retention`, `test_what_the_past_day_tool_read_reaches_the_reply_at_level_four`. Live:
  - "remind me exactly what I told you on 2026-11-15 about Sam's dinner…" → the Reply Plan called `past_day {"date": "2026-11-15"}` → "4 messages from 15 Nov:" and the transcript. Zeph: "You booked Luigi's for 8pm on Saturday, and you'd checked the menu because Sam's allergic to shellfish."
  - "what were my exact words on 2026-10-11?" → "No messages from 11 Oct: messages are only kept for 30 days. Answer from that day's Day Summary…". Zeph: "messages are only kept for thirty days… I'd rather say that than paraphrase and pass it off as your words."
  - A first live run found the Reply denying it had the day ("I don't have anything from the 15th"), because the Reply Plan's guidance didn't carry the details. Code now hands what the tool read to the Reply at level 4 (test added). Re-run on a clean User: correct.
- **Tool call in the Model Call Log:** `test_the_past_day_tool_call_shows_in_the_model_call_log`. In the browser as an Admin, the trace's Reply Plan step shows "Tools called: past_day", and its Content shows TOOL CALLS past_day `{"date": "2026-11-15"}` with "4 messages from 15 Nov:" and the messages.
- **Admin-editable with hints:** `test_the_window_settings_are_admin_editable_with_hints` and the `PlatformSettingsForm` test. In the browser: "Recent messages" (24 hours) and "Recent messages cap" (400 msgs) show in the Conversations section of Platform settings with their hints. A change to 12 saved and was still there after a reload, then was set back to 24. Screenshots at 1280 and 390 match the other field rows.
- **One migration head:** this issue adds no migration. The new settings are seeded from `platform_settings.yaml`. After the rebase the head is 0071 (issue 09), and the stack's `alembic_version` reads 0071.
- **Docs:** `CONTEXT.md` has a new **Recent Messages** term (Avoid: reply window, which already names a Check-in's). Conversation and Reply Plan are updated. `docs/message-pipeline/README.md` gets Built notes for the Recent Messages and the past-day tool, "Not yet" no longer lists 11, and the Today table is updated.
- **Design:** the field rows use the existing `FieldRow`/`FieldNumber` like their neighbours (no new parts). `node design/compare.cjs AdminModelCallTrace`: `FAIL 0.13%` (0.64% before 09 landed). "Tools called: past_day" lines up. Still different: the "Pattern" fact (issue 14), which moves the Check-in facts. Owned by no issue: the "Sample data" pill and the year in "Started 19 Nov 2026". This issue is not the last on the reference, so no full PASS is due. `AdminPersona` stays at 0.71%, the same parts recorded in 06 and 07.
- **Checks** (after the rebase): `uv run pytest` 1442 passed; `ruff check` "All checks passed!"; `ruff format --check` "550 files already formatted"; `mypy src` "Success: no issues found in 202 source files". `pnpm lint` and `pnpm typecheck` clean; `pnpm format:check` "All matched files use Prettier code style!"; `pnpm test` 887 passed in 131 files.
- **`/code-review`:** Standards found no hard breaches. Fixed: the duplicated new-Conversation check (one helper now), vague names (`parse_day_argument`, `day_transcript`, `how_many`, the `_NOTE` texts), a string cut that dropped the year, the inline memory join, and the `true()` filter trick. Spec: fixed texts left unanswered at the end of an earlier Conversation being merged into the latest Message, and in the Reply's chat turns (test added). The tool now says when retention may have taken the start of the boundary day.
- **Caveats, kept on purpose:**
  - The past-day tool reads by each message's own day, not by the day its Conversation started (as Day Summaries do). This matches "what did I say on 12 Nov?".
  - If the cap cuts into today's still-open Conversation, no Day Summary exists yet to stand in.
  - What the tool reads is not capped before it goes to the Reply. A very busy day costs more tokens on that one reply.
  - The concept was renamed **Recent Messages** (`recent_messages_hours`, `recent_messages_cap`) from the issue's "24-hour window", to avoid the existing "reply window".
  - No Eval was run (Evals cost money).

## Completion

- Completed: 2026-11-20
- Commit: <filled in after merge>
