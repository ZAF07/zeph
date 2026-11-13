# 20 — Onboarding must be finished before Telegram can be linked

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

Today only the Dashboard makes a User finish onboarding before they reach the Telegram link. The backend does not check. A signed-in User can ask the API for a connection token directly, link Telegram and start chatting without ever acknowledging the AI Notice. The Companion would then have no name, country or time zone for them.

Close the gap in the backend:

- Asking for a new connection token before onboarding is finished is refused with a clear error. Nothing is created.
- If a User who has not finished onboarding sends `/start <token>` in Telegram with a token that already exists (for example, one made before this fix), nothing is linked. The token stays unused, and the Companion replies asking them to finish setting up on the Dashboard first. The reply text is a new seeded platform setting that Admins can edit, like the other Telegram connection replies.
- After onboarding, nothing changes: the onboarding flow's Telegram step and the Connect Telegram page work as before.

## Acceptance criteria

- [ ] Asking for a connection token before onboarding is finished is refused with a clear error, and no token is saved.
- [ ] Once onboarding is finished, asking for a connection token works as before.
- [ ] `/start <token>` from a User who has not finished onboarding links nothing, leaves the token unused, and replies with the new "finish onboarding first" setting.
- [ ] The new reply is seeded from platform settings and can be edited by Admins.
- [ ] Onboarding's Telegram step and the Connect Telegram page still show a working link for an onboarded User.
- [ ] Tests cover each case above; all checks pass.
- [ ] Verified in the running app: a non-onboarded User is refused, and an onboarded User can still link Telegram.

## Blocked by

None - can start immediately.
