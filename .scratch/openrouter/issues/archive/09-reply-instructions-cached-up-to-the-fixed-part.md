# 09 — Reply instructions cached up to the fixed part

Status: completed
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

- [x] Each picked Claude model's minimum cached block size is checked and written in this issue
- [x] `/run`: with the Reply on each Claude model (Haiku, Sonnet, Opus, Fable), the second of two messages in a row shows cached tokens in the logs
- [x] `/run`: with the Reply on DeepSeek V4 Pro and Flash, the second of two messages in a row shows cached tokens in the logs
- [x] Services with fixed instructions still get cache hits
- [x] Cache numbers for Check-ins, memory processing and the keeping steps are looked at; any that miss get their own issue
- [x] The language's checks pass

## Blocked by

- 06

## Comments

- 2026-11-25, done (branch `openrouter-09-reply-cache-fixed-part`). Evidence:
  - Minimum cached block size, from Anthropic's prompt caching docs (read 2026-11-25): **512 tokens** for each picked model, Haiku 5.5, Sonnet 5.5, Opus 5.5 and Fable 5.2. The Reply's tools plus fixed part are about 3,200 tokens (measured below), so every model reaches it.
  - Built: the `ChatModel` port's `generate` takes an optional `message_instructions` (empty by default) after `instructions`. `write_instructions` returns the two parts (`ReplyInstructions`): fixed = Persona, response prompt, priority order; for this message = the sections from "## 1.". The OpenRouter adapter (`to_system_message`) marks only the fixed part for a Claude model, in a text part of its own, and sends the per-message part after it unmarked; other models get the two joined, fixed part first. The direct DeepSeek adapter joins them too. The Model Call Log keeps them as one text. The cache line is now logged for every model, not only Claude, so DeepSeek's numbers can be seen.
  - Tests: `tests/adapters/test_openrouter_chat_model.py` (Claude gets only the fixed part marked; only per-message text is sent unmarked; DeepSeek gets them joined; a DeepSeek reply's cache numbers are logged), `tests/test_reply_priority_order.py` (the fixed part ends before the first section and is the same whatever the message needs; the composer gives the model the two parts), `tests/adapters/test_deepseek_chat_model.py`, `tests/adapters/test_eval_counting_chat_model.py`, `tests/test_model_call_log.py` (the log keeps one text).
  - `/run` (worktree stack, default `openrouter` adapter, database at 0097). Same way as issue 06: messages posted to the real `/telegram/webhook` of the real app inside the backend container, on the app database, through the eval `InProcessCompanion` (real repositories, real `OpenRouterChatModel`, a recording chat channel because fake chat IDs can't receive sends). Each cache line was tagged with its step by the run script. Two messages in a row per model; the Reply's lines:
    - `anthropic/claude-haiku-5.5`: first "read 0 of its 4062 prompt tokens from the cache and wrote 3216 to it", second "read 3216 of its 4082 ... and wrote 0".
    - `anthropic/claude-sonnet-5.5` (thinking on, see caveats): first "read 0 of its 4909 ... and wrote 3217", second "read 3217 of its 4962 ... and wrote 0".
    - `anthropic/claude-opus-5.5`: first "read 0 of its 4272 ... and wrote 3217", second "read 3217 of its 4474 ... and wrote 0".
    - `anthropic/claude-fable-5.2`: first "read 0 of its 4499 ... and wrote 3217", second "read 3217 of its 4601 ... and wrote 0".
    - `deepseek/deepseek-v4-pro-0813`: first "read 0 of its 3424 ... and wrote 0", second "read 1280 of its 3483".
    - `deepseek/deepseek-v4.1-flash-1017`: first "read 1280 of its 3536", second "read 1280 of its 3592".
    - Run again on the backend rebuilt from the final code after the rebase: Haiku read 3216 on both messages (of 6646 and 6653), Flash read 1280 and 1152. Replies arrived every time.
  - Services with fixed instructions, every service on Haiku, two messages in a row: Safeguard wrote 589 then read 589; Understanding wrote 1008 then read 1008; Reply plan wrote 5031 then read 5031.
  - Other services, every service on Haiku, two Conversations ended one after the other (clock moved past the quiet gap, scheduler tick run by hand) and three Check-in ticks a day apart. First end wrote, second end read the same number: memory processing (`conversation_end`) 1483, Life Threads 861, Patterns 1036, Curiosities 1848, Move outcomes 586, Portrait 517. Check-in: wrote 1209, then read 1209 twice. None missed, so no issue was filed for them.
  - Checks after rebasing on main (327c8c2): `pytest` 2229 passed, `ruff`, `ruff format --check`, `mypy` clean. No `web/` files changed, so the web checks were not run.
  - Code review: standards (a test helper's docstring, keyword arguments in the eval chat model), spec (tools that change per message, see caveats).
  - Docs: ADR-0028, `docs/DEPLOYMENT_GUIDE.md` and `docs/message-pipeline/README.md`. No new domain terms, so `CONTEXT.md` is unchanged.
  - Caveats:
    - **Sonnet 5.5 fails with thinking off** (400 "Reasoning is mandatory"), and the Reply's thinking is off by default. This was already so before this issue. The Sonnet run above was made with `response_thinking` on. Filed as issue 11.
    - **Tools come before the instructions, so a tool that changes breaks the cache.** `send_photo` and `ask_about_photo` list photos for the message in their descriptions. Two plain text messages hit; a turn where photos matter will not. Filed as issue 13.
    - DeepSeek V4 Pro read nothing for Safeguard, Understanding and Reply plan in one run, and did read in a later one. Filed as issue 12.
    - Not exercised in the run, so their cache numbers were not seen: Pattern tagging and matching, Personal Sticker keeping, Knowledge "when it helps", the photo viewer and the Day Summary.
    - DeepSeek reads less of the Reply than Claude (about 1,280 of 3,500 tokens), as it caches by itself in its own block sizes.
    - Every OpenRouter call now logs one cache line, so the backend prints a line per call for DeepSeek too.
    - The cache lasts 5 minutes, so a hit needs two Replies within that time.
    - The run set models with SQL and set them back after; no `*_model` setting holds a Claude name. It cost a little (two messages on each model, well under a dollar).

## Completion

- Completed: 2026-11-25
- Commit: 280322b (merge of openrouter-09-reply-cache-fixed-part; work in 7aca021 f3a867a eb35521)
