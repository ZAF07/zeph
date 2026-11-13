# 01 — Features, with Web Search as the first one

Status: completed

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

- [x] The admin Features page lists Web Search with its switch for everyone and last change; only Admins can see or change it
- [x] The Web Search switch is gone from the Settings page, and an existing install keeps its old on/off value after the migration
- [x] With Web Search off for everyone, replies get no Web Search tools and the "not available on your account" note; turning it back on restores both
- [x] Turning it off and on records who and when, shown on the page
- [x] Seam 1 tests cover the admin endpoints, the migration carry-over and the reply tools; seam 3 tests cover the Features page
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

None - can start immediately

## Comments

**2026-11-13 — implemented, reviewed and verified** on branch `feat/features-01-web-search-switch`.

Done and verified: every acceptance criterion. `make check` green (Python 347, web 267; ruff, ruff format, mypy, eslint, prettier, tsc clean).

Docker run with real Postgres, Clerk (dev), DeepSeek and Tavily, signed in as a temporary Clerk test Admin:
- Migration on a real install: `web_search_enabled` was set to `false` at revision 0014; after the rebuild (0015) `feature_switches` had `web_search | off | never changed`, the old setting was gone and `reply_features_unavailable_note` was seeded.
- Features page showed Web Search "Off for everyone", "Never changed". No Web Search switch on Platform settings; its Web search section shows only the daily limit.
- Off: "Can you look up who won the Booker Prize this year?" posted to the webhook as the owner's connected Telegram account → no web search (count stayed 4), reply: "I can't, sorry — web search isn't available on your account right now…".
- Turned on from the page → "Changed 13 Nov, 12:09 by run-check-…@example.com", kept after reload. Same question → 1 search (4 → 5), reply named the winner and said "According to the BBC…".
- Turned off again at 390px → recorded "Changed 13 Nov, 12:10 by …", no sideways scroll, no page errors.
- A plain User opening `/admin/features` was sent to `/`.
- No backend errors. Clean-up: temporary Users deleted from the database and Clerk; Web Search switch reset to on with no recorded change (as before the run). The two test messages and replies stay in the owner's own Conversation.

Decisions:
- Core `FeatureService` (`core/features.py`): `works_for(user_id, feature)`, `unavailable_for`, `unavailable_note`, `list_for_everyone`, `set_for_everyone`. The fixed Feature list is `FEATURES` (only Web Search for now); `feature_details` finds a Feature's name and description.
- `feature_switches` table: one row per Feature (`is_on`, `changed_by`, `changed_at`). A Feature with no row is on for everyone. Migration 0015 copies a true/false `web_search_enabled` (else on), keeping who/when only if an Admin had saved it, then deletes the setting; downgrade puts it back.
- Admin API: `GET /api/admin/features`, `PUT /api/admin/features/{feature}` with `{"on": bool}`; the response gives `changed_by_email`. Unknown Features and non-true/false values get 422.
- The note is a seeded setting `reply_features_unavailable_note` with `{features}` and `{dashboard_url}`, added to the reply instructions only when a Feature doesn't work for the User. Like the other `reply_*` texts it isn't on the Settings page.
- `SettingKind.ON_OFF` was removed (Web Search was its only setting); the Dashboard's `SettingValue` no longer allows true/false.
- A switch on the Features page saves as soon as it is flipped; a failed change shows an alert and keeps the switch as it was.

Caveats / follow-ups:
- Per-User switches, the other Features and the Users-page panel are issues 02–05.

Evidence: seam 1 `tests/test_features.py` (7: Web Search listed on with no change; off/on records who and when; only Admins; unknown Feature or value refused; replies lose web tools and get the note when off, both back when on; switch no longer a platform setting; migration keeps an existing install's value); `tests/test_web_search.py` and `tests/test_admin_settings.py` updated. Seam 3 `web/src/components/AdminFeatures.test.tsx` (5: row with description, switch, never changed; who/when; turning off; failed change keeps switch; Try again), `PlatformSettingsForm.test.tsx` (no switch, limit shown), `SidebarNav.test.tsx` (Features link).

## Completion

- Completed: 2026-11-13
- Commit: fb78a73 "Features issue 01: Features core service with Web Search as the first Feature…", review fixes d22e509 "Features issue 01 review fixes: one feature_details helper…", archive 50d2560 "Features issue 01 done: archive issue with run evidence…" (merged from `feat/features-01-web-search-switch` in f020e5c "Merge Features issue 01…")
