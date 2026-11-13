# 05 — Settings in Chat as a Feature

Status: ready-for-agent

## Parent

`.scratch/features/PRD.md`

## What to build

Settings in Chat (ADR 0006) joins the Feature list, ready for a lower plan that only allows settings on the Dashboard.

- When it doesn't work for a User, the reply isn't offered the settings tools, except Delete My Data, which is always offered and keeps its confirmation word.
- The "not available on your account" note tells the Companion to point the User to the Dashboard link when they ask to change a setting.
- The Safeguard still runs first, unchanged.

## Acceptance criteria

- [ ] With Settings in Chat off, asking in chat to pause Check-ins (or any other setting) changes nothing and the reply points to the Dashboard link
- [ ] With Settings in Chat off, "delete my data" in chat still works with its confirmation word
- [ ] With it on, every chat setting works as before
- [ ] It shows on the Features page and per-User panel with its switch and last change
- [ ] Seam 1 tests cover on, off and Delete My Data; seam 3 tests cover the new row
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/features/issues/01-features-and-web-search-switch.md`
