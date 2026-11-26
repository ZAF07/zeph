# Code map: how the code is put together

Where things live, how they connect, and how to add to them. For what Zeph does, see `ABOUT.md` and `CONTEXT.md`. For the reply path in detail, see `docs/message-pipeline/README.md`.

## The rule

- **Core** (`src/companion/core/`) holds all business logic. It talks to the outside world only through **ports** (interfaces in `core/ports.py`).
- **Adapters** (`src/companion/adapters/`) implement the ports: Postgres, Telegram, the model, Clerk, and so on.
- Core never imports an adapter or its library. `core/ruff.toml` bans them, so `ruff` fails if you try (ADR 0003).

## Folder map

| Path | What it is |
|---|---|
| `src/companion/main.py` | Builds the real app. Picks each adapter from `.env` (`build_chat_model`, `build_chat_channel`, …) and calls `create_app`. uvicorn runs `build_production_app`. |
| `src/companion/app.py` | The composition root. `AppDependencies` lists every outside thing; `create_app` builds every core service and route from it. |
| `src/companion/config.py` | `Settings`: secrets, adapter choices and addresses, read from `.env`. |
| `src/companion/prestart.py` | Runs before the backend starts: migrates the database, loads seed data, registers the Telegram webhook. |
| `src/companion/eval_runner.py` | The Eval service: works queued Eval Runs one at a time. |
| `src/companion/eval_terminal.py` | `make eval`: queues an Eval Run and prints it. |
| `src/companion/pattern_matching_terminal.py` | `make match-patterns`: matches Patterns with no Pattern Type to the catalog. |
| `src/companion/seed/` | Seed data in YAML: Platform Settings, Copy, Helplines, Memory Categories, Check-in Kinds, Needs, Moves, Thought Experiments, the Pattern Catalog, Knowledge, Eval Cases. |
| `src/companion/core/` | Business logic, flat (see the table below). |
| `src/companion/core/evals/` | The Evals: cases, runs, the Judge, one file per Eval, and their own ports (`core/evals/ports.py`). |
| `src/companion/adapters/` | One folder per outside thing (see below). |
| `tests/` | `pytest`. Most tests drive the real app (`create_app`) on a real Postgres, with fakes from `tests/fakes.py` for the rest. `tests/adapters/` tests adapters; `tests/contract/` calls real services and is skipped unless you run `make contract`. |
| `evals/README.md` | What each Eval checks. Evals cost money and never run in `make check`. |
| `scripts/` | `worktree_setup.py`, `seed_prompt_hash.py`, `backup.sh`, `load_test/` (`make load-test`). |
| `web/` | The Dashboard (Next.js). See the last section. |

### Adapters

| Folder or file | Wraps | Implements |
|---|---|---|
| `postgres/` | Postgres (SQLAlchemy). Tables in `tables.py`, repositories in `repositories.py`, migrations in `migrations/` | `Repositories`, `Transaction`, the Eval repositories |
| `pgvector/` | pgvector search | `KnowledgeVectorStore` |
| `telegram/` | Telegram. `webhook.py` is the route Telegram posts to; `chat_channel.py` sends | `ChatChannel` |
| `openrouter/` | OpenRouter (the main model provider) | `ChatModel`, `PhotoViewer` |
| `deepseek/` | DeepSeek direct, the backup (ADR 0028) | `ChatModel`, `PhotoViewer` |
| `chat_tools.py` | The tool loop shared by both model adapters | — |
| `clerk/` | Clerk | `AuthVerifier`, `AuthAccounts` |
| `fastembed/` | A local embedding model | `Embedder` |
| `pypdf/` | Reading text out of uploaded PDFs | `DocumentTextExtractor` |
| `tavily/` | Tavily web search | `WebSearch` |
| `http/` | FastAPI routes for the Dashboard and Admin pages | — (drives core) |
| `clock.py`, `scheduler.py`, `timer.py`, `user_work_queue.py` | The system clock, the in-process scheduler loop, waits, per-User work threads | `Clock`, `Scheduler`, `Timer`, `UserWorkQueue` |
| `*_seed.py` | Reading seed files (Pattern Catalog, Knowledge, Eval Cases) | — |
| `load_test/` | Free stand-ins for `make load-test` | several |
| `evals/` | Running the app in-process for Evals, with stand-ins | — |

