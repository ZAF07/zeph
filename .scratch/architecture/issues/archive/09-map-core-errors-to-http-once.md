# 09 — Map core errors to HTTP status codes once

Status: completed

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

- [x] Exception handlers registered once; routes no longer map core errors by hand
- [x] Every existing core error has a base class and keeps its current status code (tests)
- [x] Home and Check-ins routes make one core call each; routes don't read platform settings directly
- [x] Existing API tests pass; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [x] `/run`: a 404, a 403 (Feature off), a 422 and a 409 (last Admin) from the Dashboard look as before

## Blocked by

- `.scratch/architecture/issues/07-transaction-port-admin-rule-data-deletion.md` (one `LastAdminError`)

## Comments

### 14 Nov 2026 — done

- Base classes in `core/errors.py`: `CoreError` with `NotFoundError` (404), `NotAllowedError` (403), `InvalidError` (422), `ConflictError` (409) and `OutsideServiceError` (502, needed to keep the sticker-import 502). An error's text is its class's `shown_message`, or the text it was raised with. `NotFoundError` is still a `LookupError` and `InvalidError` still a `ValueError`, so older catches keep working.
- Every core error a route mapped by hand now inherits from one and carries the exact text the route showed. `MemoryNotFoundError` got a subclass, `ConversationSummaryNotFoundError`, because the two routes showed different text. `LastAdminError` is raised with the text for the change being refused (`LAST_ADMIN_DEMOTION`, `LAST_ADMIN_ACCOUNT_DELETION`) through `refuse_if_last_admin(..., refusal)`. `StickerSetNotFoundError` builds its own "There is no sticker set called “X”." text.
- `adapters/http/errors.py`: `add_core_error_handlers(app)`, called once in `create_app`, answers each kind with its status and `{"detail": message}`. The routes in `admin_api.py` and `dashboard_api.py` have no `except` blocks left (27 admin, 10 Dashboard removed).
- Core now shapes the pages: `HomeService.get(user)` (now also returns Check-ins availability, memory note and the short AI notice), `CheckInService.page(user)` → `CheckInsPage`, `MeService.describe(user)` → `Me` (new `core/me.py`), and `PlatformSettingsService.dashboard_content()` → `DashboardContent`. The Dashboard router no longer gets the settings repository.
- Not changed: errors that never reach HTTP (`EmptyReplyError`, `TextExtractionError`, `MessageRefusedError`, `ChatBlockedError`, `InvalidCheckInAnswerError`) have no base class. The three "image missing" 404s (Shared Photo, Personal Sticker, Sticker Library) still raise `HTTPException` in the route, because they come from a `None` result, not a core error. Auth's 401/403 are unchanged. Routes that change Check-ins or the profile make the change and then call `page`/`describe`, so that's two core calls.
- Code review (Standards and Spec in parallel): no standards breaches; every status code and body matches `main`. Fixed: repeated `to_check_ins_response(check_in_service.page(...))` and `to_me_response(me_service.describe(...))` now go through one helper each. Not changed: the handler's `else str(error)` branch (needed for Starlette's handler type); `Me` keeps its name to match `/me` and `MeResponse`; the new core methods are tested through the API tests (`test_dashboard_home.py`, `test_check_ins.py`, `test_onboarding.py`, `test_photo_viewing.py`).
- `/run` (worktree stack, ports 3150/8150, real Clerk, the only Admin):
  - 404: `DELETE /api/memory-items/<unknown>` → `{"detail":"Memory not found"}`; `GET /api/admin/users/<unknown>/features` → `{"detail":"No such User"}`.
  - 422: `PATCH /api/me` with time zone `Mars/Nowhere` → `{"detail":"Time zone is not recognised."}`.
  - 403: with Check-ins off for everyone, `PATCH /api/check-ins` → `{"detail":"Not available on your account"}`; the Check-ins page shows "Not available on your account" and the "Check-ins aren't available…" notice.
  - 409: demoting yourself → "This is the last Admin. Make someone else an Admin first."; Delete my account on `/account` → the page shows "You’re the only Admin. Make someone else an Admin before deleting your account."
  - `GET /api/me`, `/api/home`, `/api/check-ins`, `/api/platform-content` → 200 with the same fields. No page errors. The run's Feature switch row and the test user were removed afterwards.

## Completion

- Completed: 2026-11-14
- Evidence per criterion:
  - Handlers registered once; no hand mapping: `add_core_error_handlers(app)` at `src/companion/app.py:295` only; `grep "except " src/companion/adapters/http/` finds none.
  - Every core error has a base class and keeps its status: `tests/test_core_error_status_codes.py`, 29 cases (each error, its base, status and exact body) plus one showing a new error gets its status from its base.
  - Home and Check-ins make one core call each; no settings reads in routes: `get_home` → `home_service.get(user)`, `get_check_ins` → `check_in_service.page(user)`; `grep "platform_settings\.|\.load()"` in `dashboard_api.py` finds none.
  - Checks (after rebase on the Understanding docs): `pytest` 735 passed (9 evals deselected); `ruff check .` and `ruff format --check .` clean; `mypy` no issues in 106 files.
  - `/run`: see Comments.
- Commits:
  - 0261446 "Architecture issue 09: map core errors to HTTP once"
  - 77f2f1c "Review fixes: one helper each for the /me and Check-ins responses"
  - 4c2092e "Architecture issue 09 done: archive issue with test, run and review evidence; ADR 0011 says core errors carry their kind and HTTP maps each kind once"
  - 52031d4 "Merge architecture issue 09: map core errors to HTTP once; …" (merged into main)

