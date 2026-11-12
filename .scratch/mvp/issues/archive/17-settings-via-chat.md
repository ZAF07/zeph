# 17 — Settings via chat

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

Users can change their settings by telling the Companion in plain words, not just on the Dashboard (ADR-0006). Response composition gets tools that call the same core services the Dashboard API uses: pause or resume Check-ins, change Check-in frequency and quiet hours, turn User Memory on or off, forget a specific Memory Item, change time zone, and "Delete my data". There are no slash commands besides `/start <token>`.

"Delete my data" only runs after the User replies with an exact confirmation word; any other reply cancels it. Delete account, country and disconnecting Telegram are not available in chat.

The Companion says plainly what it changed in its reply. Each change is recorded as made via chat, and the Dashboard shows a "Changed in chat" caption with the date on that setting. The Safeguard runs first, so a crisis message never triggers a tool.

## Design

- `docs/design/zeph-product.html`: the "Changed in chat" caption on settings in Check-ins, Memories and Account and privacy

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [x] Asking in plain words pauses or resumes Check-ins, changes frequency or quiet hours, turns User Memory on or off, forgets a named Memory Item, or changes time zone
- [x] The reply says plainly what was changed; an unclear request gets a question back, not a guess
- [x] "Delete my data" in chat asks for the exact confirmation word and only deletes after it; anything else cancels
- [x] Requests to delete the account, change country or disconnect Telegram are pointed to the Dashboard and change nothing
- [x] Changes made in chat show on the Dashboard with a "Changed in chat" caption and date
- [x] A message the Safeguard flags as a crisis never runs a settings tool
- [x] Core code imports no LangChain or LangGraph; tools are thin calls into core services
- [x] Seam 1 tests with a scripted fake chat model cover each allowed change, the delete confirmation (confirmed and cancelled), refused Dashboard-only changes, and crisis → no tool
- [x] Seam 3 tests cover the "Changed in chat" caption
- [x] Evals include a few settings requests to check the right tool is picked
- [x] `make check` passes
- [x] Verified in the running app via `/run`: pause Check-ins and forget a memory by chatting on Telegram, then see both on the Dashboard

## Blocked by

- `.scratch/mvp/issues/06-user-memory.md`
- `.scratch/mvp/issues/11-basic-check-ins.md`
- `.scratch/mvp/issues/14-data-retention-and-deletion.md`

## Comments

**2026-11-12 — implemented, reviewed and verified** on branch `settings-via-chat`.

Done and verified: every acceptance criterion. `make check` green (Python 333, web 248; ruff, ruff format, mypy, eslint, prettier, tsc clean). Evals with real DeepSeek: Settings 12 of 12, Safeguard 30 of 30, Knowledge 8 of 8, Persona 17 of 18. The one Persona miss is `captioned-photo` (photo honesty). It fails the same way on `main`, so it isn't caused by this change; it is filed as issue 19.

Docker run with real Postgres, Clerk (dev) and DeepSeek. A temporary Clerk test User had a Telegram Connection made up for the run, whose replies went to the owner's own bot chat. Messages went in through the real webhook:
- "give me a week off from check-ins" → paused until 19 Nov. Reply: "Done — check-ins are off for a week, back on the 19th."
- "forget what I told you about my sister" → the Jo Memory Item was deleted and the other one stayed. Reply: "Forgotten — the thing about your sister is gone."
- "no messages after 9pm … moved to London, update my time zone" → quiet hours start at 21:00, time zone Europe/London. The reply said plainly what changed.
- "delete my account" → nothing changed. Reply: "I can't do that one from here, sorry — it's on the Dashboard, under Account and privacy."
- "stop remembering things about me" → User Memory off, and the reply said nothing was deleted.
- Delete my data: asked → reply asks for exactly "DELETE" and lists what goes. "hmm actually no, keep it" cancelled it ("nothing was deleted") and the memory stayed. Asked again, then "DELETE" → Conversations, Memory Items, Summaries, Check-ins, Telegram Connection and LangGraph checkpoints all 0. The account, name and settings were kept. No backend errors.
- Dashboard: "Changed in chat · 12 Nov" shown under quiet hours, time zone and pause on Check-ins, under the memory switch on Memories, and under time zone on Account and privacy. Changing quiet hours on the Dashboard removed that caption (3 → 2, also after reload). After the review fix, saving only the name on Account kept the time-zone caption (also after reload). At 390px there was no sideways scroll, and there were no page errors.
- Clean-up: temporary Users deleted from the database and Clerk; no made-up Telegram Connection left.

