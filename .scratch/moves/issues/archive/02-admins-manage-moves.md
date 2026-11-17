# 02 — Admins manage Moves, and Research needs Web Search

Status: completed
Lane: A

## Parent

`.scratch/moves/PRD.md`

## Parallel work

Two agents work this PRD at once, each in its own worktree. **Lane A: 02 → 03 → 06 → 07. Lane B: 04 → 05 → 08.** 09 goes to whichever lane is free first. Don't pick up the other lane's issues. Lane B is changing some of the same files (migrations, the seed settings file, the Understanding module, the admin Dashboard). Before pushing: `git fetch origin && git rebase origin/main`; if you added a migration, point it at the newest one so there is a single head; keep both lanes' changes when resolving conflicts.

## What to build

Admins manage Moves on the Dashboard, and a Move can need a Feature.

- Admin API: list, create, edit, delete and reorder Moves; duplicate names (ignoring case) refused as a conflict; an unknown Move id is not found (ADR-0011). Deleting a Move removes it from every Need's rule-outs; Understandings and Move Outcomes that named it keep the name.
- Need create and edit accept ruled-out Moves.
- A Move may need a Feature. Research needs Web Search (seed and migration). A Move whose Feature doesn't work for the User, or whose daily limit is used up (the Web Search Limit), is never offered to the Understanding. The reply then follows the existing Web Search wording: it says plainly it can't look things up (on their account, or until tomorrow), answers from what it knows, and never claims it searched.
- Dashboard (TanStack Query, ADR-0012; one API client): an admin Moves page modelled on the Needs page (no design in `docs/design/`, copy the Needs page's look) with add, edit, delete, reorder and the needed Feature; the Need edit form gains a ruled-out Moves picker.
- Changes reach the next reply.

## Acceptance criteria

- [x] Admins add, edit, delete and reorder Moves through the API and Dashboard; duplicate names are refused.
- [x] Deleting a Move clears it from Needs' rule-outs.
- [x] Need rule-outs are saved and change which Moves the Understanding is shown.
- [x] With Web Search off for a User, or its limit used up, Research is never offered, and the reply says so plainly without claiming it searched.
- [x] API tests (prior art: the Admin Needs tests), webhook tests for gating, Vitest + RTL tests for the pages; backend and web checks pass.
- [x] `/run`: Admin edits a Move on the Dashboard and the next reply uses it; with Web Search off for the owner, Research isn't picked.

## Blocked by

- `.scratch/moves/issues/01-moves-shape-replies.md`

## Comments

### 2026-11-17 — done (agent, branch `moves-02-admins-manage-moves`)

What changed:
- Moves are managed through the admin API: `MoveService` (`core/moves.py`) with list, add, edit, delete and reorder; `GET/POST /api/admin/moves`, `PUT/DELETE /api/admin/moves/{id}`, `POST /api/admin/moves/{id}/move`. A taken name, ignoring case, is a conflict (409, `MoveNameTakenError`); an unknown Move is not found (404, "No such Move"). `MoveRepository` gains get, add, update, delete, set_sort_orders.
- Deleting a Move clears it from every Need's rule-outs (the existing `ON DELETE CASCADE`); saved Understandings keep its name.
- Need add and edit take `ruled_out_move_ids` (required in the request; an unknown Move ID is 404). `NeedDetails` carries them and the repository saves them in the Need's transaction. The Need response lists them.
- A Move may need a Feature: `Move.needed_feature`, `moves.needed_feature` column. Migration `0052` (written as 0051, renumbered after issue 04's `0051_move_outcomes` merged first) adds it and sets Research (by name, ignoring case) to `web_search`; `seed/moves.yaml` says the same for fresh installs.
- The Understanding is shown only Moves whose needed Feature works for the User right now (`moves_that_work`, `UnderstandingService._working_features`). Web Search counts as not working once the Web Search Limit is used up (`web_search_limit_used_up`, now shared with `WebSearchTools`). A Research named anyway is dropped like any disallowed Move. The reply keeps the existing wording (`reply_features_unavailable_note` / `reply_web_search_limit_note`).
- Eval Need overrides (check and Make Live) keep the live Need's rule-outs (`NeedService.get` made public).
- Dashboard: `/admin/moves` page (`MovesManager`, `MoveCard`), modelled on the Needs page, with add, edit, delete, reorder and a "Needs a Feature" choice (names from the Features list); "Moves" in the admin sidebar; the Need card gains a "Ruled-out Moves" checkbox picker. API client: `listMoves`, `addMove`, `updateMove`, `deleteMove`, `moveMove`; query key `moves`. The web `Feature` type gains `curiosities` (the backend already had it).

Decisions made while building:
- A taken Move name is a 409, as the issue asks, though a taken Need name is still a 422 (unchanged).
- `ruled_out_move_ids` is required on Need requests, so an edit that leaves it out can't silently clear the rule-outs.
- The Moves and Needs pages wait for the Features / Moves list before drawing the cards, so a stored choice is never shown as "None".

Evidence per acceptance criterion:
- Add, edit, delete, reorder; duplicates refused: `tests/test_admin_moves.py` (`test_admin_can_add_edit_and_delete_moves`, `test_bad_moves_are_refused` (409 with the name, 422 for blank/too long/unknown Feature, 404 for unknown IDs), `test_admin_can_move_a_move_up_or_down`, `test_only_admins_can_manage_moves`); Dashboard `web/src/components/MovesManager.test.tsx` (9 tests: list, edit with Feature, add, refused name shown, remove, reorder, ends disabled, failed move, load failure).
- Deleting a Move clears rule-outs: `test_deleting_a_move_clears_it_from_every_needs_rule_outs`; `test_a_deleted_move_is_not_offered_and_saved_understandings_keep_its_name`.
- Need rule-outs saved and change the Moves shown: `test_a_needs_ruled_out_moves_are_shown_and_saved` (add, edit, unknown ID 404 leaves them as they were), `test_a_changed_rule_out_changes_the_moves_the_next_understanding_is_shown`; Make Live keeps them (`test_make_live_applies_the_overrides_once_and_the_run_shows_who_when_and_what`); `NeedsManager.test.tsx` (rule-outs shown, changed and saved, sent on add).
- Web Search off or limit used up: `tests/test_moves.py::test_with_web_search_off_research_is_never_offered_and_the_reply_says_so`, `::test_with_the_web_search_limit_used_up_research_is_never_offered`, `::test_a_move_needing_a_feature_that_works_is_offered`; migration `tests/test_moves_migration.py::test_the_migration_says_research_needs_web_search`; `test_admin_sees_the_moves_in_order_with_the_feature_each_needs`.
- Checks on the final code: `pytest` 1210 passed; `ruff check .`, `ruff format --check .`, `mypy src` clean; web `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 68 files / 474 passed.
- After rebasing on main (with issue 04): conflicts were imports only (kept both); `pytest` 1227 passed; `ruff`, `ruff format`, `mypy` clean; web lint, format, typecheck clean, `pnpm test` 68 files / 478 passed, `pnpm build` compiles `/admin/moves`. The stack migrated 0050 → 0051 (Move Outcomes) → 0052 (Research needs Web Search) to a single head; the Moves and Needs pages load with no page errors.
- `/run` (worktree stack 3020/8020/5452, migrated before the rebase; Research `needed_feature = web_search`):
  - Dashboard as a signed-in Admin (Playwright): the Moves page lists the 8 Moves with Research needing "Web Search"; edited Suggest's "how to do it" (marker `RUNCHECK-0217`) and saved ("Saved Suggest."); on the Needs page ticked Push as ruled out for Advice and saved ("Saved Advice."); DB showed both saves; the page works at 390px; no page errors.
  - Next reply, inside the backend container on the real repositories, DeepSeek, Tavily, embedder and clock (only the chat channel, scheduler and timer swapped, since Telegram can't reach a fake chat): the hosting chat ("SGD 20 a month with managed Postgres… help me pick?") → Understanding `Advice / Research + Suggest`; Advice's allowed Moves no longer listed Push; the reply instructions held the edited Suggest text; the reply made 4 web searches and named real options with sources (Neon free + Fly.io, Railway, Koyeb) and ended on two to weigh.
  - Turned Web Search Off for that User on the Dashboard (Users → Features → Web Search: Off). Next Message ("cheap VPS in Singapore… can you look up some options?") → Understanding `Advice / Suggest`; Research not offered (missing from every Need's allowed Moves); no web tools; the unavailable note was in the instructions; the reply said "I can't look anything up right now — web search isn't available on your account" and suggested from what it knows, without claiming it searched.
  - Run data put back (Suggest text from the seed, Advice rule-outs cleared) and the test user deleted (`cleanup.sh`).

Code review (standards and spec): no hard violations, no spec gaps. Fixed: `reloadMovesAndNeeds` (it reloads Needs too); the Move service named in `app.py` like the Need service; the override helper's docstring says why the value is read before the live Need (a malformed value stays a 422). Kept: 409 for a taken Move name (the issue asks for a conflict); copying the Needs code shape; `moveMove` naming (follows `moveNeed`); add/save/remove outside `useMutation` (copied from the Needs page).

Caveats:
- Two saves of the same Move name at the same moment could hit the unique index and give a 500 instead of a 409 (Needs has the same gap); fine with one Admin.
- The Web Search usage count is now read twice per reply (Understanding and web tools).
- Shared files touched: a new migration (`0052`, revises issue 04's `0051`), `seed/moves.yaml`, `core/models.py`, `core/ports.py`, `adapters/postgres/*`, `admin_api.py`, `app.py`, `api-client.ts`, `queries.ts`, `SidebarNav.tsx`.

## Completion

- Completed: 2026-11-17
