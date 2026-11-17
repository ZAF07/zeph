# 10 — Two saves of the same Move or Need name at once give a 500

Status: completed

## Symptom

When two Admin saves give a Move the same name (ignoring case) at the same moment, the second one should be refused like any taken name: a 409 with "There is already a Move called “…”." Instead it can fail with a 500 (an unhandled database error), and the Dashboard shows the generic "Couldn't save the Move" message.

Needs have the same gap: a taken Need name is normally refused with a 422 ("There is already a Need called “…”."), but two saves at once can give a 500 instead.

Nothing wrong is saved, because the unique index on the name stops the second row. Only the error is wrong. This is unlikely while the owner is the only Admin.

Not reproduced yet. Found in the code review of issue 02.

## Repro

Not deterministic: it needs two requests at the same moment.

1. As an Admin, send two `POST /api/admin/moves` requests at once with the same name (or with names that differ only in case), e.g. `{"name": "Celebrate", "when_it_fits": "x", "how_to_do_it": "y", "needed_feature": null}`.
2. Both pass the name check before either is saved. The second insert then hits the `moves_name_ignoring_case` unique index.
3. Expected: the second gets a 409. Actual: it can get a 500.

The same applies to `PUT /api/admin/moves/{id}`, and to `POST`/`PUT /api/admin/needs` (expected 422 there).

## Suspected location

- `src/companion/core/moves.py` — `MoveService._checked_details` checks the name against `list_all()`, then `add`/`update` save it in a separate step.
- `src/companion/core/needs.py` — `NeedService._checked_details`, same pattern.
- `src/companion/adapters/postgres/repositories.py` — `PostgresMoveRepository.add`/`update` and `PostgresNeedRepository.add`/`update` don't handle a unique-index error.

## Acceptance criteria

- [x] Two saves of the same Move name at once give one success and one 409 with the usual "already a Move called" text, never a 500
- [x] The same holds for Needs (one success and one 422)
- [x] A test covers the refused second save
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`

## Comments

Fixed as the issue suggested: the database's unique name rule stays the final guard, and its error is now turned into the usual refusal.
- **Port** (`core/ports.py`): new `NameTakenError`, raised by `NeedRepository`/`MoveRepository` `add` and `update` when another row already has the name.
- **Postgres adapter** (`adapters/postgres/repositories.py`): `_refusing_taken_names()` wraps the four saves and turns a `UniqueViolation` on `needs_name_key` or `moves_name_ignoring_case` into `NameTakenError`. Other database errors are still raised as before. The transaction rolls back before the error is turned.
- **Services** (`core/moves.py`, `core/needs.py`): `add`/`update` catch `NameTakenError` and raise the same error the name check raises (`name_taken_error`): `MoveNameTakenError` (409) or `InvalidNeedError` (422), with "There is already a … called “…”."

Evidence per acceptance criterion:
- **Moves: one success and one 409, never a 500**: `/run` on the worktree stack (8020) as a signed-in Admin, 15 rounds each of 4 `POST /api/admin/moves` at once with the same name (two in capitals) and 2 `PUT`s renaming to the same name. Before the fix (same script, fix stashed): 27 POST and 13 PUT moves got 500s (backend log `500 Internal Server Error`). With the final code: POST 15 × 201 and 45 × 409, PUT 15 × 200 and 15 × 409, text "There is already a Move called “Final14”.", 0 × 500 in the backend log.
- **Needs: one success and one 422**: same runs. Before: 37 POST and 10 PUT needs got 500s. After: POST 15 × 201 and 45 × 422, PUT 15 × 200 and 15 × 422, "There is already a Need called “NeedFinal14”.", no 500s.
- **A test covers the refused second save**: `tests/test_admin_moves.py::test_adding_a_name_another_save_took_at_the_same_moment_is_refused` and `test_renaming_to_a_name_another_save_took_at_the_same_moment_is_refused`; `tests/test_admin_needs.py::test_adding_a_need_name_another_save_took_at_the_same_moment_is_refused` and `test_renaming_a_need_to_a_name_another_save_took_at_once_is_refused`. They let another save land just after the name check (`MovesSavedDuringTheNameCheck`, `NeedsSavedDuringTheNameCheck`). All four were red before the fix (`UniqueViolation`) and are green after.
- **Checks pass**: `uv run ruff check .` all passed; `uv run ruff format --check .` 439 files formatted; `uv run mypy src` no issues in 181 files; `uv run pytest -n auto` 1279 passed.

Code review (Standards and Spec, sub-agents):
- Fixed: `name_taken` renamed `name_taken_error` (it builds an error, not a yes/no check).
- Filed: issue 12. Need names that differ only in case, saved at once, both save, because `needs_name_key` is case-sensitive (Moves' index is on `lower(name)`). This needs a migration, so it's kept out of this fix.
- Kept: the short try/except in each of the four saves (plain to read); the index names as strings in `UNIQUE_NAME_INDEXES`, which is the name issue 12 adds to.

## Completion

- Completed: 2026-11-17
- Commits (branch `moves-10-same-name-at-once`):
  - `55947b9` Moves issue 10: a same-name save at the same moment is refused, not a 500
  - `0e3f061` Moves issue 10: review fixes; file issue 12 for Need names differing only in case
  - `eeb0871` Moves issue 10 done: archive issue with check and run evidence
- Merge into `main`: `f9128f6` Merge Moves issue 10: a same-name Move or Need save at the same moment is refused (409 or 422), not a 500
