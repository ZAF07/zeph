# 03 — Stickers and Knowledge as Features

Status: completed

## Parent

`.scratch/features/PRD.md`

## What to build

Stickers and Knowledge join the Feature list, so Admins can switch them for everyone (and per User once issue 02 is in).

- Stickers: the reply is offered the sticker tool only when Stickers works for the User. Incoming stickers are still read through their emoji, and Admins can still add stickers by sending them.
- Knowledge: Knowledge retrieval is skipped when Knowledge doesn't work for the User, so no passages go into the reply.
- Both appear on the admin Features page (and in the per-User panel) with descriptions, and in the "not available on your account" note when off.

## Acceptance criteria

- [x] With Stickers off, replies get no sticker tool and no sticker is sent; incoming stickers still read as their emoji
- [x] With Knowledge off, no Knowledge passages go into the reply
- [x] Both show on the Features page with their switch and last change, and turning them back on restores them
- [x] Seam 1 tests cover both on and off; seam 3 tests cover the new rows
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/features/issues/01-features-and-web-search-switch.md`

## Comments

**2026-11-13 — implemented, reviewed and verified** on branch `feat/features-03-stickers-and-knowledge`.

Done and verified: every acceptance criterion. `make check` green on the final code (exit 0: Python 361 passed; web 282 passed; ruff, ruff format, mypy, eslint, prettier, tsc clean).

Docker run with real Postgres, Clerk (dev), DeepSeek and fastembed/pgvector, signed in as a temporary Clerk test Admin. Reply checks used a probe inside the backend container, built from the real adapters and database: `StickerTools.offer` and `KnowledgeRetrieval.recall` for the owner.
- Features page: three rows (Web Search, Stickers, Knowledge), each with its description, "On for everyone" and "Never changed". No page errors.
- Clicked Stickers and Knowledge off → "Off for everyone", "Changed 13 Nov, 13:29 by run-check-…". Probe: works stickers=False, knowledge=False; sticker tools `[]`; Knowledge passages 0 chars.
- With Stickers off, the owner sent a sticker to the webhook (🌱, fake file id) → added to the Sticker Library. Admins can still add stickers by sending them. Gave it a note in the database (setup only); the probe still showed no sticker tool.
- Real message to the webhook as the owner's Telegram account asking for a celebration sticker → the reply had no sticker. The model said stickers "isn't available on your account".
- Clicked both back on → probe: sticker tools `['send_sticker']`, Knowledge passages 2604 chars.
- Users page → Features on the owner's row → panel lists Web Search, Stickers and Knowledge. Set Knowledge Off for the owner → "Off: turned off for this User" with who and when. Probe: Knowledge 0 chars, Stickers still offered. Back to Default → "On: on for everyone", Knowledge 2604 chars.
- 390px: panel fits, no sideways scroll. No backend errors in the logs.
- Clean-up: deleted the test sticker. Removed the Stickers/Knowledge switch rows, so both are on with no recorded change. No per-User rows. Test Admin deleted from Clerk and the database. The test message and reply stay in the owner's own Conversation.

Decisions:
- No migration. A Feature with no saved switch is on for everyone, so existing installs get Stickers and Knowledge on.
- `StickerTools.offer(user_id)` returns an empty choice when Stickers doesn't work. Incoming stickers and Admins adding stickers don't check the switch.
- `KnowledgeRetrieval.recall(user_id, conversation_id)` returns "" before embedding or searching when Knowledge doesn't work.
- Order in the Feature list: Web Search, Stickers, Knowledge. Issues 04 and 05 add the rest.
- The Dashboard only needed the `Feature` type widened. The Features page and panel already show whatever Features the API lists.

Review (`/code-review`): Standards had no hard violations. Spec found nothing missing or wrong. Fixed: the Web Search test now uses the shared `unavailable_note` helper, the off path no longer reads the sticker tool description, and the Stickers description is clearer. Left: the repeated `send_sticker` filter in tests, and that a new Feature is listed in 3 places (enum, `FEATURES`, TS type). Both are minor.

Evidence: seam 1 `tests/test_features.py`. The list tests now cover all three Features. 5 new tests:
- Stickers off for everyone, then back on: no sticker tool, no sticker sent, the note shown.
- Stickers off for one User: their sticker is still read as its emoji; the owner still gets the tool.
- Admins add stickers by sending them while Stickers is off.
- Knowledge off for everyone, then back on: no passages, no search, the note shown.
- Knowledge off for one User only.

Seam 3: `web/src/components/AdminFeatures.test.tsx` (Stickers and Knowledge rows, last change, turning back on) and `UserFeaturesPanel.test.tsx` (new rows, reasons, turning Knowledge back on for the User).

## Completion

- Completed: 2026-11-13
- Commit: 41766d3 "Features issue 03: Stickers and Knowledge join the Feature list…", review fixes 88ffc67 "Features issue 03 review fixes: Web Search test reuses the unavailable_note helper…", archive 85900de "Features issue 03 done: archive issue with run evidence…" (merged from `feat/features-03-stickers-and-knowledge` in 002aa8b "Merge Features issue 03…")
