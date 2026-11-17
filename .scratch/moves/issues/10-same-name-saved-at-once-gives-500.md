# 10 — Two saves of the same Move or Need name at once give a 500

Status: needs-triage

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

- [ ] Two saves of the same Move name at once give one success and one 409 with the usual "already a Move called" text, never a 500
- [ ] The same holds for Needs (one success and one 422)
- [ ] A test covers the refused second save
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
