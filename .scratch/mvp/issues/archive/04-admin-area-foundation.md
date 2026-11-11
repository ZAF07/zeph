# 04 — Admin area foundation

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

The admin area of the Dashboard, plus the role model behind it. A User whose email is in the initial Admin emails config becomes an Admin on first sign-in. Admins can promote and demote other Users, edit platform settings (Persona, prompts for each core service, the model each core service uses, the Conversation quiet gap), and see a User list with activity counts but never message content. The backend checks the Admin role on every admin request.

The admin area lives in the same Dashboard shell as the User pages: an "Admin" sidebar group shown only to Admins, using the same design tokens with a denser layout for tables and editors.

This slice also creates the reusable settings editing pattern that later slices extend.

## Design

- `docs/design/zeph-admin.html`: Users, Persona, Prompts and models, Platform settings (and the Admin sidebar group they share)

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [x] Signing in with an email from the initial Admin emails config gives the Admin role; the role is stored in our database, not Clerk
- [x] Admins can promote and demote Users; demoting the last Admin is refused
- [x] Non-Admins calling any admin API get refused by the backend, and the admin area is hidden from them
- [x] Admin pages sit under an Admin sidebar group in the same Dashboard shell
- [x] Admins can edit the Persona, each core service's prompt, the model each core service uses, and the quiet gap; changes take effect on the next message without a restart
- [x] The User list shows signup date, Telegram Connection status and message/Conversation counts, never message text
- [x] Seam 1 tests cover bootstrap, role changes, last-Admin protection, role checks on admin endpoints, and a settings change affecting the next reply
- [x] Seam 3 tests cover the admin pages with a mocked API client
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/02-chat-with-the-companion.md`

## Comments

**2026-11-11 — implemented on branch `feat/04-admin-area-foundation`.**

Decisions:
- Role is a `role` column on `users` (`user` / `admin`), migration `0004`. Also `platform_settings.updated_by`, so pages show "Last saved … by …".
- Bootstrap: a new User whose email is in `INITIAL_ADMIN_EMAILS` (any case) becomes an Admin. A listed **existing** User also becomes an Admin on sign-in, but only while the platform has no Admin at all, so an account made before the config was set still gets in. Once there is an Admin, demotions stick.
- Last-Admin protection is done in one locked database step, so two Admins demoting each other at once can't leave zero Admins.
- Admin API lives under `/api/admin` with the Admin check on the router itself: every route added there is refused (403) for non-Admins. Endpoints: `GET /users`, `PUT /users/{id}/role`, `GET/PATCH /settings`, `GET /core-services`.
- Reusable settings pattern: the core lists editable settings with a rule each (`EDITABLE_SETTINGS` in `core/platform_settings.py`: text, whole number with range, or model from the seeded `available_models`). `PATCH /api/admin/settings` checks every value and saves all or nothing; refusals are plain words. Core services are listed in `CORE_SERVICES` (only Response composition today); later slices add theirs and their pages pick keys. On the web: `useAdminSettings` hook, `lastSavedNote`, `LoadFailed`.
- Pages: Users (search, filters, make/remove Admin), Persona, Prompts & models, Platform settings (quiet gap, plus AI notice, short AI notice and Memory explanation wording, which already were settings).
- "Messages sent" counts messages the User sent, not the Companion's replies.
- Admin pages sit in `(dashboard)/admin` with a wider column; User pages moved to a `(dashboard)/(user)` route group (URLs unchanged).
- The Dashboard checks only input shape (whole number, not blank); ranges and model choices are the backend's and its message is shown.

Caveats / follow-ups:
- Only Response composition appears on Prompts & models. Safeguard (05), post-conversation processing (06) and Check-ins (11) must add an entry to `CORE_SERVICES`, `EDITABLE_SETTINGS` and the seed.
- The other Platform settings rows in the design (daily limit, ignore threshold, retention, web search, limit reply) belong to issues 09/11/13/14.
- Persona versions ("v12") and "Start from default" from the design were left out; there is no setting history.
- Fixed a shipped styling bug in passing: global `a` colours were unlayered CSS and overrode Tailwind classes (blue sidebar links, blue text on the black Connect Telegram button). They now sit in `@layer base`.
- `INITIAL_ADMIN_EMAILS` in `.env` is still empty; set it to the owner's email and restart. The owner's existing account will become Admin on next sign-in (no Admin exists yet).
- Admin role is hidden client-side via `getMe` (sidebar and gate each ask); the backend is the real check.
- Review judgement calls not acted on: load/error pattern still repeats across components; setting labels appear in both backend and form; test helpers keep one-line docstrings like the existing ones.
- Live run did not send a real Telegram message after editing; "applies to the next message" is proven by seam 1 tests and the backend reading settings on every call.

Evidence:
- Seam 1: `tests/test_admin.py` (10: bootstrap, case, no-Admin fallback, user list without text, 401/403, promote/demote, last Admin, step down, unknown User, concurrent demotion), `tests/test_admin_settings.py` (16: read, who/when saved, next reply uses new persona/prompt/model, shorter quiet gap, 8 invalid values, plain-words refusal, all-or-nothing, core services, every admin endpoint 403), plus a config test.
- Seam 3: `AdminGate`, `SidebarNav`, `AdminUsers`, `PersonaEditor`, `PromptsAndModels`, `PlatformSettingsForm` tests, plus `dates` and `settings` helper tests.
- `make check`: Python 65 passed; web 74 passed; ruff, mypy, eslint, prettier, tsc clean.
- `/run` (Docker Compose, real Clerk test users made via Clerk's Backend API and sign-in tickets, deleted afterwards): listed email got `admin`; plain User got 403 on admin API and was sent from `/admin/users` to `/` with no Admin group; Admin saw the 4 admin links, the user table with counts and no text; removing the only Admin showed the refusal; promote → User's admin API 200, demote → 403; Persona, model and quiet gap saved and read back from the backend; quiet gap 2 refused with the plain message. Seeded values restored afterwards.

## Completion

- Completed: 2026-11-11
- Commit: <to be filled in manually>
