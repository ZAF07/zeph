# 08 — Reply instructions cached up to the fixed part

Status: needs-triage
Blocked by: 06

## Parent

`.scratch/openrouter/PRD.md` (user stories 19, 20). Found on 2026-11-25, during the `/run` of issue 06.

## What to build

With the Reply on a Claude model, prompt caching never hits. The adapter marks the whole instructions as one cached part, and the Reply's instructions end with text made for that one message (from "## 2. What they just asked or need right now" on). So every Reply writes about 3,900 tokens to the cache and no later Reply reads them. A cache write costs about a quarter more than plain input, so the Reply on Claude costs more with caching than without.

Measured in the issue 06 `/run` (haiku, two messages in a row): the first Reply wrote 3,965 tokens and read 0; the second wrote 3,859 and read 0. The first 3,992 characters of the two instructions (about 60%) were the same, and so were the 6 tools offered.

Safeguard, Understanding and Reply plan are not affected: their instructions are fixed, and the Reply plan read 4,674 of 8,249 prompt tokens from the cache on the second message.

The fixed part of the Reply's instructions (and the tools, which come before it) should be cached on its own, so the second Reply reads it.

## Open questions

- How the adapter learns where the fixed part ends. The `ChatModel` port takes one `instructions` text today. Options: the port takes the fixed part and the per-message part as two texts; or the per-message part moves out of the instructions into the messages.
- Whether to stop marking the Reply for caching until this is built, so it doesn't cost more in the meantime.
- Whether the same is true of other services not run in the issue 06 check (Check-ins, memory processing, the keeping steps).

## Acceptance criteria

- [ ] `/run`: with the Reply on a Claude model, the second of two messages in a row shows cached tokens in the logs
- [ ] Services with fixed instructions still get cache hits
- [ ] DeepSeek calls are unchanged
- [ ] The language's checks pass

## Blocked by

- 06

## Comments
