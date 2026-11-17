# 06 — Unmade next Move becomes a Curiosity

Status: completed
Lane: A

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane B is changing some of the same files (the seed settings file, the Conversation-end work). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

A follow-up the Companion meant to make comes back naturally later.

- When a Conversation ends with a next Move it had in mind but never made, Curiosity keeping is shown that next Move and why, and may turn it into a Curiosity (e.g. "did they decide what 'done' means for internal testing?").
- From there it works like any Curiosity: raised in a later chat or a Curiosity Check-in. No other state carries across Conversations.
- The seed Curiosity keeping prompt explains this.

## Acceptance criteria

- [x] Curiosity keeping receives an unmade next Move and its why; a made one isn't passed.
- [x] Nothing is passed while the Curiosities Feature doesn't work or User Memory is off (the existing rules).
- [x] Conversation-end-seam tests (prior art: the Curiosity tests); backend checks pass.
- [x] `/run`: a Conversation that ends with an unmade next Move produces a matching Curiosity.

## Blocked by

- `.scratch/moves/issues/03-next-move-in-mind.md`

## Comments

### 2026-11-17 — done (agent, branch `moves-06-unmade-next-move`)

What changed:
- `CuriosityKeeper.keep_from` reads the Conversation's Understandings, and the keeping model is shown a new section: "A next Move Zeph had in mind but never made:" followed by e.g. "Plan steps, once they've settled on a host." or "None.". The model turns it into a Curiosity through the usual new-Curiosity path, so from then on it works like any other (raised in a later chat or a Curiosity Check-in).
- `describe_unmade_next_move` (in `core/curiosities.py`) takes only the newest Understanding's next Move. An earlier one was made or dropped by the Understanding after it, so it isn't passed.
- The seed Curiosity keeping prompt explains it: write a Curiosity about where they've got to, not about the help itself (e.g. "did they get the app deployed?"), and leave it out if the Conversation shows it no longer fits. Migration `0055_unmade_next_move_curiosity` deletes the stored `curiosity_keeping_prompt` so it reloads from the seed on next start (prior art: 0054).
- The existing gating is untouched. Curiosity keeping runs only while User Memory and Curiosities work, so nothing is passed otherwise.

Decision made while building:
- "Unmade" means the next Move the newest Understanding still held when the Conversation ended (CONTEXT.md: the next Understanding "follows or drops" it).

Evidence per acceptance criterion:
- Unmade next Move and why passed, a made one not passed: `tests/test_unmade_next_move.py::test_an_unmade_next_move_reaches_curiosity_keeping_and_can_become_one` (keeper sees "Plan steps, once they've picked a host." and the Curiosity it writes is saved), `test_a_next_move_made_in_a_later_reply_is_not_passed` and `test_a_conversation_with_no_next_move_passes_none` (keeper sees "None.").
- Nothing passed while Curiosities is off or User Memory is off: `test_with_curiosities_off_no_unmade_next_move_is_passed` and `test_with_user_memory_off_no_unmade_next_move_is_passed`. Curiosity keeping is never called and no Curiosity is saved.
- Conversation-end-seam tests, backend checks: the tests above, plus `tests/test_moves_migration.py::test_the_unmade_next_move_migration_reloads_the_curiosity_keeping_prompt`. On the final code: `ruff check`, `ruff format --check`, `mypy` clean (178 files); `pytest` 1245 passed. No web changes.
- `/run` (worktree stack 3020/8020/5452). Migrations ran to `0055` on the stack, and the live `curiosity_keeping_prompt` has the new wording. The run was inside the backend container: real repositories, DeepSeek chat model, Tavily web search and embedder. Only the chat channel, timer and scheduler were fakes, because Telegram can't reach a made-up chat, and the real clock was moved 3 hours on to pass the quiet gap. A plain User sent the hosting chat in two Messages: "going around in circles on where to host my app", then "small next.js app, budget SGD 15-20 a month, needs managed postgres".
  - Understandings: `Advice / Suggest + Research, next Plan steps ("once I know their stack, budget and expected traffic …")` → `Advice / Suggest + Research, next Plan steps ("once they've settled on a host, a short deploy checklist will finish it off")`.
  - At Conversation end, the one Curiosity keeping call was shown "A next Move Zeph had in mind but never made: Plan steps, once they've settled on a host, a short deploy checklist will finish it off."
  - Curiosity saved: "Did you end up going with Railway for the app, or did Render's flat bill win you over?" (why: Zeph wonders whether they actually settled), not before 2026-11-18, sensitivity low, waiting.

Code review (standards and spec): no hard violations, nothing missing, no scope creep. Fixed: the unmade next Move is loaded into a named variable before asking, like the other inputs. Kept: the two-line "Move, why." wording is close to `format_earlier_understanding` in `understanding.py`; it isn't shared because `understanding.py` already imports from `curiosities.py`.

Caveats:
- If the last Message got a fallback Understanding (the model call failed), it holds no next Move, so an earlier held one is lost. Stored Understandings don't record that they were a fallback, and fixing this would need a schema change for a rare failure.
- Migration 0055 replaces any Dashboard edit to the Curiosity keeping prompt with the seed wording (fine while the owner is the only User).
- Shared files touched: the seed settings file and a new migration (0055, on 0054). Lane B's issue 08 was in progress at the same time; if it adds a migration, it must point at 0055.

## Completion

- Completed: 2026-11-17
- Commit: `9104578` — Moves issue 06: an unmade next Move may become a Curiosity — Curiosity keeping is shown the next Move the newest Understanding still held when the Conversation ended, with why; the seed prompt explains it; migration 0055 reloads it
- Commit: `abf3aa6` — Moves issue 06: review fix — load the unmade next Move into a named variable before asking, like the other inputs
