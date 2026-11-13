# 27 — A failed Clerk call during Delete account leaves the Clerk account behind

Status: ready-for-agent

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

- [ ] If Clerk fails during Delete account, the User's data is still deleted, the User is signed out, and the page doesn't show an error
- [ ] The Clerk account is deleted on a later scheduler tick once Clerk works again, and the entry is then removed
- [ ] Repeated Clerk failures keep the entry and are logged, without stopping other scheduled work
- [ ] The pending list holds no personal data beyond the auth ID
- [ ] Tests cover: Clerk fails then the retry succeeds; Clerk returns 404 on retry; the scheduler keeps going when a retry fails
- [ ] `/run`: with Clerk made to fail, Delete account signs the User out; once Clerk is fixed, the next tick deletes the Clerk account
- [ ] `make check` passes (`pytest`, `ruff`, `ruff format`, `mypy`, `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`)

## Comments
