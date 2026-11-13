# 05 — Settings in Chat as a Feature

Status: completed

## Parent

`.scratch/features/PRD.md`

## What to build

Settings in Chat (ADR 0006) joins the Feature list, ready for a lower plan that only allows settings on the Dashboard.

- When it doesn't work for a User, the reply isn't offered the settings tools, except Delete My Data, which is always offered and keeps its confirmation word.
- The "not available on your account" note tells the Companion to point the User to the Dashboard link when they ask to change a setting.
- The Safeguard still runs first, unchanged.

## Acceptance criteria

- [x] With Settings in Chat off, asking in chat to pause Check-ins (or any other setting) changes nothing and the reply points to the Dashboard link
- [x] With Settings in Chat off, "delete my data" in chat still works with its confirmation word
- [x] With it on, every chat setting works as before
- [x] It shows on the Features page and per-User panel with its switch and last change
- [x] Seam 1 tests cover on, off and Delete My Data; seam 3 tests cover the new row
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/features/issues/01-features-and-web-search-switch.md`

## Comments

**2026-11-13: implemented, reviewed and verified** on branch `feat/features-05-settings-in-chat`.

Done and verified: every acceptance criterion. `make check` passed on the final code (exit 0). Python: 372 passed. Web: 289 passed. ruff, ruff format, mypy, eslint, prettier and tsc were clean.

Docker run with real Postgres, Clerk (dev) and DeepSeek, signed in as a temporary Clerk test Admin. The tool checks used a probe inside the backend container, built from the real repositories, that showed which settings tools and instructions a reply to the owner gets. Chat checks were real messages to the webhook as the owner's Telegram account.
- Features page: a new "Settings in Chat" row with its description, "On for everyone" and "Never changed". Clicked off → "Off for everyone", "Changed 13 Nov, 14:17 by run-check-…". No page errors.
- Probe while off: tools `['start_deleting_my_data']` only, the delete-only instructions, and the note "These aren't available on this person's account right now: Settings in Chat… change their settings on the Dashboard: http://localhost:3000". The new setting was seeded into the existing database on start.
- Real message "please change my time zone to Europe/London" → time zone stayed Asia/Singapore. Reply: "settings aren't available in chat on your account. You can change your time zone on the Dashboard: http://localhost:3000".
- Real message "please delete my data" → the tool ran (`data_deletion_requested_at` set) and the reply asked to "Reply with exactly DELETE to confirm". Then sent "No, cancel that" → "Cancelled — nothing deleted". The request was cleared and the Telegram Connection was still there.
- Clicked back on → probe listed all 9 settings tools again.
- Users page → Features on the owner's row → Settings in Chat Off → "Off: turned off for this User" with who and when. Probe: only the delete tool. Back to Default → "On: on for everyone". At 390px: no sideways scroll (scrollWidth 390). No backend errors in the logs.
- Clean-up: removed the Settings in Chat switch row, so it's on with no recorded change. No per-User rows. Test Admin deleted from Clerk and the database. The test messages and replies stay in the owner's own Conversation.

Decisions:
- No migration. A Feature with no saved switch is on for everyone.
- When off, `SettingsTools.offer(user_id)` offers only `start_deleting_my_data`. Instead of `reply_settings_instructions` (which names tools that aren't there), the reply gets a new seeded setting, `reply_delete_data_instructions`: start deleting when asked, and never say another setting was changed. The existing not-available note already points to the Dashboard link, so it wasn't changed.
- Off also hides `list_memories` and `forget_memory` in chat. Seeing and deleting memories still works on the Dashboard.
- "With it on, every chat setting works as before" rests on the probe (all 9 tools offered) and the unchanged settings-via-chat tests passing. The owner's real settings weren't changed in the run.

Review (`/code-review`):
- Standards: no hard violations.
- Spec: met. It flagged that ADR 0006 didn't mention Features, and that the off test's pause check proved nothing.
- Fixed: the `offer()` docstring, one `SettingsOffer` built from the chosen tools and instructions, and the pause check dropped (the tool-list check is the proof). ADR 0006 got a new consequence.
- Left: tool names written out as strings in tests (matches `SETTINGS_TOOLS`), and that a Feature is still listed in 3 places (enum, `FEATURES`, TS type).

Evidence:
- Seam 1: `tests/test_features.py`. Both list tests now include `settings_in_chat`. 2 new tests:
  - Off for everyone, then back on: only the delete tool, the delete-only instructions, the note with the Dashboard link; all tools and the normal instructions when back on.
  - Off for one User: Delete My Data still asks for the confirmation word and deletes on it; the owner still gets every tool.
- Seam 3: `web/src/components/AdminFeatures.test.tsx` (Settings in Chat row, turning it off, last change) and `UserFeaturesPanel.test.tsx` (row, turning it off for the User, reason and last change).
- Docs: `CONTEXT.md` (Feature: the Companion points to the Dashboard when Settings in Chat is off) and ADR 0006.

## Completion

- Completed: 2026-11-13
- Commit: 1b8a9e2 "Features issue 05: Settings in Chat joins the Feature list…", review fixes f0833d6 "Features issue 05 review fixes: SettingsTools.offer docstring…"
