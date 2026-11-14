# 02 — Replies run in a core ReplyService; LangGraph removed

Status: completed

## Parent

`.scratch/understanding/PRD.md`

## What to build

Prefactor for Understanding (ADR-0009). Move the reply step (check → recall memory → recall Knowledge → compose → deliver) out of the LangGraph adapter into a core `ReplyService` in plain Python, with the same order and behaviour. Remove the conversation-engine port, the LangGraph adapter, the Postgres checkpointer and its tables, and the LangGraph/LangChain-graph dependencies no longer used. The ReplyGate keeps the house rules; on a confirmed Delete My Data nothing graph-related is left to delete.

Pure refactor: no change in what Users get, including failures raising as today.

## Acceptance criteria

- [x] `ReplyService` in core runs the reply steps; nothing in core imports LangGraph
- [x] The LangGraph adapter, the checkpointer and its tables are gone (migration drops them); unused dependencies removed
- [x] Existing end-to-end tests pass with no logic changes (only wiring or fixture changes, e.g. no checkpointer fixture)
- [x] `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [x] `/run` in a worktree: a normal, a crisis and an over-limit message each get the right reply

## Blocked by

None - can start immediately.

## Comments

- Branch `understanding-02-reply-service`, worktree `ai-chat-companion-understanding-02` (ports 3170/8170/5602).
- `ReplyService` (`src/companion/core/reply_service.py`) runs the same steps in the same order as the old LangGraph nodes and passes the same values. It catches nothing, so a failing step still raises to `IncomingMessageHandler`, which sends `reply_failed_message`. A stop from the ReplyGate (crisis, Delete My Data, over limit) just returns.
- Removed: the `ConversationEngine` port, `adapters/langgraph/`, `ConversationServices`, `build_conversation_engine` in `AppDependencies`, the `CONVERSATION_ENGINE_ADAPTER` setting (config, docker-compose, `.env.example`), every `forget_user` call (`UserDataService`, account-deletion retry, `MessageRetention`), and `list_users_with_messages_sent_before` (its only caller was the retention step that forgot checkpoints). An old `CONVERSATION_ENGINE_ADAPTER` line in a `.env` is harmless, as settings ignore unknown keys.
- Migration 0025 drops `checkpoint_writes`, `checkpoint_blobs`, `checkpoints`, `checkpoint_migrations` with `IF EXISTS` (LangGraph made them outside Alembic). Empty downgrade: the checkpointer made its own tables.
- Dependencies removed: `langgraph`, `langgraph-checkpoint-postgres`, `psycopg-pool` (only the checkpointer's pool used it). `uv.lock` changed.
- Tests: only fixture and wiring changes. The `checkpointer` fixture and the `has_checkpoints` assertions are gone, and so are `FakeConversationEngine` and `test_old_messages_stay_until_the_saved_state_can_be_deleted_too`, which only tested a failing checkpoint delete. No new `ReplyService` unit test: the existing chat tests drive it end to end, as the issue asks.
- Note for whoever merges next: `messages-01-group-texts` also has a migration 0025 (`0025_message_wait`). Whichever lands second must renumber to 0026.
- Code review (Standards and Spec in parallel):
  - Fixed: a stale `CONVERSATION_ENGINE_ADAPTER=langgraph` in `.env.example`; a stale "conversation engine's saved state" in the `message_retention_days` seed comment; `checked` renamed to `gate_result`.
  - Not changed: the old adapter turned an empty `safeguard_text` into `None`. That only undid its own `None → ""` for checkpoint storage, and `safeguard_text` is always built by `photo_message_text` with the photo descriptions, so it is never empty. `deliver_reply`'s 7 arguments are carried over unchanged.
- `/run` (worktree stack, after `make db-copy` from the main stack):
  - Migration on a copy of the real database: `alembic_version` went from 0024 to 0025, and the 4 checkpoint tables (1,484 checkpoints) were dropped. The backend started normally, and `import langgraph` in the backend image fails with `ModuleNotFoundError`.
  - Replies: the real app was built in the backend container through `build_production_app()` (real DeepSeek, Postgres, Safeguard, usage limits). Only the Telegram chat channel was swapped for a recording one, because Telegram refuses made-up chat IDs. Messages were posted to `/telegram/webhook` for the Admin with a test Telegram Connection:
    - Normal ("long day at work… making dinner") → 200, model reply in 2 parts: "Long day, and you still cook. That's better than I'd manage." / "What are you making?"
    - Crisis ("i want to end my life tonight") → 200, the helpline reply (SOS 1767, IMH 6389 2222, 995), and 1 Safeguard Event saved.
    - Over limit (`daily_message_limit` set to today's count of 29) → 200, the `daily_limit_reply` text "I'm honestly wiped for today…". The limit was then put back to 200.

## Completion

- Completed: 2026-11-14
- Evidence per criterion:
  - `ReplyService` in core, no LangGraph in core: `src/companion/core/reply_service.py`; `grep -rl langgraph src evals tests` finds no `.py` files; the core `ruff.toml` still bans `langgraph`.
  - Adapter, checkpointer and tables gone; dependencies removed: `src/companion/adapters/langgraph` no longer exists; migration `0025_drop_langgraph_checkpoints.py` dropped the 4 tables on a copy of the real database (see `/run`); `uv.lock` has 0 `langgraph` entries.
  - Existing end-to-end tests pass with only wiring and fixture changes: 734 passed (see Comments for what changed in tests).
  - `uv run ruff check .`: all checks passed. `uv run ruff format --check .`: 292 files already formatted. `uv run mypy`: no issues in 105 source files. `uv run pytest`: 734 passed, 9 deselected.
  - `/run` in a worktree: normal, crisis and over-limit messages each got the right reply (see Comments).
- Commits:
  - 10d39c9 "Understanding issue 02: replies run in a core ReplyService; LangGraph removed"
  - 412599b "Understanding issue 02: review fixes — drop stale engine references, clearer gate result name"
  - 304b03c "Understanding issue 02 done: archive issue with test, run and review evidence"
  - ca2eb6d "Merge understanding issue 02: replies run in a core ReplyService; LangGraph removed" (merged from `understanding-02-reply-service` into main)
