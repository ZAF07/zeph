# 01 — Sign out button on Home

Status: ready-for-agent

## Parent

None (small, well-understood work; no PRD).

## What to build

A signed-in User can't sign out of the Dashboard today. Add a "Sign out" button on the Home page, next to the "Talk to Zeph" button.

- Clicking it signs the User out and takes them to `/sign-in`.
- It always shows for a signed-in User, even when there's no Telegram Connection (when "Talk to Zeph" is hidden).
- It uses the secondary button style, so "Talk to Zeph" stays the main action.
- It uses the existing `useSignOut` helper in `web/src/lib/auth/client.ts`, so Clerk stays inside the auth files.
- It lives in its own component (`SignOutButton`), used by `DashboardHome`.

## Acceptance criteria

- [ ] Home shows a "Sign out" button next to "Talk to Zeph"
- [ ] It shows when the User has no Telegram Connection
- [ ] Clicking it signs the User out and lands on `/sign-in`; going back to `/` asks them to sign in again
- [ ] It still fits at 390px wide with no sideways scroll
- [ ] Vitest + React Testing Library tests cover: button shown with and without a Telegram Connection, click calls sign out with `/sign-in`
- [ ] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` pass
- [ ] Verified in the running app via `/run`

## Blocked by

None.

## Comments
