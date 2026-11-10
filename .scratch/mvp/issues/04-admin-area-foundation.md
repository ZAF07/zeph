# 04 — Admin area foundation

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

The admin area of the Dashboard, plus the role model behind it. A User whose email is in the initial Admin emails config becomes an Admin on first sign-in. Admins can promote and demote other Users, edit platform settings (Persona, prompts for each core service, the model each core service uses, the Conversation quiet gap), and see a User list with activity counts but never message content. The backend checks the Admin role on every admin request.

This slice also creates the reusable settings editing pattern that later slices extend.

## Acceptance criteria

- [ ] Signing in with an email from the initial Admin emails config gives the Admin role; the role is stored in our database, not Clerk
- [ ] Admins can promote and demote Users; demoting the last Admin is refused
- [ ] Non-Admins calling any admin API get refused by the backend, and the admin area is hidden from them
- [ ] Admins can edit the Persona, each core service's prompt, the model each core service uses, and the quiet gap; changes take effect on the next message without a restart
- [ ] The User list shows signup date, Telegram Connection status and message/Conversation counts, never message text
- [ ] Seam 1 tests cover bootstrap, role changes, last-Admin protection, role checks on admin endpoints, and a settings change affecting the next reply
- [ ] Seam 3 tests cover the admin pages with a mocked API client
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/02-chat-with-the-companion.md`
