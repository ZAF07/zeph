.PHONY: check check-python check-web contract eval up

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

## Real-LLM evals (issue 15).
eval:
	@echo "No evals yet; they arrive in issue 15." && exit 1

## Start everything.
up:
	docker compose up --build