`langgraph/` holds nothing in git; replies no longer use LangGraph (ADR 0009).

## Core files by area

| Area | Files | What they do |
|---|---|---|
| Reply path | `incoming_messages.py`, `message_wait.py`, `typing_keeper.py`, `reply_gate.py`, `reply_attempt.py`, `reply_service.py`, `recent_messages.py`, `understanding.py`, `memory_retrieval.py`, `knowledge_retrieval.py`, `reply_plan.py`, `past_day.py`, `response_composition.py`, `reply_tools.py`, `conversations.py`, `transcripts.py` | A text arrives, is checked, Zeph waits for the User to pause, then Understanding → Recall → Reply Plan → Reply, and the reply is sent. |
| Reply tools | `chat_settings.py`, `web_search.py`, `stickers.py`, `sticker_adding.py`, `personal_stickers.py`, `photos.py` | Tools a reply may call: change settings in chat, search the web, send stickers and photos. Also the Sticker Library and Personal Stickers. |
| Conversation end and scheduled work | `scheduled_work.py`, `post_conversation.py`, `familiarity.py`, `user_portrait.py`, `move_outcomes.py`, `message_retention.py` | Each scheduler tick ends quiet Conversations and runs their end steps (Day Summary, User Memory, Life Threads, Patterns, Curiosities, Move Outcomes, Familiarity, the User Portrait, …), sends due Check-ins and deletes old messages. |
| User Memory | `user_memory.py`, `life_threads.py`, `memory_categories.py`, `user_data.py` | Memory Items, Day Summaries, Life Threads and Memory Categories; what the User sees and deletes; Delete My Data and Account Deletion. |
| Patterns | `patterns.py`, `observations.py`, `pattern_scoring.py`, `pattern_catalog.py`, `pattern_matching.py`, `unmatched_review.py`, `ready_gate.py`, `pattern_sharing.py`, `predictions.py`, `told_patterns.py`, `agenda.py` | The pattern pipeline: tagging Observations, scoring, the catalog, the gate before sharing, sharing, Predictions, the Agenda. See `docs/pattern-pipeline/`. |
| Curiosities and Thought Experiments | `curiosities.py`, `curiosity_pace.py`, `thought_experiments.py`, `starter_thought_experiments.py` | What Zeph wants to ask, how often, and the Thought Experiments it puts to Users. |
| Check-ins | `check_ins.py`, `check_in_decision.py`, `check_in_kinds.py`, `check_in_schedule.py`, `woven_check_ins.py` | Check-in settings, deciding and sending due Check-ins, Check-in Kinds, the Admin schedule, Woven-in Check-ins. |
| Safety | `safeguard.py`, `helplines.py` | The Safeguard checks every text for crisis and sends the Crisis Reply; Helplines per country. |
| Dashboard and Admin services | `users.py`, `me.py`, `home.py`, `admin_users.py`, `copy.py`, `needs.py`, `moves.py`, `telegram_connection.py`, `knowledge.py` | What the Dashboard pages read and change: the User's profile, Home, Admins, Copy, Needs, Moves, Telegram Connection, Knowledge. |
| Platform and settings | `platform_settings.py`, `features.py`, `settings_changes.py`, `model_call_log.py`, `usage.py`, `user_snapshot.py`, `timing.py` | Platform Settings, Feature switches, who changed a setting, the Model Call Log, Usage and the Daily Message Limit, User snapshots, a User's local time and day. |
| Building blocks | `ports.py`, `models.py`, `errors.py` | Ports, domain types, error kinds (see below). |

## Key building blocks

**`core/ports.py`.** Ports are `Protocol` classes. Three kinds:

