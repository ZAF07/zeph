.PHONY: check check-python check-web contract eval up restart worktree-setup worktree-teardown db-copy

MAIN_DIR := $(shell dirname "$$(git rev-parse --path-format=absolute --git-common-dir)")
THIS_DIR := $(shell git rev-parse --show-toplevel)
COMPOSE := env -u COMPOSE_PROJECT_NAME -u COMPOSE_PROFILES docker compose
WORKTREE_PROJECT := $(shell sed -n 's/^COMPOSE_PROJECT_NAME=//p' .env 2>/dev/null)
WORKTREE_COMPOSE := env -u COMPOSE_PROJECT_NAME docker compose -p "$(WORKTREE_PROJECT)"
MAIN_COMPOSE := cd "$(MAIN_DIR)" && env -u COMPOSE_PROJECT_NAME -u COMPOSE_PROFILES docker compose
REQUIRE_WORKTREE = @test "$(THIS_DIR)" != "$(MAIN_DIR)" -a -n "$(WORKTREE_PROJECT)" || { echo "Run this in a worktree set up with make worktree-setup."; exit 1; }

## Run every check from CLAUDE.md (Python and TypeScript).
check: check-python check-web

check-python:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy
	uv run pytest

check-web:
	cd web && pnpm lint
	cd web && pnpm format:check
	cd web && pnpm typecheck
	cd web && pnpm test

## Adapter contract tests against real services; needs keys in .env.
contract:
	set -a && . ./.env && set +a && uv run pytest -m contract

## Real-LLM evals: Safeguard, Persona, Knowledge and Settings; needs keys in .env. See evals/README.md.
eval:
	set -a && . ./.env && set +a && uv run pytest evals -m eval

## Start everything.
up:
	$(COMPOSE) up --build

## Rebuild and restart everything in the background, picking up code and .env changes.
restart:
	$(COMPOSE) up --build --force-recreate --detach

## Run once in a new git worktree: own .env, ports and database, then install packages.
worktree-setup:
	uv sync
	uv run python -m scripts.worktree_setup
	cd web && pnpm install

## Stop this worktree's stack and delete its containers, images, network and database. Run when done.
worktree-teardown:
	$(REQUIRE_WORKTREE)
	$(WORKTREE_COMPOSE) down --volumes --remove-orphans --rmi local

## Replace this worktree's database with a copy of the main stack's (both stacks running).
## Telegram links are removed from the copy so this stack's Check-ins never reach real Users.
db-copy:
	$(REQUIRE_WORKTREE)
	($(MAIN_COMPOSE) exec -T postgres sh -c 'pg_dump -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"') > .db-copy.sql
	$(WORKTREE_COMPOSE) stop backend
	$(WORKTREE_COMPOSE) exec -T postgres sh -c 'dropdb --force -U "$$POSTGRES_USER" "$$POSTGRES_DB" && createdb -U "$$POSTGRES_USER" "$$POSTGRES_DB"'
	$(WORKTREE_COMPOSE) exec -T postgres sh -c 'psql -q -v ON_ERROR_STOP=1 -U "$$POSTGRES_USER" -d "$$POSTGRES_DB"' < .db-copy.sql
	$(WORKTREE_COMPOSE) exec -T postgres sh -c 'psql -q -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -c "delete from telegram_connections"'
	rm .db-copy.sql
	$(WORKTREE_COMPOSE) start backend
