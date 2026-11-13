# 01 — Features, with Web Search as the first one

Status: ready-for-agent

## Parent

`.scratch/features/PRD.md`

## What to build

The tracer bullet for Features: one Feature (Web Search) with its switch for everyone, end to end.

- A Features core service that answers "does this Feature work for this User?" and lists the switches for everyone with their last change. Other core services ask it instead of reading switches themselves.
- Storage for the switch for everyone (on/off, changed by, changed at), seeded on. A migration copies the current `web_search_enabled` setting into the Web Search switch and removes the setting, so it leaves the Settings page.
- A new admin Features page: one row per Feature with name, short description, switch and last change (Admin's email and date). Keep it clean and easy to scan; more Features join it in later issues.
- The reply is offered the Web Search tools only when Web Search works for the User.
- When any Feature doesn't work for a User, the reply instructions get a short Admin-managed note (new platform setting) naming those Features and telling the Companion to say plainly they aren't available on their account (and, for settings, to use the Dashboard at `{dashboard_url}`). Later Features reuse this note.
- The Safeguard, Crisis Reply, AI Notice, Delete My Data and seeing own data never check a switch.

## Acceptance criteria

- [ ] The admin Features page lists Web Search with its switch for everyone and last change; only Admins can see or change it
- [ ] The Web Search switch is gone from the Settings page, and an existing install keeps its old on/off value after the migration
- [ ] With Web Search off for everyone, replies get no Web Search tools and the "not available on your account" note; turning it back on restores both
- [ ] Turning it off and on records who and when, shown on the page
- [ ] Seam 1 tests cover the admin endpoints, the migration carry-over and the reply tools; seam 3 tests cover the Features page
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

None - can start immediately
