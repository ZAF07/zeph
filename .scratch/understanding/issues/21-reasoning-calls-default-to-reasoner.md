# 21 — Calls that need reasoning default to deepseek-reasoner

Status: ready-for-agent

## What

Every model setting in `src/companion/seed/platform_settings.yaml` defaults to `deepseek-chat`, which isn't built for reasoning. Evals are inconsistent from run to run (e.g. issue 18). Calls that make judgments should default to `deepseek-reasoner`. Admins can still pick any model on the Dashboard.

## Decisions (grilling, 2026-11-15)

- **Reasoner by default** for: `understanding_model`, `safeguard_model`, `memory_processing_model`, `life_thread_keeping_model`, `portrait_model`, `curiosity_keeping_model`, `check_in_model`.
- **Stay on `deepseek-chat`:** `response_model` (writing in voice), `knowledge_when_it_helps_model`, `personal_sticker_keeping_model`. `photo_model` is unchanged.
- **Slower replies are accepted.** Understanding and Safeguard are on the reply path; conversations must be solid more than fast. Flag it if reply time more than doubles.
- **Seed file only, no migration** (same reason as issue 17: not live, Admins own settings in production). At the end, reset these 7 settings in the local main database with a one-off command, shown to the User before it runs.
- **Make it work with reasoner**: if a call breaks on reasoner (tool calls, JSON output, `tool_choice="none"`, passing `reasoning_content` back), fix the adapter simply; if that isn't simple, keep that call on chat and ask.
- **Measure (costs money: ~6 full eval runs):** run `make eval` 3 times on today's defaults, then 3 times on reasoner, with the stack down so the seed file is used. Record each case's pass rate and time and tokens per call.

## Acceptance criteria

- [ ] The 7 settings above default to `deepseek-reasoner` in the seed file
- [ ] Each of those calls works on reasoner in the running app (`/run`)
- [ ] No eval case passes less often than before; flaky cases mostly become steady (before/after table in Comments)
- [ ] Reply-path time and cost change reported
- [ ] `make check-python` passes
- [ ] The local main database has the new defaults

## Comments
