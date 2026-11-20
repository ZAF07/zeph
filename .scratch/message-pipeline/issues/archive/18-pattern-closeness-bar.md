# 18 — A closeness bar of its own for Patterns

Status: completed
Lane: B
Blocked by: 14

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

Since 14, a Pattern comes to mind directly when it is at least as close in meaning as the **Life Thread closeness bar** (62) to what the User means and their latest texts. Patterns are worded in general terms ("when something grabs them, everything else goes quiet") while messages are concrete, so they score lower than Threads do: in 14's live run a clear fit scored 0.53 on the message alone and only got in at 0.626 once the Understanding's meaning was added.

Give Patterns their own Admin-editable **Pattern closeness bar**, starting at **52** (Zaf's choice, 20 Nov 2026). The Life Thread closeness bar goes back to being for Threads only. Linked recall (through a Thread in mind) is unchanged.

Measured with the real embedder on the message text alone (20 Nov 2026): messages that clearly fit a Pattern scored 0.47–0.66; unrelated ones 0.35–0.61. So at 52 some small talk will bring a Pattern to mind too; the Reply Plan still decides whether to use or offer it.

## Design

An ordinary field row with a hint in the Memory section of Platform settings, next to the Pattern push-back wait, as in the "Field rows" sample in `AdminPersona`. No new parts.

## Acceptance criteria

- [x] Direct Pattern recall uses the new `pattern_closeness_percent` setting, not the Life Thread bar
- [x] The Life Thread closeness bar no longer affects Patterns, and its hint no longer mentions them
- [x] The new bar is Admin-editable with a hint, seeded at 52, and appears on existing installs without a migration
- [x] `docs/message-pipeline/README.md` describes what was built
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 14 — Patterns come to mind in replies (done, `0db0f64`)

## Comments

### Evidence (20 Nov 2026, branch `message-pipeline-18-pattern-closeness-bar`)

- **Default chosen from real scores.** The real embedder scored message text alone against three Patterns: fits 0.47–0.66, unrelated small talk 0.35–0.61. No bar separates them cleanly. Zaf chose 52.
- **Tests (red first, then green):**
  - `test_direct_pattern_recall_follows_the_pattern_bar_not_the_thread_bar`: with the Thread bar at 100, the Pattern comes in at Pattern bar 20 and stays out at 100.
  - `test_the_pattern_bar_is_admin_editable_with_a_hint_and_seeded_at_52`: also checks the Life Thread hint no longer mentions Patterns.
  - Vitest `shows and saves the Pattern closeness bar, with its hint`: failed without the row, passed with it.
- **Checks:**
  - `uv run pytest`: 1481 passed. `ruff check`, `ruff format --check` and `mypy src` are clean.
  - `pnpm lint`, `format:check` and `typecheck` are clean. `pnpm test`: 899 passed.
- **Running app (worktree stack, real DeepSeek and embedder):**
  - **Existing install:** the database had `pattern_closeness_percent = 52`. I deleted the row and restarted the backend. The row came back at 52 with the database still at 0073, so no migration is needed.
  - **Guitar message, no Thread, bars 62/52:** it scores 0.531 on its own text. The Pattern came to mind with "Life Threads in mind: None." and the Reply Plan used it (`patterns_used` set, not offered).
  - **"going to the gym after this", no Thread, bar 52:** the Pattern came to mind as noise, as the scores predicted. The Reply Plan didn't use it.
  - **Same gym message, same User, no Thread, bar 100:** "Patterns in mind: None."
  - **Dashboard:** the "Pattern closeness bar" row with its hint shows in Memory, between the brushed-off Thread wait and the pushed-back Pattern wait. It showed 52, saved as 57, and still read 57 after a reload. The database said 57 while the Life Thread bar stayed at 62. No page errors.
  - No design reference covers Platform settings, so the pixel test doesn't apply.
- **/code-review:**
  - Spec: no findings.
  - Standards: no hard findings. Kept the scores in the hint, because the Older Conversation and Move Outcome hints carry scores too.

## Completion

- Completed: 2026-11-20
- Commit: to be filled in after merge
