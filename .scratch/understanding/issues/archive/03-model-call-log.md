# 03 — Model Call Log

Status: completed

## Parent

`.scratch/understanding/PRD.md`

## What to build

Admins can see every model call the Companion makes, grouped into one trace per Message or Check-in (ADR-0010, `CONTEXT.md` "Model Call Log"). Record calls around the existing usage-recording chat model wrapper so every service (Safeguard, memory, reply, photos, Check-ins, Conversation-end work) is covered without each logging itself.

- **Every User, no content:** step, model, tokens, duration, errors, and the shape of the decision where one exists (e.g. which tools were called).
- **Full content only** when the User is an Admin, or the run is an Eval: instructions, history, tools offered, tool calls and results, the response, and the model's reasoning when it gives one. Content for other Users is never stored. Local and worktree runs also write full content to developer logs.
- Admin API and admin Dashboard page: list traces (filter by User, date, step, errors) and open one.
- Removed by Message Retention (with the messages), Delete My Data and Account Deletion.

## Acceptance criteria

- [x] A plain User's Message produces a trace with steps, models, tokens, timings and errors, and no content anywhere in storage or API
- [x] An Admin's own Message produces a trace with full content, including tool calls and results
- [x] Check-ins and Conversation-end work produce traces too
- [x] Admin page lists and opens traces, with filters; Vitest + RTL tests with the API client mocked
- [x] Message Retention, Delete My Data and Account Deletion remove the User's entries (covered by the per-User table deletion test)
- [x] `pytest`, `ruff`, `ruff format --check`, `mypy`, `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test` pass
- [x] `/run`: as an Admin, send a message in the worktree and open its trace on the Dashboard; a plain User's trace shows no content

## Blocked by

None - can start immediately.

## Comments

- Branch `understanding-03-model-call-log`, worktree `ai-chat-companion-understanding-03` (ports 3180/8180/5612).
- Plan: one `model_calls` table (migration 0026), one row per model call, grouped by a trace ID. Each `UserSnapshot` carries the trace (Message, Check-in or Conversation end), so no globals. `UsageRecordingChatModel` times each call, catches errors, records tool names and saves the entry; each call site names its step. Photos move onto the wrapper. Content is stored only for Admins and Eval runs (`AppDependencies.model_call_content_for_everyone`). `MODEL_CALL_DEVELOPER_LOGS=true` writes full content to developer logs.
- Rebased on main after Messages issue 01 (message grouping). A Message is several texts checked one by one, then one reply, so `PendingMessage` now holds the trace and every text check, photo and the reply use it: one trace per Message. Migration renumbered to 0027 (main took 0026).
- Decision shape is the tools called, as the issue's example says. Need picked, Threads found and so on come with the Understanding slices that make those decisions.
- Developer logs: `MODEL_CALL_DEVELOPER_LOGS=true` in a local or worktree `.env` (off in `.env.example`, off by default in code).
- Message Retention deletes entries by when each call started, like messages by when each was sent, so an old trace's later Conversation-end call can outlive its Message calls for a little while.

## Evidence

- **Plain User, no content:** `tests/test_model_call_log.py::test_a_plain_users_message_makes_a_trace_with_no_content` checks steps, model, tokens, time, `tools_called == ["web_search"]`, `content` null in the API, and no word of the message in any stored column. `/run`: the plain User's rows had `content` null, and no row of theirs held "lighthouse" or "secret" (`select count(*) ... = 0`).
- **Admin, full content:** `test_an_admins_own_message_keeps_full_content_with_tool_calls` (instructions, history, tools offered, the tool call's arguments and result, the response). Reasoning is covered by `tests/adapters/test_deepseek_chat_model.py::test_the_models_reasoning_is_kept_when_it_gives_one` and `test_an_eval_run_keeps_full_content_for_every_user`.
- **Check-ins and Conversation end:** `test_check_ins_and_conversation_end_make_their_own_traces`. **One trace per Message:** `test_texts_sent_in_a_row_make_one_trace_for_their_message`. **Errors:** `test_a_failing_model_call_shows_its_error`. **Photos:** `test_a_photo_is_part_of_its_messages_trace`.
- **Admin page:** `web/src/components/ModelCallLog.test.tsx` (list, links, all four filters, empty and error states) and `ModelCallTraceView.test.tsx` (no content for a plain User, full content with tool calls for an Admin, a gone trace), with the API client mocked. API filters: `test_traces_can_be_filtered_by_user_days_and_errors`; 404 and plain-User 403 tests.
- **Deletes:** `tests/test_data_deletion.py` finds every table with a `user_id` column and asserts each has rows before and none after, for Delete My Data and Account Deletion. `model_calls` is now one of them, and it passes. Retention: `test_message_retention_removes_old_entries`.
- **Checks (rebased code):** `pytest` 765 passed; `ruff check` all passed; `ruff format --check` 298 files already formatted; `mypy src` no issues; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean; `pnpm test` 50 files, 342 tests passed.
- **/run in the worktree** (ports 3180/8180): a Telegram send from a fake chat fails in a worktree, so the real app ran inside the backend container with the real database, DeepSeek and Tavily, and only the chat channel swapped for a recorder. The Admin asked for a lighthouse book and the reply called `web_search`. The plain User sent two texts in a row. Stored: Admin trace `safeguard, reply` with content; plain User trace `safeguard, safeguard, reply` with no content. As the signed-in Admin, `/admin/model-calls` listed both ("Safeguard ×2 → Reply", Content None and Full). The plain User's trace page said "No content kept for this User" on each call. The Admin's trace opened with the Reply's content: instructions, history, tools offered, and the `web_search` call `{"query": "best books about lighthouses"}` with its results. No page errors. The developer logs printed full content for both Users.
- **/code-review:** Standards found no hard violations. Fixed from it: duplicated record calls (one helper), a `ModelCallRequest` instead of nine loose arguments, a single answer-or-error outcome, `.env.example` developer logs off, the logger name, `to_model_call_response`, `formatTokens`. Kept as is: the `UsageRecordingChatModel` name, since it still records usage and a rename would touch every service; and loose filter arguments on the backend, which match the Safeguard Events endpoint. Spec: no scope creep. The rebase gap (one trace per Message) is fixed above.

## Completion

- Completed: 2026-11-14
- Commits: `ecd9452` (Model Call Log), `5811810` (review fixes: one trace per Message after rebase, single call outcome), `5f91e0c` (issue archived, CONTEXT.md)
- Merged into main: `32dfa91` (branch `understanding-03-model-call-log`, pushed to origin)
