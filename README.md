# AI Companion (Zeph)

Zeph is an AI companion that Users talk to through Telegram. A web Dashboard lets Users manage their account, preferences and privacy, and lets Admins configure the platform.

What the product is for: `ABOUT.md`. What each term means (User, Admin, Conversation, Check-in, ...): `CONTEXT.md`.

## What's in the repo

| Folder | What it holds |
|---|---|
| `src/companion/` | Python backend (FastAPI), ports and adapters |
| `web/` | Next.js Dashboard |
| `tests/` | Python tests |
| `evals/` | The Evals guide (`README.md`). The Eval code and cases are in `src/companion/` |
| `scripts/` | Worktree setup, load test, backup |
| `docs/` | Guides and ADRs (`docs/adr/`) |

## Prerequisites

- **Docker** with Compose. The stack runs in it, and `pytest` starts its own Postgres with testcontainers.
- **uv**, for Python. The project needs Python 3.12 (`.python-version`, `pyproject.toml`).
- **pnpm**, for the Dashboard. The Dashboard image uses Node 22.

## First-time setup

1. Copy `.env.example` to `.env` and fill it in. `.env` is never committed. The groups that matter:

   | Group | Keys | Notes |
   |---|---|---|
   | Compose | `COMPOSE_PROFILES` | `local,eval` locally (ngrok and eval-runner) |
   | Postgres | `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | Pick any values |
   | Clerk | `CLERK_SECRET_KEY`, `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Sign-in |
   | Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `TELEGRAM_WEBHOOK_SECRET` | See "Telegram locally" |
   | ngrok | `NGROK_AUTHTOKEN`, `NGROK_DOMAIN` | So Telegram can reach your laptop |
   | Addresses | `WEBHOOK_BASE_URL`, `NEXT_PUBLIC_API_URL`, `DASHBOARD_URL` | Locally `WEBHOOK_BASE_URL` is `https://<NGROK_DOMAIN>` |
   | Model and search | `OPENROUTER_API_KEY`, `TAVILY_API_KEY`, `DEEPSEEK_API_KEY` | DeepSeek only when `CHAT_MODEL_ADAPTER=deepseek` |
   | Admins | `INITIAL_ADMIN_EMAILS` | Emails that become Admins on first sign-in |
   | Optional | `*_ADAPTER`, `MODEL_CALL_DEVELOPER_LOGS`, `MESSAGE_POOL_SIZE`, ports | Defaults are in `.env.example` |

   A missing required key stops startup with a message naming it. The backend reads settings in `src/companion/config.py`; the Dashboard in `web/src/env.ts`.

2. Start the stack:

   | Command | What it does |
   |---|---|
   | `make up` | Builds and starts everything, in the foreground |
   | `make restart` | Rebuilds and restarts everything in the background. Use it after code or `.env` changes |

   What starts (`docker-compose.yml`):

   | Service | Address | Notes |
   |---|---|---|
   | `postgres` | `localhost:5432` | Postgres 16 with pgvector |
   | `backend` | `http://localhost:8000` | Runs migrations and loads seed data, then the API. Health: `/health` |
   | `web` | `http://localhost:3000` | The Dashboard (a production build) |
   | `ngrok` | your `NGROK_DOMAIN` | Profile `local` only |
   | `eval-runner` | none | Profile `eval` only. Works Eval Runs |

   Ports come from `POSTGRES_PORT`, `BACKEND_PORT` and `WEB_PORT`. `caddy` (HTTPS) runs in production only (profile `prod`).

## Running checks

