# 09 — Map core errors to HTTP status codes once

Status: ready-for-agent

## Parent

Architecture review, 14 Nov 2026, point 8. Decided in a `/grill-with-docs` session.

## Why

Routes in `adapters/http/dashboard_api.py` and `admin_api.py` catch core errors and raise `HTTPException` by hand (about 100 uses). Status codes can drift between routes. Some routes combine several core calls (Home, the Check-ins page via `to_check_ins_response`, `to_home_response`) and read platform settings directly (`get_platform_content`).

## What to build

- A few core error base classes (e.g. `NotFoundError`, `NotAllowedError`, `InvalidError`, `ConflictError`); existing core errors inherit from them.
- FastAPI exception handlers registered once: not found → 404, Feature not available / not allowed → 403, invalid → 422, conflict (e.g. `LastAdminError`) → 409.
- Routes call one core method and return its result; page-shaped combining (Home, Check-ins page) moves into core.

## Decisions

- Done for consistency and extensibility: a new error gets the right status by its base class; new routes stay small.
- Response bodies and status codes don't change for existing routes.

## Acceptance criteria

- [ ] Exception handlers registered once; routes no longer map core errors by hand
- [ ] Every existing core error has a base class and keeps its current status code (tests)
- [ ] Home and Check-ins routes make one core call each; routes don't read platform settings directly
- [ ] Existing API tests pass; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [ ] `/run`: a 404, a 403 (Feature off), a 422 and a 409 (last Admin) from the Dashboard look as before

## Blocked by

- `.scratch/architecture/issues/07-transaction-port-admin-rule-data-deletion.md` (one `LastAdminError`)
