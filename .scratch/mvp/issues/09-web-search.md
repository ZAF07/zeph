# 09 — Web search

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

The Companion can search the web and fetch pages when the conversation needs it. Introduces the web search port (Tavily adapter). Search and page fetch are tools the model may call during response composition. The tool instructions forbid personal details in queries, and the Companion mentions sources when it uses web information. Admins can turn web search on or off and set a per-User daily web search limit.

## Acceptance criteria

- [ ] Response composition can call web search and page fetch tools; results reach the reply
- [ ] Tool instructions say queries must never contain the User's personal details
- [ ] Replies that use web information mention where it came from
- [ ] With web search off, the tools are not offered to the model
- [ ] Once a User hits the daily web search limit, the tools are not offered for that User until the next day
- [ ] Seam 1 tests with a fake web search adapter cover: tool call → result used, toggle off, daily limit reached
- [ ] A separate contract test checks the Tavily adapter against the real API
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/04-admin-area-foundation.md`