Decisions:
- Tools live in core `chat_settings.py` (`SettingsTools` offers `ReplySettingsTools` per reply, like web search and stickers). Each tool is a thin call into the same core service the Dashboard API uses (`CheckInService.pause/resume/change_settings`, `UserService.update_preferences`, `UserMemoryService.delete_item`), with `in_chat=True`. Tools: `pause_check_ins`, `resume_check_ins`, `change_check_in_frequency`, `change_quiet_hours`, `turn_user_memory_on_or_off`, `list_memories` + `forget_memory` (by number from the list), `change_time_zone`, `start_deleting_my_data`. Delete account, country and Telegram disconnect have no tool, so a misread message can't change them.
- "Changed in chat" is stored per setting on the User (`settings_changed_in_chat`, JSONB, migration 0014): `check_in_pause`, `check_in_frequency`, `quiet_hours`, `user_memory`, `time_zone`. A change made in chat stamps the time. A Dashboard change that really changes the value drops the stamp. Turning Check-ins on or off counts as a pause change. `/api/me` returns it as `changed_in_chat`.
- Delete my data in chat: the tool only sets `data_deletion_requested_at`. A new graph step after the Safeguard settles it on the User's next message. The whole message equal to the confirmation word (Admin setting `data_deletion_confirmation_word`, default DELETE; case and outer spaces ignored) deletes the data and sends the fixed `data_deleted_reply` without saving it. Anything else cancels, and the reply is told to say so (`reply_data_deletion_cancelled_note`). A crisis message also cancels it. The engine deletes the User's checkpoint thread after a confirmed turn. `ChatDataDeletion` deletes through the same repository call as the Dashboard's `UserDataService.delete_data`; it can't use that service directly, because that service needs the conversation engine that runs the turn.
- The Safeguard already runs before composition, so tools are never offered on a crisis.
- Tool descriptions are in code; the reply instructions (`reply_settings_instructions`) and replies are seeded platform settings. The first eval run had the model asking "want me to?" on clear requests, so the instructions now say to act straight away. The eval went from 9/12 to 12/12.
- The design's "You can also tell Zeph…" hints, deferred by issue 14, were added on Check-ins and Your data.
- `to_transcript_lines` moved into `core/transcripts.py` to break an import cycle.

Caveats / follow-ups:
- Forgetting a Memory Item or deleting data in chat leaves no "changed in chat" record. There is no setting left to caption.
- A delete request has no time limit. The User's next message settles it whenever that comes, even after a Check-in in between.
- Over the daily message limit, a cancelling message gets only the limit reply, so the cancel isn't mentioned.
- Unclear requests and Dashboard-only refusals rely on the prompt; the Settings eval checks them.
- `captioned-photo` Persona eval fails on `main` too (issue 19).

Evidence: seam 1 `tests/test_settings_via_chat.py` (17: tools and instructions offered; pause marks changed in chat; resume; pause when off changes nothing; frequency and quiet hours; unclear quiet hours change nothing; memory off and on; forget a named Memory Item; forget without listing or with a wrong number; time zone incl. unknown one; Dashboard change clears the mark; saving the profile unchanged keeps the marks; turning Check-ins off clears the pause mark; delete only after the word, incl. checkpoints and unknown-user afterwards; any other reply cancels; crisis runs no tool; crisis cancels a pending delete); `tests/test_eval_helpers.py` (3 new); seam 3 `web/src/components/ChangedInChatCaption.test.tsx` (2), `CheckInsSettings.test.tsx` (3 new: hint, captions with day, caption dropped after a Dashboard change), `Memories.test.tsx` (1 new), `AccountSettings.test.tsx` (3 new: Delete my data hint, time zone and memory captions, caption dropped after save); eval `evals/test_settings_eval.py` with `evals/cases/settings.yaml` (12 cases).

## Completion

- Completed: 2026-11-12
- Commit: 9c15133, review fixes b54cbe5
