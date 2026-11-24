# 06 — Prompt caching for Claude

Status: completed
Blocked by: 05

## Parent

`.scratch/openrouter/PRD.md` (user stories 19, 20).

## What to build

Calls to Claude models through OpenRouter mark the system instructions with `cache_control`, so long repeated prompts are cached. DeepSeek models get no marker. The adapter reads the cached-token count from the reply's usage and logs it, so caching can be checked. Bug reports in other libraries show markers being dropped on the OpenAI-format path, so the contract test must prove real cache hits.

## Acceptance criteria

- [x] Adapter tests: Claude models get `cache_control` on the system instructions; DeepSeek models don't; cached tokens are read from usage and logged
- [x] Contract test (remind the operator first): two Claude calls with the same long instructions; the second shows cached tokens
- [x] `/run`: with a core service on Claude, two messages in a row show cached tokens in the logs
- [x] `pytest`, `ruff`, `ruff format`, `mypy` pass

## Blocked by

- 05

## Comments

- 2026-11-25, done (branch `openrouter-06-prompt-caching`). Evidence:
  - Built: for a Claude model (any `anthropic/` name) the OpenRouter adapter sends the system instructions as one text part with `cache_control: {type: ephemeral}` (kept 5 minutes by Anthropic). Replies, every tool round and photos all get it, because the marker is added where the request is built. Other models' requests are unchanged. For each Claude call the adapter logs at INFO: "A call to <model> read N of its M prompt tokens from the cache and wrote W to it" (from `usage.prompt_tokens_details`). Nothing printed INFO logs, so the backend now prints this adapter's logs (`show_prompt_cache_logs` in `main.py`).
  - Adapter tests (`tests/adapters/test_openrouter_chat_model.py`, `test_openrouter_photo_viewer.py`): a Claude model gets the marker on the instructions; the marker stays on every tool round; a DeepSeek model gets none; a Claude photo call gets it; empty instructions are sent unmarked (Anthropic refuses an empty text part); the cached tokens of a Claude reply are logged; a reply that says nothing about the cache is logged as 0; a DeepSeek reply logs nothing. `tests/test_config.py`: the backend prints the adapter's INFO logs.
  - Contract test (operator reminded in the session that it costs a little; four runs of two haiku calls, under a cent in all): `test_openrouter_reads_a_claude_models_instructions_from_the_cache_the_second_time` passed against the real API. First call "read 0 of its 11421 prompt tokens from the cache and wrote 11412 to it", second "read 11412 of its 11421 ... and wrote 0". So the marker is not dropped on this path. The other seven OpenRouter contract tests (reasoning, tools, photo, on DeepSeek and Claude) also passed with the marker in place.
  - `/run` (worktree stack, default `openrouter` adapter, final code after the last rebase, database at 0093). Messages were posted to the real `/telegram/webhook` of the real app inside the backend container, on the app database, through the eval `InProcessCompanion`: real repositories and the real `OpenRouterChatModel`, with a recording chat channel because fake chat IDs can't receive sends.
    - Reply plan on `anthropic/claude-haiku-5.5`, two messages in a row: first "read 0 of its 8048 prompt tokens from the cache and wrote 4674 to it", second "read 4674 of its 8249 prompt tokens from the cache and wrote 0 to it". Run again two minutes later: both messages read 4674 (of 8649 and 8668). Run once more on the backend rebuilt after the last rebase (with issue 08's change to the request): first "read 0 of its 8685 ... and wrote 4674", second "read 4674 of its 8838 ... and wrote 0". Replies arrived each time, and the Model Call Log shows reply_plan on haiku and the other steps on DeepSeek, no errors.
    - The real app factory (`build_production_app`, run inside the backend container) leaves the adapter's logger at INFO with one handler, and a line logged there is printed once.
    - The service was set back after each run; no `*_model` setting holds a Claude name.
  - Checks, after rebasing on main (e696d66, which has issue 08's Opus and Fable models): `pytest` 2111 passed, `ruff`, `ruff format --check`, `mypy` clean. No `web/` files changed, so the web checks were not run.
  - Code review: standards (no hard violations; one helper now prints a logger for both the Model Call Log and this adapter, clearer names), spec (the contract test now reads only the cache lines, so a credits warning can't break it; empty instructions are sent unmarked).
  - Docs: ADR-0028 and `docs/DEPLOYMENT_GUIDE.md` say how caching works and how to check it.
  - Caveats:
    - **The Reply gets no cache hits on Claude.** Its instructions end with the plan for that one message, so they are written to the cache every time and never read (first Reply: read 0, wrote 3965; second: read 0, wrote 3859). A cache write costs about a quarter more than plain input, so the Reply on Claude costs a little more with caching than without. Safeguard, Understanding and Reply plan have fixed instructions and are fine. Filed as issue 09 (`needs-triage`), with the open question of how the adapter learns where the fixed part ends.
    - Opus 5.5 and Fable 5.2 (issue 08) are `anthropic/` names, so they get the marker too. Only haiku was called here.
    - The cache lasts 5 minutes, so a hit needs two calls of the same service within that time.
    - The `/run` set the service's model with SQL, not through the Dashboard (the Dashboard path was checked in issue 05).
    - The cached-token count is only in the backend logs, not in the Model Call Log or the Dashboard.

## Completion

- Completed: 2026-11-25
- Commit: <to be filled in after the merge>
