# 20 — Onboarding must be finished before Telegram can be linked

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

Today only the Dashboard makes a User finish onboarding before they reach the Telegram link. The backend does not check. A signed-in User can ask the API for a connection token directly, link Telegram and start chatting without ever acknowledging the AI Notice. The Companion would then have no name, country or time zone for them.

Close the gap in the backend:

- Asking for a new connection token before onboarding is finished is refused with a clear error. Nothing is created.
- If a User who has not finished onboarding sends `/start <token>` in Telegram with a token that already exists (for example, one made before this fix), nothing is linked. The token stays unused, and the Companion replies asking them to finish setting up on the Dashboard first. The reply text is a new seeded platform setting that Admins can edit, like the other Telegram connection replies.
- After onboarding, nothing changes: the onboarding flow's Telegram step and the Connect Telegram page work as before.

## Acceptance criteria

- [x] Asking for a connection token before onboarding is finished is refused with a clear error, and no token is saved.
- [x] Once onboarding is finished, asking for a connection token works as before.
- [x] `/start <token>` from a User who has not finished onboarding links nothing, leaves the token unused, and replies with the new "finish onboarding first" setting.
- [x] The new reply is seeded from platform settings and can be edited by Admins.
- [x] Onboarding's Telegram step and the Connect Telegram page still show a working link for an onboarded User.
- [x] Tests cover each case above; all checks pass.
- [x] Verified in the running app: a non-onboarded User is refused, and an onboarded User can still link Telegram.

## Blocked by

None - can start immediately.

## Comments

### 2026-11-13 — plan (branch `mvp-20-onboarding-before-telegram`)

- `TelegramConnectionService.create_token` takes the `User` and raises `OnboardingNotFinishedError` before onboarding; the Dashboard API turns it into a 409 "Finish onboarding before connecting Telegram." and saves nothing.
- `handle_start` checks the token's User after the token is found active and before it is claimed or rejected. A User who hasn't onboarded gets the new `onboarding_unfinished_reply`; the token stays unused.
- `User.has_finished_onboarding` holds the check in one place.
- The new reply is a seeded platform setting and is on the admin Settings page under Wording. It must keep `{dashboard_url}`. No migration: the seed loader adds the new key on start.

### 2026-11-13 — evidence

- Checks: ruff, ruff format, mypy pass; pytest 441 passed; web lint, prettier, typecheck pass; vitest 293 passed.
- Tests, `tests/test_telegram_connection.py`: a token is refused with 409 before onboarding and none is saved; a token is issued with 201 after onboarding; `/start` with an existing token from a User who hasn't onboarded links nothing, leaves the token active and sends the seeded reply. `tests/test_admin_settings.py`: an Admin sees the seeded reply, edits it, and the edited text is what `/start` sends; a value without `{dashboard_url}` is refused. Vitest: the Settings page shows and saves the reply.
- The shared test helper `create_connection_token` now marks the test User onboarded in the database first (onboarding times only, so names and Memory Items in other tests stay as they were). `onboarding_answers` moved into `tests/telegram_helpers.py`.
- `/run` (own stack `mvp20` on ports 3001/8001/5433, so the other agent's stack was left alone; real Clerk sign-in, real Telegram replies to the owner's chat):
  - Non-onboarded User: `/connect-telegram` sent them to `/onboarding`; `POST /api/telegram-connection/tokens` gave 409 "Finish onboarding before connecting Telegram."; 0 tokens saved.
  - An old token `OLD1-TOKN` written to the database for that User, then `/start OLD1-TOKN` sent to the webhook: 200, token still unused, 0 Telegram Connections, no errors in the logs.
  - Onboarding finished in the browser: step 6 "Let's meet on Telegram." showed a working `t.me/Zeph_07_bot?start=…` link and QR code; the Connect Telegram page showed the same; no page errors.
  - Onboarded User: `POST …/tokens` gave 201 with a new token; `/start` with it linked Telegram (`zaffere`) and that token became used.
  - Admin Settings page: the "Finish onboarding first" reply showed its seeded text, was edited and saved (database value and `updated_by` changed); saving a value without `{dashboard_url}` showed "The "Finish onboarding first" reply must include {dashboard_url}, the link to the Dashboard."
  - The Clerk test user and the `mvp20` stack with its database were removed. A first `/start` sent before the old token was saved (a shell slip) gave the owner's chat one extra "link expired" reply.

### Review

- Standards: no hard breaks. Took the suggestion to add `User.has_finished_onboarding`. Kept the `CompanionTestClient` test seam: the token helper runs behind about 160 test calls that don't take the `engine` fixture.
- Spec: the reply was first only seeded, which didn't meet "can be edited by Admins". Fixed by putting it on the admin Settings page.

### Decisions

- Refusal is 409 Conflict. The Dashboard never shows it in normal use, because it sends Users through onboarding first; if it did happen, the card's normal "couldn't make a link" state shows.
- An expired or used token from a User who hasn't onboarded still gets the "link expired" reply; the onboarding check only runs for a token that would otherwise work.
- When the Telegram account already belongs to another User and the token's User hasn't onboarded, they get the onboarding reply and the token is not marked "connected elsewhere".
- Follow-up, not done here: the other Telegram connection replies (`welcome_message`, `connection_token_invalid_reply`, `telegram_connected_elsewhere_reply`, `unknown_telegram_user_reply`) are seeded but still not on the admin Settings page.

## Completion

- Completed: 2026-11-13
- Commit: <to be filled in after merge>
