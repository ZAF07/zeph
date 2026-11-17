# 01 — Moves shape replies

Status: completed
Lane: solo (lands before any other Moves issue)

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **This issue runs alone and must be merged to main before Lane A (02, 03, 06, 07) and Lane B (04, 05, 08) start.** Keep it to what's below, so both lanes build on one shared base.

## What to build

The tracer bullet. The Companion picks Moves before each reply, and they change what it does.

- Moves exist as Admin-managed data (ADR-0004, ADR-0016): name (unique ignoring case), when it fits, how to do it, list position. Starter Moves in the seed: Calm, Ground, Reframe, Mirror, Suggest, Plan steps, Push, Research.
- Each Need has ruled-out Moves. Starter rule-outs in the seed: Be heard rules out Reframe, Suggest, Plan steps, Push, Research; Think it through rules out Suggest, Research; Just chatting rules out Calm, Ground, Reframe, Mirror, Plan steps, Push; Get it done and Ask more rule out all.
- A migration adds the starter Moves and rule-outs to a database that has Needs but no Moves (follow the Check-in Kinds migration).
- The Understanding is shown the Moves each Need allows and picks a lead Move and at most one supporting Move, or none. An unknown or disallowed Move is dropped. The fallback Understanding has no Moves.
- The lead and supporting Moves' "how to do it" go into the reply guidance after the Need's "how to reply".
- Understandings store the lead and supporting Move names. The Model Call Log shape shows them (never content for Users).
- Seed wording (these are the defaults): the Persona says the Companion has real views and says them, and is here to help the User grow and get unstuck (keep "follow their lead" for topics); the web search tool description drops "not for advice" and allows practical requirements such as a budget in queries, never personal details; the Understanding prompt explains Moves; any Need wording needed to separate stance from action.

No Admin page yet (issue 02). Web tools stay offered on every reply as today.

## Acceptance criteria

- [x] Starter Moves and rule-outs load on a fresh install, and the migration adds them to an existing database with no Moves (and adds nothing when Moves exist).
- [x] A Telegram Message read as Be heard is never given Push, Suggest, Plan steps, Research or Reframe; a disallowed or unknown Move in the model's answer is dropped.
- [x] The picked lead and supporting Moves' "how to do it" reach the reply instructions.
- [x] Understandings store the Moves, and the Model Call Log shows their names without content.
- [x] Seed Persona, web search tool description, Understanding prompt and Needs carry the new wording.
- [x] Tests at the Telegram webhook seam (prior art: the Understanding tests) and the migration seam; `pytest`, `ruff`, `ruff format`, `mypy` pass.
- [x] `/run`: in the running app, the hosting chat from the PRD leads to a Research or Suggest Move and a reply that names real options.

## Blocked by

None - can start immediately

## Comments

### 2026-11-17 — done (agent, branch `moves-01-shape-replies`)

What changed:
- Moves are Admin-managed data: `moves` table (name unique ignoring case, `moves_name_ignoring_case` index), `need_ruled_out_moves` link table (deleting a Move or Need clears its rule-outs by cascade), `MoveRepository` port + `PostgresMoveRepository`; `Need.ruled_out_move_ids`.
- Seed: `seed/moves.yaml` (8 starter Moves); `seed/needs.yaml` gains `ruled_out_moves` per Need; `seed_moves` loads both on first run (nothing once any Move exists). Wired into prestart, the test fixtures and the Eval environment.
- Migration `0050_moves`: tables, `understandings.lead_move`/`support_move`; adds the starter Moves and rule-outs when there are Needs but no Moves. The starter rows are written into the migration itself (review fix), so later seed changes don't change it. It also sets the new Advice and Accountability "how to reply" and deletes `persona`, `understanding_prompt`, `web_search_tool_description` and `reply_web_search_instructions` so they reload from the seed on next start (prior art: 0039).
- Understanding (`core/understanding.py`): shown every Move and "Moves each Need allows"; `pick_moves` keeps only Moves the picked Need allows (any case); unknown, ruled-out or same-as-lead Moves are dropped; the fallback form has none. Reply guidance adds "Lead with: X. <how to do it>" and "Support it with: Y. …" after the Need's "how to reply".
- Model Call Log: `UnderstandingShape.lead_move`/`support_move`, in the admin API response and the Dashboard trace facts ("Lead Move", "Supporting Move").
- Eval Run snapshots keep each Need's ruled-out Move IDs (the snapshot test caught that they were dropped).
- Seed wording: Persona (helps them grow and get unstuck; has real views and says them; offers help rather than handing the work back; "follow their lead" kept for topics); web search tool description (practical legwork allowed, budget/requirements in queries, never personal details; "not for advice" gone); `reply_web_search_instructions` (also for finding and comparing options); Understanding prompt (`lead_move`, `support_move`); Advice and Accountability "how to reply" now set stance only.

