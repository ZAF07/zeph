# 07 — Transaction port; last-Admin rule and Delete My Data in core

Status: ready-for-agent

## Parent

Architecture review, 14 Nov 2026, point 6. Decided in a `/grill-with-docs` session. ADR: `docs/adr/0008-transactions-across-repositories-through-a-port.md`.

## Why

- "There is always at least one Admin" is written twice in SQL (`demote_unless_last_admin`, `delete_unless_last_admin` in `adapters/postgres/repositories.py`), with two `LastAdminError` classes (`core/admin_users.py`, `core/user_data.py`).
- `UserRepository.delete_data` deletes rows from 8 tables owned by other repositories. A new per-User table can be missed: a privacy leak.

## What to build

- Transaction port: `with repositories.transaction() as tx:` gives the repositories inside one transaction, plus `tx.lock_admins()`.
- The last-Admin rule in core, in one place, used by demoting an Admin and deleting an account; one `LastAdminError`.
- `delete_for_user(user_id)` on every repository holding per-User data; Delete My Data and Account Deletion call them all in one transaction.
- A test that lists every table with a `user_id` column and fails if any isn't cleared by Delete My Data (except tables that must survive it, listed explicitly, e.g. the User row and pending auth account deletions).

## Decisions

- Transaction port over keeping the SQL: removes the duplicate rule and the privacy-leak risk, and is reusable.
- No change in behaviour.

## Acceptance criteria

- [ ] Transaction port and Postgres adapter, with Admin row locking
- [ ] Last-Admin rule only in core; one `LastAdminError`
- [ ] Each repository deletes only its own rows; `delete_data`, `demote_unless_last_admin`, `delete_unless_last_admin` are gone
- [ ] Coverage test for per-User tables
- [ ] Concurrency test: two last-but-one Admins demoting each other at once leaves one Admin
- [ ] Existing tests pass; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [ ] `/run`: Delete My Data in chat and on the Dashboard clears the User's data; demoting the last Admin is refused

## Blocked by

None.
