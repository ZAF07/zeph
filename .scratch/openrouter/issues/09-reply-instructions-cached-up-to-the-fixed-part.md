# 09 — Reply instructions cached up to the fixed part

Status: ready-for-agent
Blocked by: 06

## Parent

`.scratch/openrouter/PRD.md` (user stories 19, 20). Found on 2026-11-25, during the `/run` of issue 06.

## What to build

With the Reply on a Claude model, prompt caching never hits. The adapter marks the whole instructions as one cached part, and the Reply's instructions end with text made for that one message (from "## 2. What they just asked or need right now" on). So every Reply writes about 3,900 tokens to the cache and no later Reply reads them. A cache write costs about a quarter more than plain input, so the Reply on Claude costs more with caching than without.

Measured in the issue 06 `/run` (haiku, two messages in a row): the first Reply wrote 3,965 tokens and read 0; the second wrote 3,859 and read 0. The first 3,992 characters of the two instructions (about 60%) were the same, and so were the 6 tools offered.

Safeguard, Understanding and Reply plan are not affected: their instructions are fixed, and the Reply plan read 4,674 of 8,249 prompt tokens from the cache on the second message.

The fixed part of the Reply's instructions (and the tools, which come before it) should be cached on its own, so the second Reply reads it. This must hold for every model that can be picked for the Reply: all Claude models (Haiku, Sonnet, Opus, Fable) and DeepSeek V4 Pro and Flash.

## Decisions (2026-11-25)

- The Reply already builds the fixed part and the per-message part separately (`write_instructions` in `response_composition.py`). It stops joining them into one text and passes them to the `ChatModel` port as two texts. The per-message text is optional and empty by default, so the other services don't change.
- The fixed part is the Persona, the response prompt and the priority order. It ends before "## 1." (the boundaries and data deletion note change per User and message), not before "## 2.".
- The Claude adapter marks only the fixed part for caching. For DeepSeek, which caches the same start of a request by itself, the two texts are joined with the fixed part first.
- Caching must work for every model that can be picked: all Claude models (Haiku, Sonnet, Opus, Fable) and DeepSeek V4 Pro and Flash, not just Haiku.
- Check first: each Claude model has a minimum size a cached block must reach, and some are higher than others. Find each picked model's minimum and check that tools plus the fixed part (about 2,500 tokens) reach it. If a model's minimum is not reached, say so in this issue before building, because the fix would not help that model.
- Don't stop caching the Reply in the meantime. Just build the fix.
- Other services (Check-ins, memory processing, the keeping steps): look at their cache numbers in the logs during this issue's `/run`, and file a separate issue for any that miss.

## Acceptance criteria

- [ ] Each picked Claude model's minimum cached block size is checked and written in this issue
- [ ] `/run`: with the Reply on each Claude model (Haiku, Sonnet, Opus, Fable), the second of two messages in a row shows cached tokens in the logs
- [ ] `/run`: with the Reply on DeepSeek V4 Pro and Flash, the second of two messages in a row shows cached tokens in the logs
- [ ] Services with fixed instructions still get cache hits
- [ ] Cache numbers for Check-ins, memory processing and the keeping steps are looked at; any that miss get their own issue
- [ ] The language's checks pass

## Blocked by

- 06

## Comments