| Command | What it runs |
|---|---|
| `make check` | `check-python` and `check-web` |
| `make check-python` | `ruff check`, `ruff format --check`, `mypy`, `pytest` |
| `make check-web` | In `web/`: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test` |
| `make contract` | Only the tests marked `contract` |

**Contract tests** check the adapters against the real outside services, so they need real keys in `.env`. Plain `pytest` skips them (`-m 'not contract'` in `pyproject.toml`). They live in `tests/contract/`.

## Telegram locally

See `docs/LOCAL_TELEGRAM_BOT_GUIDE.md`. In short: production keeps the real bot, and local work uses its own bot through ngrok, because Telegram sends a bot's messages to one address only. Without a local bot, set `TELEGRAM_WEBHOOK_REGISTER=false` and post updates to `http://localhost:8000/telegram/webhook`.

## Worktrees

Each git worktree can run its own stack next to the main one.

| Command | What it does |
|---|---|
| `make worktree-setup` | Run once in a new worktree. Copies `.env` from the main folder, picks free ports (3010/8010/5442, then 3020/8020/5452, ...), names its own Compose project (so its own database), turns off ngrok and Telegram webhook registration, and installs packages. Never writes to the main folder |
| `make worktree-teardown` | Stops the worktree's stack and deletes its containers, images, network and database. Also clears Docker build cache older than 48 hours |
| `make db-copy` | Replaces the worktree's database with a copy of the main stack's (both must be running). Telegram links are removed, so its Check-ins never reach real Users |

A worktree's addresses are `WEB_PORT` and `BACKEND_PORT` in its `.env`. Test Telegram by posting to `/telegram/webhook` on `BACKEND_PORT`.

## Other make targets

| Command | What it does |
|---|---|
| `make eval` | Runs real-model Evals on this stack's eval-runner. **Costs money.** `EVALS=` and `CASES=` pick what runs. See `evals/README.md` |
| `make match-patterns` | Matches Patterns with no Pattern Type to the Pattern Catalog, then tags their evidence again. **Makes real model calls.** `TYPES=` picks Pattern Types |
| `make load-test` | Load tests a worktree's stack for free, on adapters that call no model, search or Telegram. Worktrees only. `make restart` puts the backend back |

## Guides

| Guide | What it's for |
|---|---|
| `docs/developer/code-map.md` | Where things are in the code |
| `docs/developer/privacy-and-user-data.md` | What User data is kept and how it is removed |
| `docs/developer/features-and-settings.md` | Features and Platform Settings |
| `docs/developer/how-work-runs.md` | How background work runs |
| `docs/developer/check-ins.md` | How Check-ins work |
| `docs/developer/user-memory.md` | How User Memory works |
| `docs/developer/model-calls.md` | How model calls are made and logged |
| `docs/message-pipeline/README.md` | How Zeph handles a message, from texts arriving to Conversation end. A target design, with notes on what is built |
| `docs/pattern-pipeline/README.md` | How Zeph finds, tests and shares a Pattern. A target design, with notes on what is built |
| `docs/pattern-pipeline/lifecycle.md` | How Observations and Patterns are scored and change state |
| `docs/pattern-pipeline/tagging.md` | How tagging turns what a User said into Observations |
| `docs/pattern-catalog/README.md` | Admin guide to the Pattern Catalog and its Pattern Types |
| `docs/thought-experiments/README.md` | Admin guide to Thought Experiments |
| `docs/pattern-evals/README.md` | How the Pattern pipeline is tested, and how far to trust each Eval |
| `evals/README.md` | What each Eval checks and how to run it |
| `web/design/README.md` | The build contract for all Dashboard UI work. Read it in full first |
| `docs/DEPLOYMENT_GUIDE.md` | How production runs and how to deploy |
| `docs/PROMPT_EDITS_AND_DEPLOYS_GUIDE.md` | Keeping an Admin's prompt edits across a deploy |
| `src/companion/adapters/postgres/migrations/README.md` | How migrations run, and how to change a seed prompt |
| `docs/adr/` | Why decisions were made, one ADR each |

## How work is tracked

- Issues are markdown files in `.scratch/<feature>/issues/`. See `docs/agents/issue-tracker.md`.
- How we work and the coding standards are in `CLAUDE.md`.
