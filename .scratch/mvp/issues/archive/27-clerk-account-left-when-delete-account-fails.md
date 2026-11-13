# 27 — A failed Clerk call during Delete account leaves the Clerk account behind

Status: completed

## Parent

`.scratch/mvp/PRD.md` (a caveat left in `issues/archive/14-data-retention-and-deletion.md`)

## Symptom

Delete account runs three steps in order (`UserDataService.delete_account`):

1. Forget the conversation engine's saved state.
2. Delete the User's row (all their tables go with it).
3. Ask Clerk to delete their account (`ClerkAccounts.delete_account`).

If step 3 fails (Clerk down, network error, wrong secret key), our data is already gone but:

- The Clerk account is still there and the User is still signed in.
- The page shows "We couldn't delete your account. Please try again."
- Their next request makes a brand-new empty User (`UserService.get_or_create`). If they reload, the Dashboard sends them to onboarding, so they have to finish onboarding before they can try again.
- If they just leave, the Clerk account (with their email) stays forever. Signing in later gives a fresh empty account.

Expected: once a User confirms Delete account, their Clerk account is deleted for sure, without them having to do anything else.

## Repro

Deterministic. Make Clerk fail during the delete, for example:

- In a test: have the fake auth accounts raise on `delete_account`, then call `DELETE /api/me`. The response is 500, the users row is gone, and nothing remembers the Clerk account still needs deleting.
- In the running app: set a wrong `CLERK_SECRET_KEY` for the backend only, then press Delete account.

## Suspected location

- `src/companion/core/user_data.py` — `UserDataService.delete_account`
- `src/companion/adapters/clerk/accounts.py` — `ClerkAccounts.delete_account`
- `web/src/components/DeleteAccountSection.tsx` — the failed state

## Chosen fix (decided by the user)

The sturdier fix: keep a list of "Clerk accounts still to delete" and have the scheduler retry them each tick until Clerk succeeds.

- Delete account saves the auth ID to that list in the same transaction that deletes the User's row, so we never lose track of it.
- Then it tries Clerk straight away. If that works, the entry is removed. If not, the request still succeeds for the User (their data is gone) and they are signed out.
- Each scheduler tick retries what's left. A 404 from Clerk counts as done (already the case).
- The list holds only the auth ID and when it was added, so no personal data is kept.

Open detail to settle while implementing: a User with a pending entry who signs in again before the retry works would get a new empty User. The retry should still delete the Clerk account (which signs them out). Note what was chosen in Comments.

## Acceptance criteria

- [x] If Clerk fails during Delete account, the User's data is still deleted, the User is signed out, and the page doesn't show an error
- [x] The Clerk account is deleted on a later scheduler tick once Clerk works again, and the entry is then removed
- [x] Repeated Clerk failures keep the entry and are logged, without stopping other scheduled work
- [x] The pending list holds no personal data beyond the auth ID
- [x] Tests cover: Clerk fails then the retry succeeds; Clerk returns 404 on retry; the scheduler keeps going when a retry fails
- [x] `/run`: with Clerk made to fail, Delete account signs the User out; once Clerk is fixed, the next tick deletes the Clerk account
- [x] `make check` passes (`pytest`, `ruff`, `ruff format`, `mypy`, `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`)

## Comments

### 2026-11-13 — implemented (branch `mvp-27-clerk-delete-retry`)

- New table `pending_auth_account_deletions` (`auth_id`, `added_at` only; migration 0019). `UserRepository.delete_unless_last_admin(user_id, deleted_at)` deletes the User and adds their auth ID in one transaction.
- `UserDataService.delete_account` then tries Clerk; on success the entry is removed. Any failure is logged with the auth ID ("Could not delete an account at the auth provider (<auth_id>); will try again") and the request still returns 204, so the Dashboard signs the User out with no error. No web change was needed.
- `ScheduledWork.tick` calls `UserDataService.delete_pending_auth_accounts()` last. Each entry is tried on its own, so one failure doesn't stop the others.
- **Open detail, decided:** if the User signs in again before the retry works, a new empty User is made. When the retry succeeds it deletes the Clerk account (signing them out), forgets that User's conversation engine state, and deletes that User row in the same step as removing the entry (`PendingAuthAccountDeletionRepository.complete`). This means no orphan row is left that could still get Check-ins over Telegram.
- Known small gaps, left as they are: (1) a Clerk session token can stay valid for up to about a minute after the Clerk account is deleted. A request in that window could create a new empty User with no pending entry. That User could never sign in again, but the row would stay. (2) The "User who signed in again" cleanup doesn't check whether they are the last Admin.
- Code review fixes: a second, simultaneous DELETE no longer returns 500 (`scalar_one_or_none`); a database error after Clerk succeeds is caught and logged rather than shown to the User; the test fake moved to `tests/fakes.py`.
- `/run` (worktree stack, ports 3020/8020): signed in a test User and opened `/account` so the backend cached Clerk's keys. Then blocked `api.clerk.com` inside the backend container (`/etc/hosts`) and pressed Delete account. Result: `DELETE /api/me -> 204`, landed on `/sign-in`, no error on the page, `users` row gone, one `pending_auth_account_deletions` row, failure logged. The next tick, with Clerk still blocked, logged again and kept the entry. After `/etc/hosts` was restored, the next tick deleted it: Clerk `GET /users/<id>` went from 200 to 404, and the pending row count went from 1 to 0.

### 2026-11-13 — post-implement evidence

- Criterion 1: `test_a_failed_auth_account_delete_still_deletes_the_users_data` (204, users row gone, entry saved, failure logged). `/run`: `DELETE /api/me -> 204`, landed on `/sign-in`, no error on the page.
- Criterion 2: `test_a_later_tick_deletes_the_auth_account_once_the_provider_works`. `/run` (repeated on the final rebased code): Clerk user went from 200 to 404 on the tick after Clerk was unblocked, pending rows went from 1 to 0.
- Criterion 3: same test (two logged failures, entry kept) plus `test_one_failing_retry_does_not_stop_the_others`. Retry runs last in `ScheduledWork.tick` and catches each entry's errors.
- Criterion 4: migration 0019 has only the columns `auth_id` and `added_at`.
- Criterion 5: the tests above, plus `test_an_account_already_gone_from_clerk_on_retry_counts_as_deleted` (real `ClerkAccounts` answering 500 then 404), `test_the_retry_also_deletes_a_user_made_by_signing_in_again` and `test_deleting_an_account_twice_at_once_is_harmless`.
- Criterion 6: the `/run` evidence above. Log line: `Could not delete an account at the auth provider (user_3M3A…); will try again`.
- Criterion 7: `make check` on the rebased branch: ruff "All checks passed!", 224 files already formatted, mypy "no issues found in 91 source files", pytest 473 passed, web lint/format/typecheck clean, vitest 299 passed.
- Glossary: CONTEXT.md "Account Deletion" now says it always finishes, even if the sign-in account has to be removed later.

## Completion

- Completed: 2026-11-13
- Commit: b596cc9 "Retry deleting the Clerk account when it fails during Delete account", 35514bf "Address review: harmless double delete, catch post-Clerk errors, log auth ID", archive and glossary 6cdcb62 "MVP issue 27 done: archive issue with test, run and review evidence; glossary" (merged from `mvp-27-clerk-delete-retry` in 7ff9487 "Merge MVP issue 27: a failed Clerk call during Delete account no longer leaves the Clerk account behind…")
