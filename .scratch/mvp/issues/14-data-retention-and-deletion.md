# 14 — Data retention and "Delete my data"

Status: in-progress

## Parent

`.scratch/mvp/PRD.md`

## What to build

Users' raw messages are not kept forever, and Users can leave cleanly. On each scheduler tick, raw messages (and LangGraph checkpoints) older than the Admin-set retention period (default 30 days) are deleted; Conversation Summaries and Memory Items remain. A "Delete my data" option on the Dashboard removes the User's messages, checkpoints, User Memory, Check-in history and Telegram Connection after a confirmation. A separate "Delete account" option does the same and also deletes the User and their Clerk account (through the auth port), after a "type DELETE" confirmation.

## Design

- `docs/design/zeph-product.html`: Account and privacy (Your data section)

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [ ] A scheduler tick deletes raw messages and checkpoints older than the retention setting; Summaries and Memory Items remain
- [ ] Admins can change the retention period
- [ ] The Account & privacy page states the retention period (read from settings) and that Summaries and memories stay until deleted
- [ ] "Delete my data" (with confirmation) removes messages, checkpoints, Conversation Summaries, Memory Items, Check-in history and the Telegram Connection
- [ ] "Delete account" (type DELETE to confirm) removes everything "Delete my data" removes, plus the User record and the Clerk account
- [ ] After deletion, messages from that Telegram account are treated as from an unknown Telegram user
- [ ] Seam 2 tests with a fake clock cover retention; seam 1 tests cover "Delete my data" removing every listed kind of data
- [ ] Seam 3 tests cover the delete flow
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/06-user-memory.md`
- `.scratch/mvp/issues/12-smart-check-ins.md`

## Comments

**2026-11-12 — started on branch `feat/14-data-retention-and-deletion`.** Plan:
- New setting `message_retention_days` (default 30, 1–365) in the seed and on admin Platform settings (new "Data" section, as in the design). The Account & privacy page reads it through `GET /api/platform-content`.
- Retention runs on every scheduler tick, after Check-ins: delete every message sent before now − retention days (Conversations themselves, Summaries and Memory Items stay). For each User who lost messages, the conversation engine forgets its saved state (their LangGraph checkpoint thread). The thread carries nothing from one turn to the next, so clearing it whole is safe and also removes the old checkpoints. Our clock decides, not LangGraph's own timestamps, so seam 2 tests can use the fake clock.
- `ConversationEngine` port gains `forget_user(user_id)` (LangGraph `delete_thread`).
- New auth port `AuthAccounts.delete_account(auth_id)`; Clerk adapter calls `DELETE /v1/users/{id}`.
- `DELETE /api/me/data`: removes Conversations and messages, checkpoints, Conversation Summaries, Memory Items, Check-in history, connection tokens and the Telegram Connection, in one transaction. Profile, settings, Usage counts and Safeguard Events (no message content, Admin records) stay.
- `DELETE /api/me`: the same, plus the User row (FKs cascade), then the Clerk account. Our data goes first, so if Clerk fails a retry still works. The last Admin can't delete their account (409), so there is always an Admin.
- Dashboard: "Your data" section (retention sentence, Delete my data with type-DELETE confirm, as in the design) and "Delete account" section (type DELETE, then sign out). The design's "you can also tell Zeph" hint is left out until settings-via-chat (issue 17) exists. Export is tagged Later.
