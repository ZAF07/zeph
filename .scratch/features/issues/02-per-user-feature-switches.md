# 02 — Per-User Feature switches and the Admin Features panel

Status: ready-for-agent

## Parent

`.scratch/features/PRD.md`

## What to build

Admins can set any Feature to default, on or off for one User, shown with Web Search.

- Per-User switch storage: a row only when it isn't "default" (on/off, changed by, changed at); setting back to default removes it.
- The rule: the per-User switch if on or off, otherwise the switch for everyone. Per-User "on" gives a User a Feature that is off for everyone.
- Each row on the admin Users page gets a Features button that opens a panel: one row per Feature with default/on/off, whether it works for that User right now, why ("Off: turned off for everyone", "Off: turned off for this User", "On: turned on for this User"), and the last change. Keep the panel uncluttered.
- Delete My Data keeps per-User switches; Account Deletion removes them.

## Acceptance criteria

- [ ] An Admin can set Web Search to default, on or off for one User from the Users page panel
- [ ] Per-User off stops Web Search for that User only; per-User on gives it to that User while it is off for everyone; default follows the switch for everyone
- [ ] The panel shows whether each Feature works now, the reason and the last change (who, when)
- [ ] Delete My Data keeps the User's switches; Account Deletion removes them
- [ ] Non-Admins can't call the per-User endpoints
- [ ] Seam 1 tests cover the rule, reasons, last change and deletion cases; seam 3 tests cover the panel
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/features/issues/01-features-and-web-search-switch.md`
