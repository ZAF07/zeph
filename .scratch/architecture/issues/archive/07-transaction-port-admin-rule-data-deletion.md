# 07 — Transaction port; last-Admin rule and Delete My Data in core

Status: completed

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

- [x] Transaction port and Postgres adapter, with Admin row locking
- [x] Last-Admin rule only in core; one `LastAdminError`
- [x] Each repository deletes only its own rows; `delete_data`, `demote_unless_last_admin`, `delete_unless_last_admin` are gone
- [x] Coverage test for per-User tables
- [x] Concurrency test: two last-but-one Admins demoting each other at once leaves one Admin
- [x] Existing tests pass; `pytest`, `ruff`, `ruff format --check`, `mypy` pass
- [x] `/run`: Delete My Data in chat and on the Dashboard clears the User's data; demoting the last Admin is refused

## Blocked by

None.

## Comments

### 14 Nov 2026 — done

- Port (`core/ports.py`): `Repositories.transaction()` gives a `Transaction` with `.repositories` (each working inside it) and `lock_admins()`. A transaction started inside another joins it.
- Postgres adapter: repositories take a `Database` (the engine, or one transaction's connection). `PostgresTransaction.lock_admins` is `SELECT … FOR UPDATE` on the Admin rows, in ID order so two lockers never deadlock. Any exception rolls the whole transaction back.
- Rule: `refuse_if_last_admin(transaction, user_id)` and the one `LastAdminError`, in `core/admin_users.py`. Used by demoting an Admin and by Account Deletion.
- Deletion: `delete_for_user` on all 9 repositories with per-User rows. `delete_user_data` (Delete My Data, Dashboard and chat) calls the 6 data ones; Account Deletion also calls Usage, Safeguard Events and Feature Switches, then `users.delete`; cascading foreign keys are only a safety net. The auth-account retry deletes a re-signed-in User the same way, and `PendingAuthAccountDeletionRepository.complete` now only removes its own row.
- Behaviour unchanged. Known and unchanged from before: Account Deletion forgets the conversation engine's saved state before the last-Admin check, so a refused last Admin loses it.
- Code review (Standards and Spec in parallel). Fixed: Usage, Safeguard Events and Feature Switches got `delete_for_user` (the users repository no longer relies on cascades for them); the lock-wait helper only counts `FOR UPDATE` queries on the test database; a docstring. Not changed: `forget_user` stays before the database delete in the retry, as before; the rule stays in `admin_users.py`.
- `/run` (worktree stack, ports 3120/8120, real Clerk):
  - Removing the only Admin on `/admin/users`: 409 and "Can't remove Run check: they're the only Admin…"; they stay Admin.
  - Delete my account as the only Admin: 409, "You're the only Admin…".
  - Delete my data on `/account` with data in all 8 data tables (Telegram connected with `/start`, a message through the webhook, the rest by SQL): 204; every per-User table 0, User row kept. (The stickers card only clears on reload; the frontend is untouched by this issue.)
  - Chat Delete My Data: the webhook can't reach `settle` in a worktree (the reply gate's typing call to a fake chat is refused by Telegram first), so the real `ChatDataDeletion.settle` was run inside the backend container on the real database with a recording chat channel: answer `confirmed`, the deleted reply sent, every per-User table 0, account and flag cleared. The full webhook path is covered by `tests/test_settings_via_chat.py`.
  - Delete my account as a plain User with data (re-run after the review fixes): 204; every table 0 including the User; Clerk user gone (404); nothing left pending.

## Completion

- Completed: 2026-11-14
- Evidence per criterion:
  - Transaction port and Postgres adapter, with Admin row locking: `Transaction`/`Repositories.transaction` in `core/ports.py`; `PostgresTransaction`, `_TransactionConnection`, `_begin_transaction` in `adapters/postgres/repositories.py`. `test_a_failed_transaction_changes_nothing`.
  - Last-Admin rule only in core; one `LastAdminError`: `grep "class LastAdminError"` finds only `core/admin_users.py`; the only `with_for_update` is in `lock_admins`.
  - Each repository deletes only its own rows; the three combined methods are gone: `grep` finds none of `delete_data` (repository), `demote_unless_last_admin`, `delete_unless_last_admin`; 9 `delete_for_user` in port and adapter; the users and pending repositories delete only from their own tables.
  - Coverage test: `test_delete_my_data_removes_every_kind_of_data_but_keeps_the_account` reads every table with a `user_id` column from `information_schema`, fails if one has no test data, and checks each is cleared unless in `TABLES_KEPT_BY_DELETE_MY_DATA` (`daily_usage`, `safeguard_events`, `user_feature_switches`), which must stay unchanged. Account deletion checks every such table is empty.
  - Concurrency test: `test_two_admins_demoting_each_other_at_the_same_moment_leave_one_admin` holds the Admin lock, waits until the other demotion is blocked on it (`pg_stat_activity`), then demotes; the other gets `LastAdminError` and one Admin is left. It fails with `FOR UPDATE` removed.
  - Checks (after rebase on issue 06): `pytest` 706 passed (9 evals deselected); `ruff check`, `ruff format --check` clean; `mypy src` no issues in 102 files.
  - `/run`: see Comments.
- Commits:
  - e61f74c "Architecture issue 07: transaction port; last-Admin rule and Delete My Data in core"
  - 6c713f3 "Review fixes: every per-User repository deletes its own rows; tighter lock wait"
  - 47103e4 "Architecture issue 07 done: archive issue with test, run and review evidence; ADR 0008 says which deletes Delete My Data skips"
  - 2c3eb04 "Merge architecture issue 07: transaction port; last-Admin rule and Delete My Data in core" (merged into main)