- Outside services: `ChatModel`, `PhotoViewer`, `ChatChannel`, `WebSearch`, `Embedder`, `KnowledgeVectorStore`, `DocumentTextExtractor`, `AuthVerifier`, `AuthAccounts`.
- Running things over time: `Clock`, `Scheduler`, `Timer`, `UserWorkQueue`.
- Storage: one repository per area (`UserRepository`, `ConversationRepository`, `PatternRepository`, …).

**`Repositories` and `Transaction`** (end of `core/ports.py`, ADR 0008). `Repositories` is a frozen dataclass holding every repository. To change several in one go:

```python
with self._repositories.transaction() as transaction:
    transaction.lock_user(user.id)
    transaction.repositories.patterns...
```

- All of it is saved, or none.
- A transaction started inside another joins the outer one.
- `lock_user` locks one User's row until the end, so two jobs on the same User wait for each other (scoring and deleting Observations use it). `lock_admins` does the same for Admins (the last-Admin rule in `admin_users.py`).
- Postgres side: `PostgresTransaction` in `adapters/postgres/repositories.py`.
- Every repository with per-User rows has `delete_for_user`. `delete_user_data` in `core/user_data.py` calls them in one transaction. Usage, Safeguard Events and Feature switches go only when the whole account is deleted.

**`UserSnapshot`** (`core/models.py`). The User, their local time and day, each Feature's status, the Platform Settings, and the Model Call Log trace, read once when a reply or tick starts. Every step gets it, so none reads them again, and a change halfway through doesn't change the rest. `UserSnapshotLoader` (`core/user_snapshot.py`) reads many at once in a few queries.

**`core/models.py`.** The domain types: frozen dataclasses and enums (`User`, `Conversation`, `IncomingMessage`, `Pattern`, …). No database code.

**`core/errors.py`** (ADR 0011). Every error core raises for a refused request inherits one kind:

| Kind | HTTP |
|---|---|
| `NotFoundError` | 404 |
| `NotAllowedError` | 403 |
| `InvalidError` | 422 |
| `ConflictError` | 409 |
| `OutsideServiceError` | 502 |

`adapters/http/errors.py` maps each kind once (`add_core_error_handlers`). Routes never catch core errors. The text a person sees lives on the error (`shown_message`, or else the text it was raised with).

**The composition root.** `create_app` in `app.py` builds each service once and hands it what it needs. It also wraps the raw adapters: the model in `UsageRecordingChatModel` (records Usage and the Model Call Log) and the chat channel in `TypingKeeper`. `main.py` only picks adapters. Tests call `create_app` with fakes.

**The HTTP layer** (`adapters/http/`). Each route file has a `build_..._api_router(...)` that takes core services and returns a FastAPI router. Routes sit under `/api`. Admin routes sit under `/api/admin` and need `current_admin`; User routes are mostly in `dashboard_api.py`. `auth.py` turns the bearer token into a `User` (`AuthVerifier.verify`, then `UserService.get_or_create`). A route calls one core service and turns the result into a response model.

## How a Telegram message flows

1. Telegram posts to `/telegram/webhook` (`adapters/telegram/webhook.py`). It checks the secret, turns the update into an `IncomingMessage` (`parse_update`) and calls `IncomingMessageHandler.handle`. It returns at once.
2. `handle` (`core/incoming_messages.py`) finds the Telegram Connection and adds the work to the User's line on the `UserWorkQueue`.
3. Each text is saved and checked for crisis (`ReplyGate.screen`, which calls the `Safeguard`). Then the `Timer` waits for the User to pause (`message_wait`).
4. When the wait ends, a `UserSnapshot` is read and `ReplyService.handle` runs (`core/reply_service.py`).
5. `ReplyGate.check` applies the house rules (Delete My Data, the Daily Message Limit). Then the steps run in order: Recent Messages, Understanding, Life Threads, Patterns, Curiosities, Move Outcomes, Reply Plan, Recall (memory and Knowledge), Reply (`ResponseComposer.compose`).
6. Each model call goes through the `ChatModel` port (OpenRouter adapter). Each read and write goes through `Repositories` (Postgres adapter).
7. `ConversationService.deliver_reply` sends the reply through the `ChatChannel` port (Telegram adapter).
8. Later, a scheduler tick (`ScheduledWork.tick`) ends the quiet Conversation and runs `PostConversationProcessor.process`.

