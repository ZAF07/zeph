# 18 — Redesign: OnboardingGate old theme and unused SettingLabel

Status: completed

Lane: follow-up from issue 15. README slice: 10 (shared states).

## Parent

`.scratch/redesign/PRD.md`

## What to build

Issue 15's old-theme search left two files outside the admin pages:

- `OnboardingGate` (wraps every signed-in Dashboard page) still draws its loading box and its couldn't-load box in the old theme (`bg-subtle`, `bg-danger-tint`, `border-danger-line`, `text-danger-deep`). Use the shared state parts instead: `LoadingPanel` for loading and `LoadFailed` for couldn't load, keeping Try again.
- `SettingLabel.tsx` is imported nowhere and still uses old-theme classes. Delete it.

## Acceptance criteria

- [x] The old-theme search over `web/src` finds nothing (search shown).
- [x] `OnboardingGate` shows `LoadingPanel` while loading and `LoadFailed` with Try again when it can't load; its tests pass.
- [x] `SettingLabel.tsx` is gone and nothing breaks (`pnpm typecheck`, `pnpm test`).
- [x] A `/run` check shows the gate's loading and couldn't-load states in the new look, at 1280 and 390.

## Comments
- 2026-11-19 — Done (branch `redesign-18-onboarding-gate-old-theme`).
  - `OnboardingGate`: loading is `LoadingPanel` (banner shape, "Loading your Dashboard"); couldn't load is `LoadFailed` with the old words split into title "We couldn’t load this" and body "Nothing you’ve shared is lost.", with Try again. `SettingLabel.tsx` deleted (nothing imported it).
  - Old-theme search over `web/src` (same search as issue 15): only `TextChangesReview.tsx:56 bg-black/60` (the dialog backdrop; `black` is a token). Nothing else.
  - Checks: `pnpm typecheck` (tsc --noEmit, no errors), `pnpm lint` (no errors), `pnpm format:check` (All matched files use Prettier code style!), `pnpm test` (Test Files 114 passed · Tests 711 passed). No Python changed.
  - Tests: new "shows the loading panel while it checks" and "loads again on Try again after the check fails"; the couldn't-load test also checks the alert's words.
  - /run (worktree stack, signed-in User, `/check-ins`, `/api/me` held back then failed in Playwright): at 1280 and 390 the loading panel showed, then the couldn't-load box, and Try again loaded the page. No page errors. Screenshots: `archive/18-screenshots/`.
  - Choice for Zaf: the banner shape matches Home, Check-ins and Memories (they start with a banner). On other pages (Connect Telegram, Account, Plan, admin) the shape changes when the page arrives; admin pages then show AdminGate's card panel briefly. The card shape would instead jump on Home.

## Completion

- Completed: 2026-11-19
- Commit: merge `9301fa9` into main — "Merge redesign issue 18: OnboardingGate's loading and couldn't-load states use the shared LoadingPanel and LoadFailed (no old theme left in web/src); unused SettingLabel removed"
  - Branch `redesign-18-onboarding-gate-old-theme`:
    - `10d247b` Redesign 18: OnboardingGate uses the shared LoadingPanel and LoadFailed instead of old-theme boxes; unused SettingLabel removed
    - `258e9d9` Redesign 18: Try again test; evidence recorded, issue completed and archived, screenshots at both widths
