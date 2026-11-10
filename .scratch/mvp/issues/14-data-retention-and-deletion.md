# 14 — Data retention and "Delete my data"

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

Users' raw messages are not kept forever, and Users can leave cleanly. On each scheduler tick, raw messages (and LangGraph checkpoints) older than the Admin-set retention period (default 30 days) are deleted; Conversation Summaries and Memory Items remain. A "Delete my data" option on the Dashboard removes the User's messages, checkpoints, User Memory, Check-in history and Telegram Connection after a confirmation.

## Acceptance criteria

- [ ] A scheduler tick deletes raw messages and checkpoints older than the retention setting; Summaries and Memory Items remain
- [ ] Admins can change the retention period
- [ ] "Delete my data" (with confirmation) removes messages, checkpoints, Conversation Summaries, Memory Items, Check-in history and the Telegram Connection
- [ ] After deletion, messages from that Telegram account are treated as from an unknown Telegram user
- [ ] Seam 2 tests with a fake clock cover retention; seam 1 tests cover "Delete my data" removing every listed kind of data
- [ ] Seam 3 tests cover the delete flow
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/06-user-memory.md`
- `.scratch/mvp/issues/12-smart-check-ins.md`
