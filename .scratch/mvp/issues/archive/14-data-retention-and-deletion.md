# 14 — Data retention and "Delete my data"

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

Users' raw messages are not kept forever, and Users can leave cleanly. On each scheduler tick, raw messages (and LangGraph checkpoints) older than the Admin-set retention period (default 30 days) are deleted; Conversation Summaries and Memory Items remain. A "Delete my data" option on the Dashboard removes the User's messages, checkpoints, User Memory, Check-in history and Telegram Connection after a confirmation. A separate "Delete account" option does the same and also deletes the User and their Clerk account (through the auth port), after a "type DELETE" confirmation.

## Design

- `docs/design/zeph-product.html`: Account and privacy (Your data section)

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [x] A scheduler tick deletes raw messages and checkpoints older than the retention setting; Summaries and Memory Items remain
- [x] Admins can change the retention period
- [x] The Account & privacy page states the retention period (read from settings) and that Summaries and memories stay until deleted
- [x] "Delete my data" (with confirmation) removes messages, checkpoints, Conversation Summaries, Memory Items, Check-in history and the Telegram Connection
- [x] "Delete account" (type DELETE to confirm) removes everything "Delete my data" removes, plus the User record and the Clerk account
- [x] After deletion, messages from that Telegram account are treated as from an unknown Telegram user
- [x] Seam 2 tests with a fake clock cover retention; seam 1 tests cover "Delete my data" removing every listed kind of data
- [x] Seam 3 tests cover the delete flow
- [x] `make check` passes
- [x] Verified in the running app via `/run`

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

**2026-11-12 — implemented, reviewed and verified.** Commits `987e611`, review fixes `1645764` on `feat/14-data-retention-and-deletion`.

Done and verified: every acceptance criterion. `make check` green (Python 299, web 239; ruff, ruff format, mypy, eslint, prettier, tsc clean). Clerk contract tests pass against real Clerk (2, including the new delete one). Docker run with real Postgres, Clerk (dev) and DeepSeek, as temporary Clerk test Users:
- On start, `message_retention_days` was seeded as 30.
- Platform settings has a "Data" section with Message retention. Set 30 → 14, it survives reload. 0 is refused with "must be a whole number from 1 to 365". Account & privacy then reads "Messages are deleted automatically after 14 days. Summaries and memories stay until you delete them."
- Retention: a real webhook message from a made-up Telegram account connected to the test User. The reply stopped at Telegram for the fake chat, which was expected. That left 1 message and 2 checkpoints. I moved the message and Conversation 15 days back and added a message from now. On the next real scheduler tick, the old message and every checkpoint row (checkpoints, blobs, writes) were deleted. The recent message stayed. The Conversation Summary and Memory Item that DeepSeek wrote on that tick stayed. The scheduler logged no errors.
- Delete my data: Conversations, a Summary, a Memory Item, a Check-in, a connection token, the Telegram Connection, 2 messages and 2 checkpoints, all deleted in the browser. Confirm stays locked until DELETE is typed. Afterwards all are 0, and the User keeps their name, Admin role and onboarding. A new message from that Telegram account went straight to the unknown-user reply, with nothing saved.
- Delete account: type DELETE → "Permanently delete account". The `users` row is gone, Clerk `GET /users/{id}` gives 404, the browser lands on /sign-in, and the owner Admin remains.
- At 390px: no sideways scroll; the confirmation box fits.
- Clean-up: temporary Users deleted from the database and Clerk; retention back to 30 with no `updated_by`; no fake Telegram Connection left.

Decisions:
- Retention runs on every scheduler tick, after Check-ins. Our clock picks the cutoff, not LangGraph's own timestamps. For each User with messages older than the cutoff, the conversation engine forgets its whole saved state (their LangGraph thread) first. Only then are the messages deleted, so if forgetting fails the messages stay and the next tick tries again. Forgetting the whole thread is safe: a turn sets every value it reads, so nothing carries from one message to the next. Conversations (with no text) stay.
- `message_retention_days` is 1–365, default 30. The design's settings note said "at the next nightly run"; it now says "within a minute", because cleanup runs on each tick.
- New ports: `ConversationEngine.forget_user` and `AuthAccounts.delete_account` (Clerk adapter `ClerkAccounts`, chosen by the same `AUTH_VERIFIER_ADAPTER` setting). A user Clerk no longer has counts as deleted.
- Delete my data removes Conversations and messages, checkpoints, Summaries, Memory Items, Check-in history, connection tokens and the Telegram Connection, in one transaction. Profile, preferences, Usage counts and Safeguard Events stay; they hold no message content.
- Delete account forgets the engine state, deletes the User (foreign keys cascade everything), then deletes the Clerk account. Our data goes first, so a failed Clerk call can be retried. The last Admin gets 409 ("Make someone else an Admin first"), so there is always an Admin.
- Both deletes use "Type DELETE to confirm", as in the design. The design's "you can also tell Zeph 'delete my data'" hint is left out until issue 17 adds that; Export is Later.

Caveats / follow-ups:
- If processing a Conversation keeps failing for longer than the retention period, its messages are deleted before a Summary is ever written.
- If the Clerk call fails after our data is gone, the User sees an error and is still signed in; their next request quietly makes a new empty User. Trying again deletes both.
- "Delete my data" racing an incoming Telegram message, or retention clearing a thread in the middle of a turn, could leave a stray message or checkpoint. This is low risk and not handled.
- The backend logs the Telegram bot token in httpx error URLs. This was already the case before this issue, seen during the run.

Evidence: seam 2 `tests/test_message_retention.py` (5: tick deletes old messages and checkpoints, Summary and Memory Item stay; newer messages stay; replies still work after state is cleared; an Admin-shortened retention applies; messages stay until the saved state can be deleted); seam 1 `tests/test_data_deletion.py` (6: every kind removed and account kept, then unknown Telegram user; other Users untouched; Delete account removes the User and the Clerk account, then unknown Telegram user; last Admin refused; Admin with another Admin can delete; sign-in needed), `tests/test_admin_settings.py` (seeded value, 0 and 366 refused), `tests/test_onboarding.py` (platform content); adapters `tests/adapters/test_clerk_accounts.py` (3), contract `test_clerk_treats_deleting_an_account_it_does_not_have_as_done`; seam 3 `web/src/components/AccountSettings.test.tsx` (7 new: retention sentence, Delete my data locked until DELETE, cancel, failure, Delete account then sign out, keep account, last-Admin message), `PlatformSettingsForm.test.tsx` (Data section save).

## Completion

- Completed: 2026-11-12
- Commit: 987e611, review fixes 1645764, archive 2fd8de1 (merged from `feat/14-data-retention-and-deletion` in 955f4bf)
