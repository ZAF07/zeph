.PHONY: check check-python check-web contract eval up restart

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

## Real-LLM evals: Safeguard, Persona and Knowledge; needs keys in .env. See evals/README.md.
eval:
	set -a && . ./.env && set +a && uv run pytest evals -m eval

## Start everything.
up:
	docker compose up --build

## Rebuild and restart everything in the background, picking up code and .env changes.
restart:
	docker compose up --build --force-recreate --detach
