# 12 — DeepSeek V4 Pro reads nothing from its cache for Safeguard, Understanding and Reply plan

Status: needs-triage

## Parent

`.scratch/openrouter/PRD.md` (user stories 19, 20). Found on 2026-11-25, during the `/run` of issue 09.

## What was seen

With Safeguard, Understanding and Reply plan on `deepseek/deepseek-v4-pro-0813` (thinking on), two messages in a row about a minute apart both read 0 prompt tokens from the cache (prompts of 1,166 to 8,330 tokens, with fixed instructions at the start).

The same three services on `deepseek/deepseek-v4.1-flash-1017` read from the cache every time (e.g. Reply plan read 3,584 of 6,367). The Reply on Pro (thinking off) also read from it on the second message (1,280 of 3,483).

DeepSeek caches by itself, so there is no marker of ours to fix. Open questions: does Pro skip the cache when thinking is on, does it need more calls or more time before it reads, or does OpenRouter not report it for Pro?

## Acceptance criteria

- [ ] The cause is found and written here (try Pro with thinking off, and more than two calls)
- [ ] If we can make it hit, it is fixed; if not, ADR-0028 says so

## Comments
