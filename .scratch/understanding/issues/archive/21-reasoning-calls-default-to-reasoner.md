# 21 — Calls that need reasoning default to deepseek-reasoner

Status: completed

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

- [x] The 7 settings above default to `deepseek-reasoner` in the seed file (`tests/test_model_defaults.py`)
- [x] Each of those calls works on reasoner in the running app (`/run`: all 7 ran, saved reasoning and data)
- [x] No eval case passes less often than before; flaky cases mostly become steady (before/after table in Comments) — **waived by the user for delete-my-data** (6/8 → 4/8, caused by this change; fix moved to issue 18); flaky cases partly steadier
- [x] Reply-path time and cost change reported (3.5 s → 6.2 s, ×1.8; about +20% cost per Message)
- [x] `make check-python` passes (after rebase on `e4505b9`: ruff, format, mypy, 947 passed)
- [x] The local main database has the new defaults (`UPDATE 7`, shown to and approved by the user first)

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

- 2026-11-15 (after `/code-review`, filling evidence gaps):
  - **Money:** both modes are one model billed the same per token ([Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing): `deepseek-flash` $0.30 per 1M input tokens (cache miss) and $1.20 per 1M output at peak, half off-peak), so the cost change is the extra output tokens. Per Message on the reply path (timing run above): about 5,600 tokens in either way, out 189 → 536, so about $0.0019 → $0.0023 at peak (**about +20%, +$0.0004 per Message**). A whole `make eval` run: +26,000 output tokens, about +$0.03.
  - **Calls after a Conversation** (/run on reasoner, tokens in / out): conversation_end 1,276 / 750, life_threads 843 / 1,605, curiosities 1,176 / 887, portrait 567 / 902, check_in 1,087 / 508. For comparison, on chat in the local main DB: curiosities 109 out, life_threads 120 out, portrait 299 out (1.3–3.1 s); conversation_end on reasoner took 5.4 s there. These run in the background, not on the reply path; the /run's own durations read 0 because its clock is faked.
  - **Waiver:** the "no eval case passes less often" box is not met for delete-my-data (6/8 → 4/8, caused by this change). The user chose to ship and fix it in issue 18. "Flaky cases mostly become steady" is partly met: are-you-human and memory-off became steady and the two cases that always failed (advice-is-asked-for, goal-slip) now always pass; strong-mood, vent, struggling and forget-why-here stay flaky.
  - **Reply on reasoner with tools** (the local main DB's Admin set `response_model` to reasoner): checked in the worktree, "please don't message me after 9pm" called `change_quiet_hours`, the tool result went back and the reply came, no error, 2 of 2.
  - `make check-python` passed before review: ruff, ruff format (230 files), mypy (123 source files), pytest 946 passed. Rerun after rebase below.

## Completion

- Completed: 2026-11-15
- Commits: `426d7ed` (reasoner defaults, test, issues 18 and 22, eval README), `ab58665` (review fixes and evidence), `277fa7f` (archive); merged to main in `db2b03b`