Decisions made while building:
- A supporting Move left without a lead (lead unknown or ruled out) becomes the lead: a support with no lead means nothing.
- The raw form keeps the model's Move text (`""` for none), like `need`/`nuance`; the stored Understanding and the shape hold the checked names (`None` for none).
- Earlier Understandings shown to the next one don't list Moves yet (issue 03). No Feature gating yet: Research is offered whenever a Need allows it (issue 02).

Evidence per acceptance criterion:
- Starter Moves and rule-outs on a fresh install, and the migration: `tests/test_moves.py::test_a_fresh_install_has_the_starter_moves_and_rule_outs_in_order`; `tests/test_moves_migration.py` (added to a database with Needs and no Moves, plus new Need wording and settings reloaded; nothing added to a database without Needs; seeding adds nothing once Moves exist). Fresh worktree stack: 8 Moves, 29 rule-outs. On a copy of the main stack's real database (0049, 7 Needs, 27 Understandings): after 0050, 8 Moves, 29 rule-outs on the real Needs, all 27 Understandings kept, Advice/Accountability wording updated, the 4 settings reloaded on start (Persona contains "get unstuck", Understanding prompt contains `lead_move`). Run again with the final frozen migration (downgrade to 0049, upgrade): same result.
- Be heard never gets Push, Suggest, Plan steps, Research or Reframe; disallowed/unknown dropped: `test_being_heard_is_never_given_a_move_it_rules_out`, `test_an_unknown_or_odd_move_is_dropped_and_the_other_kept`, `test_an_unknown_need_falls_back_with_only_the_moves_the_fallback_allows`, `test_the_fallback_understanding_has_no_moves`.
- "How to do it" reaches the reply instructions, after the Need's: `test_the_picked_moves_how_to_do_it_follows_the_needs_how_to_reply`, `test_move_names_are_read_in_any_case`.
- Stored and shown in the Model Call Log without content: `saved_moves` checks in the tests above; `tests/test_model_call_log.py::test_a_plain_users_understanding_shows_its_shape_and_never_its_words` expects `lead_move: Calm`, `support_move: Mirror` and no words; `web/src/lib/model-calls.test.ts` (Lead/Supporting Move facts, "None" when absent).
- Seed wording: see "What changed"; the Understanding is shown each Move's "when it fits" (`test_the_understanding_is_shown_the_moves_and_which_each_need_allows`).
- Checks after rebasing on main (0ebe38f): `ruff check`, `ruff format --check`, `mypy src` clean; `pytest` 1196 passed; web `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 67 files / 463 passed.
- `/run` (worktree stack 3010/8010/5442, inside the backend container: real repositories, DeepSeek chat model, Tavily web search, embedder and clock; only the chat channel, auth verifier, scheduler and timer are fakes, because Telegram can't reach a fake chat): the PRD's hosting chat ("going around in circles on app hosting" → "under SGD 15–20 a month, with managed Postgres, a few hundred users" → "pick one this week").
  - Run 1: Understandings `Think it through / Plan steps`, then `Advice / Research + Suggest`, then `Advice / Suggest + Plan steps`. On the 2nd Message the reply made 3 web searches (e.g. "app hosting with managed Postgres under 20 USD a month … comparison") and read render.com/pricing, then named Render (~$13/mo: $7 web + $6 Postgres), Railway (usage-based, $5 minimum) and Fly.io (managed Postgres from $38, over budget) with sources, and picked Render. The 3rd reply gave the steps and what "done" looks like.
  - Run 2, on the final code and the real data copy: `Advice / Research + Suggest` (2 searches, read render.com and railway.com pricing pages, Render ~USD 13/mo inside the budget), then `Advice / Suggest + Plan steps`, then `Accountability / Plan steps + Suggest`.
  - Model Call Log shapes for both runs show `lead_move`/`support_move` names only.

Code review (standards and spec): no hard violations. Fixed: migration no longer reads seed files or app code (starter rows frozen in it); `PickedMoves.lead_name`/`support_name` instead of a repeated expression; `ruled_out_move_ids` has no default; `NeedRepository.get` returns early; docstrings rewrapped. Kept, as decisions above: promoting a lone support; the extra web search reply wording (Research needs it); the migration's wording reload (platform not live).

Caveats:
- Migration 0050 replaces any Dashboard edits to Persona, the Understanding prompt, the web search tool description and reply instructions, and Advice/Accountability "how to reply" with the new seed wording (fine while the owner is the only User).
- A Plan steps reply in the run used a numbered list, which the Persona forbids: wording to tune with Evals (issue 07), not changed here.
- The Eval environment stores snapshot Needs without rule-outs and gets the starter rule-outs again by name when seeded; Moves in Evals are issue 07.
- Shared files touched: `tests/conftest.py`, `tests/fakes.py`, the seed files, `prestart.py`, `main.py`, and a new migration.

## Completion

- Completed: 2026-11-17
- Commit: `0ebe38f` — Moves issue 01: Moves shape replies — the Understanding picks a lead and at most one supporting Move from those the Need allows, and their "how to do it" goes into the reply
