# 03 — Onboarding

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

After sign-up, the Dashboard walks a new User through onboarding before Connect Telegram: the name the Companion should use and the AI notice ("it's an AI, not therapy or medical care, in an emergency use Helplines") with an "I understand" tick, "What brings you here?" (choice chips plus optional free text), User Memory consent (plain explanation, on by default, clear toggle), country, and time zone. These are saved on the User and editable later in a preferences page. The Check-in step is added in issue 11.

Country is asked as a plain question with no reason given; it exists so a Crisis Reply shows the right Helplines, and that stays internal. There are no conversation style, philosophy or tradition settings — the Companion adapts to each User, and Knowledge is admin-managed (see `CONTEXT.md`, Persona).

## Design

- `docs/design/zeph-product.html`: Onboarding (all steps except Check-ins), Account and privacy (Profile section)

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [x] A new User sees the onboarding steps in order and cannot reach Connect Telegram without acknowledging the AI notice
- [x] The AI notice wording and the User Memory explanation come from platform settings (seeded), not code
- [x] User Memory is on by default and can be turned off during onboarding
- [x] Country and time zone are required and saved; country is pre-filled from the browser and the screen gives no reason for asking
- [x] The User's name and "What brings you here?" answers are saved
- [x] Onboarding has no conversation style, philosophy amount or traditions controls
- [x] A preferences page lets the User change their name, User Memory on/off, country and time zone at any time
- [x] The AI notice is also visible on the Dashboard after onboarding
- [x] Seam 1 tests cover the onboarding API (save, validation, required AI notice)
- [x] Seam 3 tests (Vitest + RTL) cover the onboarding steps and preferences page with a mocked API client
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/01-walking-skeleton.md`

## Comments

**2026-11-11 — implemented on branch `feat/03-onboarding`.**

Decisions:
- New User fields: `name`, `onboarding_reasons` (list of picked chips), `onboarding_note` (free text), `country` (two-letter code), `time_zone` (IANA name), `ai_notice_acknowledged_at`, `user_memory_enabled` (on by default), `onboarding_completed_at`. Migration `0003`.
- API: `GET /api/me` returns the profile; `PUT /api/onboarding` saves all answers at once (refused with 422 unless the AI notice is acknowledged; name, country and time zone are checked); `PATCH /api/me` changes name, User Memory, country or time zone; `GET /api/platform-content` gives the Admin-managed wording. Checks live in the core `UserService`.
- New seeded settings: `ai_notice`, `ai_notice_short` (sidebar), `user_memory_explanation` (blank line = new paragraph), `onboarding_reason_choices`.
- Onboarding is 5 steps: Hello, Intentions, Location, Memory, Telegram. Answers are saved when leaving the Memory step. Check-ins step comes in issue 11.
- Every Dashboard page is behind a gate: a User who hasn't finished onboarding is sent to `/onboarding`. A User who has finished is sent from `/onboarding` to `/`.
- Country is pre-filled from the browser language's region (e.g. `en-SG`); if the language has no region, the User picks. Time zone comes from the browser.
- Preferences live on a new Account & privacy page (Profile section, plus a User Memory switch that saves straight away). The design puts the switch on the Memories page; it can move there in issue 06.
- Added `tzdata` so time zone checks work in the slim Docker image.

Caveats / follow-ups:
- "Save and finish later" from the design was left out: with the gate, it would only send the User back to onboarding.
- The gate is in the Dashboard only. The backend still issues connection tokens to a User who hasn't onboarded.
- Name, reasons and User Memory on/off are saved but not used in chat yet (later issues: User Memory, response composition).
- The sidebar AI notice is empty if the wording fails to load.
- Some step wording is still in code (headings, the "I understand…" line). Only the notice, memory explanation and chips are settings.
- The seeded wording uses straight quotes (`I'm`); the design uses curly ones.
- Review judgement calls not acted on: the load/error/"Try again" pattern repeats in three components; profile fields are listed in many layers; country and time zone are plain strings.
- Live run: Clerk's bot check blocks headless sign-up, so the run used a test user made through Clerk's Backend API and a sign-in ticket. The test user was deleted afterwards.

Evidence:
- Seam 1: `tests/test_onboarding.py` (13 tests: save, validation, required AI notice, preferences).
- Seam 3: `OnboardingFlow.test.tsx`, `AccountSettings.test.tsx`, `OnboardingGate.test.tsx`, `SidebarAiNotice.test.tsx`, plus helper tests.
- `make check`: Python 38 passed; web 38 passed; ruff, mypy, eslint, prettier, tsc clean.
- `/run`: `/connect-telegram` redirected to `/onboarding`; Continue stayed disabled until name and tick; country pre-filled `SG`, time zone `Asia/Singapore`; Memory on by default, turned off; saved and reached the Telegram step with a live link; Account page changes (name, GB, Europe/London, Memory back on) kept after reload; database row matched.

## Completion

- Completed: 2026-11-11
- Commit: <to be filled in manually>
