# 03 — Model Call Log

Status: in-progress

## Parent

`.scratch/understanding/PRD.md`

## What to build

Admins can see every model call the Companion makes, grouped into one trace per Message or Check-in (ADR-0010, `CONTEXT.md` "Model Call Log"). Record calls around the existing usage-recording chat model wrapper so every service (Safeguard, memory, reply, photos, Check-ins, Conversation-end work) is covered without each logging itself.

- **Every User, no content:** step, model, tokens, duration, errors, and the shape of the decision where one exists (e.g. which tools were called).
- **Full content only** when the User is an Admin, or the run is an Eval: instructions, history, tools offered, tool calls and results, the response, and the model's reasoning when it gives one. Content for other Users is never stored. Local and worktree runs also write full content to developer logs.
- Admin API and admin Dashboard page: list traces (filter by User, date, step, errors) and open one.
- Removed by Message Retention (with the messages), Delete My Data and Account Deletion.

## Acceptance criteria

- [ ] A plain User's Message produces a trace with steps, models, tokens, timings and errors, and no content anywhere in storage or API
- [ ] An Admin's own Message produces a trace with full content, including tool calls and results
- [ ] Check-ins and Conversation-end work produce traces too
- [ ] Admin page lists and opens traces, with filters; Vitest + RTL tests with the API client mocked
- [ ] Message Retention, Delete My Data and Account Deletion remove the User's entries (covered by the per-User table deletion test)
- [ ] `pytest`, `ruff`, `ruff format --check`, `mypy`, `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test` pass
- [ ] `/run`: as an Admin, send a message in the worktree and open its trace on the Dashboard; a plain User's trace shows no content

## Blocked by

None - can start immediately.

## Comments

- Branch `understanding-03-model-call-log`, worktree `ai-chat-companion-understanding-03` (ports 3180/8180/5612).
- Plan: one `model_calls` table (migration 0026), one row per model call, grouped by a trace ID. Each `UserSnapshot` carries the trace (Message, Check-in or Conversation end), so no globals. `UsageRecordingChatModel` times each call, catches errors, records tool names and saves the entry; each call site names its step. Photos move onto the wrapper. Content is stored only for Admins and Eval runs (`AppDependencies.model_call_content_for_everyone`). `MODEL_CALL_DEVELOPER_LOGS=true` writes full content to developer logs.
