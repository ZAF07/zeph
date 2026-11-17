# 02 — Stop calling Clerk on every page load

Status: ready-for-agent

## What to build

On every full page load, the Dashboard shell asks Clerk's Backend API who the signed-in person is (`currentUser()`), only to show their name and email in the sidebar. That call takes 0.37–0.54 s from here, so signed-in pages return their HTML in ~350 ms while a public page (sign-in) returns in ~10 ms.

The backend's `/me` already returns the User's name and email, and every Dashboard page already loads `/me`. Show the sidebar's name and email from `/me`, and keep sending signed-out visitors to sign-in using Clerk's local session check (no network call). Clerk stays inside the auth helper and auth files only (CLAUDE.md).

Out of scope: Clerk's own browser sign-in step (~300 ms, `/v1/environment` and `/v1/client`) — it can't be avoided while using Clerk.

## Acceptance criteria

- [ ] No Clerk Backend API call happens while rendering a Dashboard page
- [ ] Measured in the running stack: signed-in page HTML returns in under 100 ms (was ~350 ms); paste the numbers
- [ ] The sidebar shows the right name and email, with a sensible placeholder while `/me` loads
- [ ] Signed-out visitors to any Dashboard page still land on sign-in
- [ ] Tests cover the sidebar showing name and email from `/me`
- [ ] `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test` pass

## Blocked by

None - can start immediately

## Comments