## How a Dashboard call flows

Example: the Home page.

1. `web/src/components/DashboardHome.tsx` calls `apiClient.getHome()` through React Query.
2. `getHome` in `web/src/lib/api-client.ts` sends `GET /api/home` with the Clerk session token.
3. `get_home` in `adapters/http/dashboard_api.py` gets the `User` from `current_user` and calls `HomeService.get`.
4. `HomeService` (`core/home.py`) reads what it needs through `Repositories` and other services.
5. The Postgres repositories run the queries. The route turns the result into `HomeResponse`.

## How to add things

**A new port and adapter**

1. Add a `Protocol` to `core/ports.py`.
2. Write the adapter in a new folder under `adapters/`. Don't import it from core.
3. Add a `build_...` function in `main.py` that picks it by a `..._ADAPTER` setting in `config.py`, and a field on `AppDependencies`.
4. Pass it in `create_app` to the services that need it.
5. Add a fake to `tests/fakes.py` and a fixture in `tests/conftest.py`; test the adapter in `tests/adapters/`.

Example to copy: `WebSearch` → `TavilyWebSearch` → `build_web_search` → `FakeWebSearch`.

**A core service the Dashboard uses**

1. Write the service class in `core/`. Take repositories and ports in `__init__`. Raise errors from `core/errors.py` kinds.
2. Build it in `create_app` and pass it to the router builder.
3. Add the route to `adapters/http/dashboard_api.py` (or `admin_api.py` for Admins). Call the service; don't catch its errors.
4. Add the type and the function to `ApiClient` in `web/src/lib/api-client.ts`. Pages call it through `useApiClient()`, never `fetch`.
5. In design-fixture mode a call with no fixture fails, so add one in `web/src/lib/design-fixtures/` if the page is drawn in `web/design/`.

**A new table**

1. Add the `Table` to `adapters/postgres/tables.py`.
2. Add a migration in `adapters/postgres/migrations/versions/`, numbered after the last one. Read `migrations/README.md` first: a seed prompt or Eval Case change has its own helper.
3. Add a repository `Protocol` to `core/ports.py` and a field to `Repositories`, or add methods to an existing repository if the table belongs to its area.
4. Write the `Postgres...Repository` in `adapters/postgres/repositories.py` and add it in `_build_repositories`.
5. If it holds per-User rows: give it `delete_for_user` and call it from `core/user_data.py`. `tests/test_data_deletion.py` fails otherwise.
6. Add the table to the `TRUNCATE` list in `tests/conftest.py` if tests need it empty.

## The Dashboard (`web/src/`)

| Path | What it is |
|---|---|
| `app/` | App Router pages. `(dashboard)/(user)/` for User pages, `(dashboard)/admin/` for Admin pages, plus `sign-in/`, `sign-up/`, `onboarding/` and the public pages (`page.tsx`, `how-it-works/`, `pricing/`). |
| `components/` | One component per file. |
| `lib/api-client.ts` | The one API client. `ApiClient` lists every backend call; `createApiClient` builds it. |
| `lib/use-api-client.ts`, `lib/choose-api-client.ts` | Give components the client, or the design-fixture client in fixture mode. |
| `lib/queries.ts` | React Query keys and shared hooks. |
| `lib/auth/` | The auth helper. `client.ts` (`useSessionToken`, `useSignOut`), `server.ts` (`isSignedIn`), `AuthProvider.tsx`. Clerk is imported only here, in `middleware.ts` and in the sign-in and sign-up pages. |
| `middleware.ts` | Clerk protects every route but the public ones (`lib/auth/public-routes.ts`). |
| `env.ts` | The typed `env` module: `apiUrl`, `clerkPublishableKey`, `designFixtures`, and `serverApiUrl()` for server-side calls. Read settings from here, not `process.env`. |

`web/design/README.md` is the UI contract: read it in full before any UI work. Pages are checked against `web/design/reference/*.html` with `web/design/compare.cjs` (ADR 0018).
