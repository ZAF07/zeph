# 14 — Data retention and "Delete my data"

Status: ready-for-agent

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
