# 18 — Redesign: OnboardingGate old theme and unused SettingLabel

Status: in-progress

Lane: follow-up from issue 15. README slice: 10 (shared states).

## Parent

`.scratch/redesign/PRD.md`

## What to build

Issue 15's old-theme search left two files outside the admin pages:

- `OnboardingGate` (wraps every signed-in Dashboard page) still draws its loading box and its couldn't-load box in the old theme (`bg-subtle`, `bg-danger-tint`, `border-danger-line`, `text-danger-deep`). Use the shared state parts instead: `LoadingPanel` for loading and `LoadFailed` for couldn't load, keeping Try again.
- `SettingLabel.tsx` is imported nowhere and still uses old-theme classes. Delete it.

## Acceptance criteria

- [ ] The old-theme search over `web/src` finds nothing (search shown).
- [ ] `OnboardingGate` shows `LoadingPanel` while loading and `LoadFailed` with Try again when it can't load; its tests pass.
- [ ] `SettingLabel.tsx` is gone and nothing breaks (`pnpm typecheck`, `pnpm test`).
- [ ] A `/run` check shows the gate's loading and couldn't-load states in the new look, at 1280 and 390.

## Comments
