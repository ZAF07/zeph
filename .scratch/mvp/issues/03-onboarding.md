# 03 — Onboarding

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

After sign-up, the Dashboard walks a new User through onboarding before Connect Telegram: the name the Companion should use and the AI notice ("it's an AI, not therapy or medical care, in an emergency use Helplines") with an "I understand" tick, "What brings you here?" (choice chips plus optional free text), User Memory consent (plain explanation, on by default, clear toggle), country, and time zone. These are saved on the User and editable later in a preferences page. The Check-in step is added in issue 11.

Country is asked as a plain question with no reason given; it exists so a Crisis Reply shows the right Helplines, and that stays internal. There are no conversation style, philosophy or tradition settings — the Companion adapts to each User, and Knowledge is admin-managed (see `CONTEXT.md`, Persona).

## Design

- `docs/design/zeph-product.html`: Onboarding (all steps except Check-ins), Account and privacy (Profile section)

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [ ] A new User sees the onboarding steps in order and cannot reach Connect Telegram without acknowledging the AI notice
- [ ] The AI notice wording and the User Memory explanation come from platform settings (seeded), not code
- [ ] User Memory is on by default and can be turned off during onboarding
- [ ] Country and time zone are required and saved; country is pre-filled from the browser and the screen gives no reason for asking
- [ ] The User's name and "What brings you here?" answers are saved
- [ ] Onboarding has no conversation style, philosophy amount or traditions controls
- [ ] A preferences page lets the User change their name, User Memory on/off, country and time zone at any time
- [ ] The AI notice is also visible on the Dashboard after onboarding
- [ ] Seam 1 tests cover the onboarding API (save, validation, required AI notice)
- [ ] Seam 3 tests (Vitest + RTL) cover the onboarding steps and preferences page with a mocked API client
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/01-walking-skeleton.md`
