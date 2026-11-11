# 17 — Settings via chat

Status: ready-for-agent

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

- [ ] Asking in plain words pauses or resumes Check-ins, changes frequency or quiet hours, turns User Memory on or off, forgets a named Memory Item, or changes time zone
- [ ] The reply says plainly what was changed; an unclear request gets a question back, not a guess
- [ ] "Delete my data" in chat asks for the exact confirmation word and only deletes after it; anything else cancels
- [ ] Requests to delete the account, change country or disconnect Telegram are pointed to the Dashboard and change nothing
- [ ] Changes made in chat show on the Dashboard with a "Changed in chat" caption and date
- [ ] A message the Safeguard flags as a crisis never runs a settings tool
- [ ] Core code imports no LangChain or LangGraph; tools are thin calls into core services
- [ ] Seam 1 tests with a scripted fake chat model cover each allowed change, the delete confirmation (confirmed and cancelled), refused Dashboard-only changes, and crisis → no tool
- [ ] Seam 3 tests cover the "Changed in chat" caption
- [ ] Evals include a few settings requests to check the right tool is picked
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`: pause Check-ins and forget a memory by chatting on Telegram, then see both on the Dashboard

## Blocked by

- `.scratch/mvp/issues/06-user-memory.md`
- `.scratch/mvp/issues/11-basic-check-ins.md`
- `.scratch/mvp/issues/14-data-retention-and-deletion.md`
