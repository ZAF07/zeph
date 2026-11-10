# 03 — Onboarding

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

After sign-up, the Dashboard walks a new User through onboarding before Connect Telegram: the AI notice ("it's an AI, not therapy or medical care, in an emergency use Helplines") with an "I understand" tick, User Memory consent (plain explanation, on by default, clear toggle), country, and time zone. These are saved on the User and editable later in a preferences page. The Check-in step is added in issue 11.

## Acceptance criteria

- [ ] A new User sees the onboarding steps in order and cannot reach Connect Telegram without acknowledging the AI notice
- [ ] The AI notice wording and the User Memory explanation come from platform settings (seeded), not code
- [ ] User Memory is on by default and can be turned off during onboarding
- [ ] Country and time zone are required and saved
- [ ] A preferences page lets the User change User Memory on/off, country and time zone at any time
- [ ] The AI notice is also visible on the Dashboard after onboarding
- [ ] Seam 1 tests cover the onboarding API (save, validation, required AI notice)
- [ ] Seam 3 tests (Vitest + RTL) cover the onboarding steps and preferences page with a mocked API client
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/01-walking-skeleton.md`
