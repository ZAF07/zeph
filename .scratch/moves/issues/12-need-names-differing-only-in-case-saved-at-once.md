# 12 — Two Need names that differ only in case, saved at once, both save

Status: needs-triage

## Symptom

Need names are meant to be unique ignoring case: `NeedService` refuses "celebrate" when "Celebrate" exists (422, "There is already a Need called “…”."). But the database only stops exact matches: `needs.name` has a plain unique rule (`needs_name_key`, migration 0028), not one on `lower(name)` like Moves' `moves_name_ignoring_case`.

So two Admin saves at the same moment of "Celebrate" and "celebrate" both pass the name check and both save. The result is two Needs whose names differ only in case. No error is shown.

Unlikely while the owner is the only Admin. Found in the code review of issue 10, which fixed the 500 for exact same-name saves at once.

## Repro

Not deterministic: it needs two requests at the same moment.

1. As an Admin, send two `POST /api/admin/needs` at once, one named "Celebrate" and one "celebrate".
2. Expected: one 201 and one 422. Actual: both can get 201.

## Suspected fix

- A migration adding a unique index on `lower(name)` for `needs` (and dropping `needs_name_key`, or keeping it). Check no live rows clash first.
- Add the new index name to `UNIQUE_NAME_INDEXES` in `src/companion/adapters/postgres/repositories.py`, so a clash is refused like a taken name.
- Mirror it in `src/companion/adapters/postgres/tables.py`.

## Acceptance criteria

- [ ] Two saves at once of Need names that differ only in case give one success and one 422 with the usual "already a Need called" text
- [ ] A test covers it (see `NeedsSavedDuringTheNameCheck` in `tests/test_admin_needs.py`)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
