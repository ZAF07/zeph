# 02 — Stop calling Clerk on every page load

Status: completed

## What to build

On every full page load, the Dashboard shell asks Clerk's Backend API who the signed-in person is (`currentUser()`), only to show their name and email in the sidebar. That call takes 0.37–0.54 s from here, so signed-in pages return their HTML in ~350 ms while a public page (sign-in) returns in ~10 ms.

The backend's `/me` already returns the User's name and email, and every Dashboard page already loads `/me`. Show the sidebar's name and email from `/me`, and keep sending signed-out visitors to sign-in using Clerk's local session check (no network call). Clerk stays inside the auth helper and auth files only (CLAUDE.md).

Out of scope: Clerk's own browser sign-in step (~300 ms, `/v1/environment` and `/v1/client`) — it can't be avoided while using Clerk.

## Acceptance criteria

- [x] No Clerk Backend API call happens while rendering a Dashboard page
- [x] Measured in the running stack: signed-in page HTML returns in under 100 ms (was ~350 ms); paste the numbers
- [x] The sidebar shows the right name and email, with a sensible placeholder while `/me` loads
- [x] Signed-out visitors to any Dashboard page still land on sign-in
- [x] Tests cover the sidebar showing name and email from `/me`
- [x] `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test` pass

## Blocked by

None - can start immediately

## Comments

Done. The shell no longer calls Clerk's `currentUser()`. `web/src/lib/auth/server.ts` now has `isSignedIn()`, which uses Clerk's `auth()` and reads the session from the request with no network call. `(dashboard)/layout.tsx` redirects to `/sign-in` when it is false, and the middleware's `auth.protect()` is unchanged. The sidebar's name, initial, email and Admin badge come from the new `SidebarAccount` client component, which reads `useMe()` (the `/me` query every page already loads). It shows grey bars while `/me` loads. A User with no name is shown by their email.

Evidence:

- **No Clerk Backend API call:** `grep -rnE "currentUser|clerkClient" web/src` finds nothing. Clerk is imported only in `middleware.ts`, `lib/auth/*` and the sign-in/up pages.
- **Timing, measured in the running stack:** production builds (`pnpm build && pnpm start`) on the host against the worktree backend, same signed-in Admin browser profile, 6 loads per page (first is warm-up), document `responseEnd - requestStart`:

  | Page | Before (old code) ms | After ms |
  | --- | --- | --- |
  | `/` | 645, 332, 330, 315, 330, 322 | 31, 12, 11, 12, 10, 10 |
  | `/memories` | 322, 969, 324, 327, 326, 310 | 11, 12, 11, 10, 11, 8 |
  | `/check-ins` | 326, 321, 339, 313, 340, 377 | 8, 8, 9, 9, 8, 9 |
  | `/account` | 367, 420, 399, 1013, 307, 321 | 8, 8, 7, 9, 9, 8 |
  | `/admin/users` | 309, 313, 326, 330, 319, 317 | 9, 8, 8, 8, 8, 8 |
  | `/sign-in` (public) | 9 | 8 |

  Signed-in pages now match the public sign-in page. The Docker stack still runs `next dev`, where pages take ~150–400 ms for reasons unrelated to Clerk (sign-in itself takes ~90 ms there). Issue 01 (production build) covers that.
- **Sidebar:** in the running stack, the sidebar foot read "R | Run check | ADMIN | run-check-…+clerk_test@example.com", which matches the `users` row (`name = Run check`, `role = admin`). With `/me` held back, the grey placeholder bars and the "Loading your account" screen-reader text showed.
- **Signed out:** a fresh browser visiting `/`, `/memories` and `/admin/users` landed on `/sign-in` each time.
- **Tests:** `web/src/components/SidebarAccount.test.tsx` covers name/initial/email from `/me`, email shown as the name, the placeholder and the Admin badge (4 passed).
- **Checks:** `pnpm lint` is clean, `pnpm format:check` passes, `pnpm typecheck` is clean, and `pnpm test` passes 66 files and 459 tests.

Code review (standards and spec) found no blocking issues. Minor notes, left as is: the email-for-name fallback is written slightly differently from the admin pages' "This User" fallback (they can't differ for a Clerk account with an email), and `isSignedIn()` is covered by the run check rather than a unit test.

## Completion

- Completed: 2026-11-17
- Commit: <to be filled in after merge>
