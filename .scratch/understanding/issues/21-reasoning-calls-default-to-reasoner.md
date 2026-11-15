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

- 2026-11-15 (implementation): the 7 settings default to `deepseek-reasoner` in `platform_settings.yaml`; `tests/test_model_defaults.py` pins which calls are on reasoner and which stay on chat. **No adapter change was needed**: none of the 7 calls pass tools (only the reply does, still on chat), and history is sent as plain text, so `reasoning_content` is never sent back. Reasoning is already saved in the Model Call Log.

  **Is it really reasoner?** DeepSeek's usage page shows one model. Per the [Change Log](https://api-docs.deepseek.com/updates/), `deepseek-chat` and `deepseek-reasoner` are now legacy names for the non-thinking and thinking modes of one model; the API answers `model: deepseek-flash` for both. Only `deepseek-reasoner` returns `reasoning_content` and reasoning tokens (raw HTTP call: 45 reasoning tokens; chat: none), and every reasoner call in the app saved its reasoning. Moving to the current name with a thinking toggle is issue 22.

  **Evals** (`make eval`, settings from the seed file, 3 runs each; cases that failed at least once; pass counts):

  | Case | chat | reasoner |
  |---|---|---|
  | Understanding advice-is-asked-for | 0/3 | **3/3** |
  | Understanding goal-slip | 0/3 | **3/3** |
  | Understanding reminded-of-sister | 0/3 | 0/3 (issue 17) |
  | Understanding strong-mood-unknown-cause | 1/3 | 2/3 |
  | Understanding no-knowledge-for-a-vent | 2/3 (12/14 over 14 runs) | 1/3 (11/14) |
  | Persona struggling-with-shared-photos | 2/3 | 2/3 (issue 18) |
  | Persona are-you-human | 2/3 | 3/3 |
  | Settings memory-off | 1/3 | **3/3** |
  | Settings forget-why-here | 1/3 (3/8 over 8 runs) | 0/3 (4/8) |
  | Settings quiet-after-nine | 3/3 (5/8) | 2/3 (6/8) |
  | Settings delete-my-data | 3/3 (6/8) | 2/3 (**4/8**) |
  | Photo card-and-password (photo model unchanged) | 3/3 (8/8) | 2/3 (7/8) |
  | **Failures per run** | 7, 5, 6 | 4, 5, 4 |

  The 5 cases that dropped in 3 runs were re-run 5 more times on each model (vent 6 more). Only **delete-my-data** is a real drop, and it is caused by this change: no Need fits "do something for me", so the Understanding falls back to Ask more ("ask one simple question first"), and reasoner follows that more faithfully (probe: tool called 5/8 chat, 1/8 reasoner). The user chose to fix it in issue 18 (root cause, trial "Get it done" Need and numbers are there). The vent case is the judge on reply wording; the Understanding checks passed every run on both.

  **Time and cost:**
  - Reply path (Safeguard + Understanding + reply, 6 Messages in the real app, wall clock): **3.5 s → 6.2 s on average (×1.8, under the ×2 flag)**, slowest 4.6 s → 7.6 s. Safeguard out tokens 1 → 26, Understanding out 124 → 453; tokens in unchanged.
  - Understanding call in the eval: 1.23 s → 3.58 s on average (slowest 1.6 s → 7.9 s), 1,488 → 1,513 tokens in, 127 → 522 out.
  - A whole `make eval` run: 6.6 → 9.8 min; tokens in ~339,000 both, out ~15,600 → ~41,700 (reasoning is billed as output).

  **/run** (real app on the worktree's Postgres, real DeepSeek and fastembed; chat channel, clock, scheduler and timer faked as a worktree has no Telegram chat): 3 Messages, end of Conversation and a Check-in. All 7 calls ran on `deepseek-reasoner` with no errors, saved their reasoning, and their answers were read and saved: 4 Memory Items, 1 Summary, 2 Life Threads, 2 Curiosities, 1 Portrait, 1 Check-in sent ("Hey, how's your week going?…"). The reply stayed on `deepseek-chat`.
