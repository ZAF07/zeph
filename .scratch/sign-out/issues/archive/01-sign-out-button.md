# 01 — Sign out button on Home

Status: completed

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

- [x] Home shows a "Sign out" button next to "Talk to Zeph"
- [x] It shows when the User has no Telegram Connection
- [x] Clicking it signs the User out and lands on `/sign-in`; going back to `/` asks them to sign in again
- [x] It still fits at 390px wide with no sideways scroll
- [x] Vitest + React Testing Library tests cover: button shown with and without a Telegram Connection, click calls sign out with `/sign-in`
- [x] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` pass
- [x] Verified in the running app via `/run`

## Blocked by

None.

## Comments
**2026-11-18: implemented, reviewed and verified** on branch `sign-out-01-button`.

Done and verified: every acceptance criterion.

- New `SignOutButton` (`web/src/components/SignOutButton.tsx`): secondary style, calls `useSignOut()("/sign-in")`. `DashboardHome` puts it in one `flex flex-wrap gap-3` group with "Talk to Zeph", outside the Telegram check.
- Tests (`web/src/components/DashboardHome.test.tsx`): the button shows with a Telegram Connection and without one; a new test clicks it and checks sign out was called with `/sign-in`. They were red before the change (3 failed) and green after (13 passed).
- Checks: eslint, prettier and tsc clean; vitest 68 files, 484 passed.

Running app (worktree stack, web on 3010, real Clerk dev), signed in as a temporary Clerk test User:
- No Telegram Connection: Home shows "Sign out" in the header, no "Talk to Zeph". No page errors. scrollWidth 1280 at 1280px, 390 at 390px.
- Added a fake Telegram Connection row (ids 990000001) to the worktree database: "Talk to Zeph" (black) and "Sign out" (outlined) sit side by side at 1280px and at 390px. scrollWidth 390 at 390px, so no sideways scroll.
- Clicked "Sign out": landed on `http://localhost:3010/sign-in`. Opening `/` again redirected to Clerk sign-in (`…accounts.dev/sign-in?redirect_url=http://localhost:3010/`). No page errors.
- Clean-up: the test User was deleted from Clerk and the database; the fake Telegram row went with it (count 0 afterwards).

Review (`/code-review`):
- Spec: met, no scope creep. Noted that the click doesn't catch a failed Clerk sign-out; left, same as the delete-account flow.
- Standards: no violations. Noted `"/sign-in"` is now written in four places; left, as it was already repeated and the new button matches the existing callers.

## Completion

- Completed: 2026-11-18
- Commit: <filled in after merge>
