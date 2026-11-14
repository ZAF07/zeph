# Transactions across repositories go through a port

Core gets one database transaction across several repositories through a transaction port (`with repositories.transaction() as tx:`), with explicit locks where a rule needs them (e.g. locking the Admin rows). Domain rules that need "all or nothing", such as "there is always at least one Admin", live in core and run inside that transaction, instead of being written in SQL inside one repository. We chose this because the rule was written twice in SQL, and Delete My Data had one repository deleting rows from eight tables owned by others, so a new per-User table could be missed and leak a User's data.

## Consequences

- Every repository that holds per-User data has `delete_for_user(user_id)`. Delete My Data and Account Deletion call them all inside one transaction, and a test fails if a per-User table isn't covered.
- Ports stay free of SQL: the transaction and locks are port methods; the Postgres adapter implements them.
- One `LastAdminError`, in core.
- Any future "all or nothing" change uses the same port rather than a new combined SQL method.
