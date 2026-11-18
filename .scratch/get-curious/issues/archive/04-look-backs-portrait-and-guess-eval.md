# 04 — Look-backs, a Portrait without open questions, and the guess Eval case

Status: completed

## Parent

`.scratch/get-curious/PRD.md`

## What to build

- **Look-backs.** The Curiosity-keeping prompt adds roughly: "Something they vented about where Zeph only listened: a gentle look-back once it has had time to settle, asking how they see it now (e.g. 'how are you feeling about the thing with your boss now?'), with not_before at least the next day and sensitivity at least medium." So a vent comes back in a later Conversation or the Curiosity Check-in, never in the same few hours. A brushed-off look-back is handled by the existing Curiosity reactions. A Reflect Move is out of scope; it'll be grilled separately.
- **Portrait.** The Portrait prompt drops "Open questions Zeph is still curious about" and says to write only what Zeph is fairly sure of. What it only suspects lives in Curiosity guesses (issue 02, ADR-0017).
- **Running platform.** A migration reloads the Curiosity-keeping and Portrait prompts from the seed, as earlier prompt migrations do.
- **Eval.** One new Understanding Eval case in the seed: the made-up User has a waiting guess Curiosity, "their mum lives in Singapore", and mentions their mum. Expect Get curious, checking it gently, never stating it as fact. **Don't run it**; Evals cost money and the owner decides when. Get curious comes from issue 03, which may not be merged yet; the case only names it.

## Parallel work: avoid clashes

Issue 03 runs at the same time in another worktree.
- **Migration number:** use the next free number. If 03 merges first with the same number, renumber yours during the rebase and point it at theirs.
- **Files:** you own the Curiosity-keeping and Portrait prompts in the platform settings seed. 03 owns the Needs and Moves seeds.
- **Understanding Eval cases seed:** both add cases at the end. When rebasing, keep both.

## Acceptance criteria

- [x] The Curiosity-keeping prompt asks for look-backs as above; the Portrait prompt no longer asks for open questions and keeps only what Zeph is fairly sure of
- [x] The migration reloads both prompts from the seed (test, as for earlier prompt migrations)
- [x] A test with the scripted chat model shows the keeping step's look-back saved with its not_before and sensitivity
- [x] The guess Understanding Eval case is in the seed, with a made-up guess Curiosity, and loads; it is not run
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] `/run`: in the running app, end a real Conversation where the User vents and Zeph only listens, and see a look-back Curiosity saved with not_before at least the next day. See the rewritten Portrait has no open questions. Shift timestamps instead of waiting

## Blocked by

- `.scratch/get-curious/issues/02-curiosity-guesses.md`

## Comments

- 2026-11-18 evidence, per criterion:
  - Prompts: the seed's Curiosity-keeping prompt has a look-back bullet ("Something they vented about where Zeph only listened: a gentle look-back ... not_before at least the next day and sensitivity at least medium"). The Portrait prompt drops "Open questions Zeph is still curious about" and says "Write only what Zeph is fairly sure of; leave out what it only suspects." Tests: `test_the_seeded_keeping_prompt_asks_for_look_backs_a_day_later_at_least_medium`, `test_the_portrait_is_written_from_what_zeph_is_sure_of_without_open_questions` (checks what the Portrait call was told).
  - Migration: `0060_look_backs_and_sure_portrait.py` (after issue 01's `0059`; first written as 0059 and renumbered on rebase) deletes both stored prompts so they reload from the seed. Test: `test_the_look_backs_migration_reloads_the_keeping_and_portrait_prompts`.
  - Scripted chat model: `test_a_look_back_from_the_keeping_step_is_saved_with_its_day_and_sensitivity` (vent, keeper given the look-back text, row saved with `not_before` the next day and `medium`). Nothing in code forces the day or sensitivity; the issue asks only for the prompt.
  - Eval case: `guess-checked-gently` in the Understanding seed. Its Curiosity holds the guess "their mum lives in Singapore" (how sure: medium), and the `why` only hints at it (her mum flew home, landing at Changi). The User mentions her mum; expected lead Move `Get curious` and rule `checks_guess_gently`. Eval Curiosities can now hold `guess` and `how_sure` (case file, Admin case form shape, made-up memory). Tests: `test_the_understanding_cases_check_a_guess_gently_with_get_curious`, `test_a_made_up_guess_curiosity_is_read_and_saved_with_how_sure_zeph_is`, and the existing every-seed-case-fits tests. **Not run**, since Evals cost money. Get curious comes from issue 03, so a run before 03 merges would fail the lead Move check.
  - Checks: `uv run ruff check .` all passed, `uv run ruff format --check .` 454 files formatted, `uv run mypy src` no issues in 184 files, `uv run pytest` 1313 passed (after rebasing on issue 01). No `web/` files changed.
- 2026-11-18 review: Standards found one hard issue: a migration number clash with issue 01's 0059, fixed by renumbering to 0060. Also fixed: a shared low/medium/high options list and a `to_eval_curiosity` helper. Spec found the case's `why` said the User told Zeph outright, so it wasn't really a guess; reworded to a hint. Left as is: the duplicated prompt-key SQL text in the test (minor), and the Admin case form's guess fields (needed so editing a case on the Dashboard doesn't drop the guess).
- 2026-11-18 `/run` (worktree stack, fresh database migrated to 0060 on start, issue 01's `asks_a_question` column present, both prompts reseeded; the main stack was down, so a test User was added with SQL). A real Conversation went through `/telegram/webhook` with `create_app`, real repositories, DeepSeek and fastembed inside a backend container; only Telegram (recording channel), the timer and the scheduler were swapped. The Conversation end was brought on by moving `last_message_at` back two hours and ticking the scheduler.
  - The User vented about a boss taking credit for their rollout plan, and said "I don't want advice right now, I just needed to say it to someone". The Understanding picked Be heard with no lead Move, so Zeph only listened.
  - At the end, the keeper answered `"ask": "How are you feeling about the thing with your boss now — has it settled at all?", "not_before": "2026-11-19", "sensitivity": "medium"` on 2026-11-18. The curiosities row is `not_before = 2026-11-19`, `sensitivity = 'medium'`, `waiting`.
  - The rewritten Portrait has no open questions (it covers the boss situation, venting over advice, no Goals yet). The Portrait call's instructions contain "fairly sure" and not "open questions".
- 2026-11-18 domain model: CONTEXT.md's Curiosity entry now says a vent where the Companion only listened becomes a look-back, asked no sooner than the next day, at least medium sensitivity. The User Portrait entry and ADR-0017 already covered the Portrait.

## Completion

- Completed: 2026-11-18
- Commits: see below once merged

