# 03 — Next Move in mind

Status: completed
Lane: A

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane B is changing some of the same files (migrations, the seed settings file, the Understanding module). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

The Companion works through a sequence of Moves over a Conversation.

- Each Understanding may hold a next Move in mind, with why (e.g. "Next: Research, once I know their requirements"). It must be one the Need allows now or could plausibly allow later; an unknown Move is dropped.
- Understandings store the next Move and why. The Model Call Log shape shows the next Move's name.
- Each Understanding sees the earlier ones in the Conversation with their lead, supporting and next Moves, so it can follow the next Move or drop it when things change (e.g. the User reacted badly).
- The seed Understanding prompt explains the next Move.

## Acceptance criteria

- [x] An Understanding's next Move and why are stored and shown to the next Understanding in the same Conversation.
- [x] Earlier Moves are shown to later Understandings.
- [x] The Model Call Log shows the next Move's name, no content.
- [x] Webhook-seam tests (prior art: the Understanding tests); backend checks pass.
- [x] `/run`: a multi-Message chat shows a next Move held and then made in a later reply.

## Blocked by

- `.scratch/moves/issues/01-moves-shape-replies.md`

## Comments

### 2026-11-17 — done (agent, branch `moves-03-next-move`)

What changed:
- The Understanding form gains `next_move` and `next_move_why`. A next Move is kept when it is a Move that can be made for the User (its needed Feature works) and that some Need allows, so one the current Need rules out (e.g. Plan steps while they're being heard) is kept for later. An unknown or odd one is dropped with its why. The fallback Understanding has none.
- Understandings store `next_move` and `next_move_why` (migration `0054_next_move`, on issue 05's 0053). An empty why is stored as none.
- Earlier Understandings shown to the next one now list their lead, supporting and next Move (with why), e.g. "- Need: Advice; lead Move: Research; supporting Move: Suggest; … Next Move in mind: Plan steps, once they've picked a host."
- Model Call Log: `UnderstandingShape.next_move` (name only), in the admin API and the Dashboard trace facts ("Next Move").
- Seed Understanding prompt explains the next Move: work through a sequence, make it when its moment comes, keep holding it, or drop it when things change (e.g. they reacted badly). Migration 0054 deletes the stored `understanding_prompt` so it reloads from the seed on next start (prior art: 0050).

Decisions made while building:
- "Could plausibly allow later" = some Need allows it. A Move whose needed Feature doesn't work right now (Research with Web Search off or its limit used up) is dropped as a next Move too, since the PRD says Research is never offered then.
- The next Move doesn't go into the reply instructions; only later Understandings see it.

Evidence per acceptance criterion:
- Next Move and why stored and shown to the next Understanding: `tests/test_next_move.py::test_the_next_move_and_why_are_stored_and_shown_to_the_next_understanding`, plus `test_a_next_move_the_need_rules_out_now_is_kept_for_later`, `test_an_unknown_or_odd_next_move_is_dropped_with_its_why`, `test_a_next_move_that_cant_be_made_for_the_user_is_dropped`, `test_the_fallback_understanding_holds_no_next_move`.
- Earlier Moves shown to later Understandings: `test_earlier_lead_and_supporting_moves_are_shown_to_later_understandings`.
- Model Call Log shows the next Move's name, no content: `tests/test_model_call_log.py::test_a_plain_users_understanding_shows_its_shape_and_never_its_words` expects `next_move: Reframe` and that the why ("anger has eased") is in neither the response nor the stored rows; `web/src/lib/model-calls.test.ts` ("Next Move" fact, "None" when absent).
- Migration: `tests/test_moves_migration.py::test_the_next_move_migration_reloads_the_understanding_prompt`. Worktree stack, reset to 0052 so the real chain ran (issue 05's 0053, then 0054): `alembic_version` 0054, the live `understanding_prompt` contains `next_move_why`.
- Checks (after rebasing on origin/main b429ae3, with issue 05 merged, and review fixes): `ruff check`, `ruff format --check`, `mypy` clean (178 files); `pytest` 1239 passed; web `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 68 files / 479 passed.
- `/run` (worktree stack 3010/8010/5442, inside the backend container: real repositories, DeepSeek chat model, Tavily web search, embedder and clock; only the chat channel, auth verifier, scheduler and timer are fakes, because Telegram can't reach a made-up chat). The PRD's hosting chat in three Messages ("going around in circles on where to host my app" → "small Next.js app … SGD 15-20 a month … managed Postgres" → "ok railway it is, I just signed up. what do I actually do now?"):
  - Run on the final code: Understandings `Advice / Research + Suggest, next Plan steps ("once they've picked a host from the comparison, to get the app deployed")` → `Advice / Research + Suggest, next Plan steps ("once they've picked a host …")` → `Advice / Plan steps + Suggest, next Push ("once the steps are laid out, to keep them from stalling …")`. The held Plan steps was made in the 3rd reply: ordered setup steps on Railway and what "done" looks like. Earlier runs gave the same shape (Plan steps held from Message 1, made in Message 3).
  - Run again after rebasing on issue 05 (merged code, migrations 0053 → 0054 run on the stack): `Advice / Research + Suggest, next Plan steps ("once they've picked a host, to map out the deploy")` → `Advice / Suggest, next Plan steps` → `Advice / Plan steps + Suggest, next Push`. Plan steps made in the 3rd reply (six ordered steps and "done looks like").
  - Model Call Log shapes show `next_move` (Plan steps, Plan steps, Push) and no words.

Code review (standards and spec): no hard violations, nothing missing. Fixed: an empty why is stored as none (was `""`); `read_move_name` → `read_form_text`, `allowed_later` → `allowed_by_any_need`. Kept: `next_move`/`next_move_why` travel as two fields, like lead/support; Research with Web Search off is dropped as a next Move (decision above).

Caveats:
- Migration 0054 replaces any Dashboard edit to the Understanding prompt with the seed wording (fine while the owner is the only User).
- Issue 05 (Lane B) landed first with its own 0053, so this issue's migration became 0054 revising it. The rebase had no text conflicts; the merged Understanding prompt and module keep both lanes' changes (Move Outcomes and the next Move).
- The Plan steps reply used a numbered list, which the Persona forbids (already noted in issue 01; Evals in issue 07).
- Shared files touched: the seed settings file, `tests/fakes.py`, `tables.py`, and a new migration.
