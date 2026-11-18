# 01 — "Asks a question" checkbox on Moves

Status: completed

## Parent

`.scratch/get-curious/PRD.md`

## What to build

Admins can tick **Asks a question** on any Move. A Move with it ticked follows two rules in every reply:

- **Never twice in a row.** If the previous Understanding in the Conversation made it, as lead or supporting, it isn't offered to the Understanding this time. It's offered again the reply after.
- **One question per reply.** If the Understanding makes it while the reply also asks why (the existing ask-why rule) or raises a Curiosity, the other question wins. The Move is dropped from that reply: it isn't put in the reply's instructions and isn't recorded as made, so no Move Outcome is kept for it. If it was the lead Move, the supporting Move doesn't move up; the reply just responds.

When the reply already asks a question (through such a Move, asking why or a Curiosity), the Woven-in Check-in model is told so, and prefers to leave the Check-in out or weave it in without another question.

The checkbox is shown and saved on the Dashboard Moves page and through the admin Moves API, and is off by default. Eval Runs keep it in their Moves snapshot. A Variant's Setting Overrides can't change it, as with a Move's needed Feature. Code never looks up a Move by name: this works for any Move with the box ticked. Get curious itself is added in issue 03.

## Parallel work: avoid clashes

Issue 02 runs at the same time in another worktree.
- **Migration number:** use the next free number. If 02 merges first with the same number, renumber yours during the rebase and point it at theirs.
- **Understanding code:** you own the Move-offering filter (next to the needed-Feature filter), the reply-guidance or Move instructions, and how a made Move is recorded. Don't touch how due Curiosities are written out for the Understanding or the reply; 02 owns that.
- **Platform settings seed:** you only touch the Woven-in Check-in wording. 02 edits the Curiosity-keeping prompt.
- **Models and tables:** you change Move only; 02 changes Curiosity.

## Acceptance criteria

- [x] A Move has an "asks a question" setting, default off, saved by a migration (the existing Moves get false) and in the Moves seed format
- [x] The admin Moves API saves and returns it; a test covers create and update
- [x] The Dashboard Moves page shows a checkbox for it on each Move and saves it; a Vitest test covers it
- [x] A Move with it ticked that the previous Understanding made, as lead or supporting, isn't offered to the Understanding; it's offered again the reply after (webhook test with the scripted chat model)
- [x] A Move with it ticked that is made together with asking why is dropped from the reply instructions and isn't recorded as made; the same applies when a Curiosity is raised
- [x] A dropped lead Move doesn't let the supporting Move take its place
- [x] The Woven-in Check-in model is told when the reply already asks a question
- [x] The Eval Run Moves snapshot keeps the setting; Setting Overrides can't change it
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`; in `web/`: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] `/run`: on the Dashboard, tick the box on a Move and see it saved. In the running app, a Message whose scripted or real Understanding made that Move doesn't get it offered on the next Message (seen in the Model Call Log or the understandings table)

## Blocked by

None - can start immediately.

## Comments

- 2026-11-18 (agent, branch `get-curious-01-asks-a-question`): started. Plan: `asks_a_question` on Move (model, table, migration 0059 (renumbered after issue 02 took 0058) which also reloads the Woven-in Check-in prompt, repo, seed loader, admin API, eval snapshot; Setting Overrides keep the live value). Understanding: filter out a ticked Move the previous Understanding made, next to the needed-Feature filter; after picking, drop ticked lead/support when the reply asks why or raises a Curiosity (support never moves up). Woven-in Check-in told when the reply already asks a question. Dashboard: checkbox on each Move card.
- 2026-11-18 evidence, per criterion:
  - Setting, default off, migration and seed format: `moves.asks_a_question` (not null, default false); migration `0059_moves_ask_a_question.py` (renumbered after issue 02 took 0058; `down_revision = "0058"`); the Moves seed reads an optional `asks_a_question` (false when left out). Tests: `test_the_asks_a_question_migration_leaves_existing_moves_unticked`, `test_seeding_reads_whether_a_move_asks_a_question`.
  - Admin Moves API: `MoveResponse` / `MoveDetailsRequest` carry it (request defaults to false). Test: `test_admin_can_add_edit_and_delete_moves` (create ticked, update unticked) and `test_admin_sees_the_moves_in_order_with_the_feature_each_needs` (all off).
  - Dashboard checkbox: "Asks a question" on each `MoveCard`. Vitest: "shows whether each Move asks a question", "saves a Move with Asks a question ticked".
  - Not offered after the previous Understanding made it: `moves_without_repeat_questions` next to `moves_that_work` in `understanding.py`. Tests: `test_a_move_that_asks_made_last_reply_is_offered_again_only_the_reply_after`, `test_a_move_that_asks_made_as_support_is_not_offered_next_reply`.
  - Dropped with asking why or a Curiosity: `drop_moves_that_ask` runs before the Understanding is saved, so Move Outcomes (read from the saved lead/support) never see it. Tests: `test_a_move_that_asks_is_dropped_when_the_reply_asks_why`, `..._when_the_reply_raises_a_curiosity`, and `test_a_move_that_doesnt_ask_is_kept_when_the_reply_asks_why`.
  - No move-up: `test_a_dropped_lead_move_that_asks_does_not_let_the_support_move_up` (saved as `(None, "Plan steps")`; the supporting Move stays as support).
  - Woven-in Check-in told: "Your reply already asks them a question." added to its Understanding lines; seed prompt says to prefer "not now" or a Check-in with no question of its own; 0059 reloads the stored prompt. Tests: `test_the_woven_in_check_in_is_told_when_a_move_in_the_reply_asks`, `..._when_the_reply_asks_why`, `..._is_not_told_so_when_the_reply_asks_nothing`, `test_the_woven_in_check_in_prompt_says_to_ask_no_second_question`.
  - Eval snapshot and overrides: snapshot JSON keeps `asks_a_question` (older snapshots read as false); `_move_details` keeps the live value, and override values keep only the text. Tests: `test_a_run_keeps_each_moves_asks_a_question_in_its_snapshot`, `test_make_live_of_a_move_override_never_changes_its_asks_a_question`.
  - Checks (after rebasing on issue 02): `uv run pytest` 1307 passed; `uv run ruff check .` all passed; `uv run ruff format --check .` 452 files formatted; `uv run mypy src` no issues in 183 files; `web/`: `pnpm lint` clean, `pnpm format:check` clean, `pnpm typecheck` clean, `pnpm test` 486 passed in 68 files. One earlier run had `test_case_history_marks_where_the_case_or_settings_changed` fail once while the stack was restarting; it passed alone and in both full runs.
- 2026-11-18 review: Standards found no hard breaches. Fixed: one shared `tick_asks_a_question` test helper, the "reply asks another question" check named once (`asks_another_question`), a clearer filter name (`moves_without_repeat_questions`), a TSDoc wrap. Kept: the migration's `get_bind().execute` form (same as 0055), the one bool passed to the Woven-in Check-in, and the dataclass defaults (off by default). Spec found nothing missing or wrong. It noted that 0059 wipes an Admin-edited Woven-in prompt, as earlier prompt migrations do; the PRD says reloading prompts is fine while the platform isn't live.
- 2026-11-18 `/run` (worktree stack rebuilt from an empty database after the rebase; it migrated through issue 02's 0058 to 0059 and both features' columns exist):
  - Dashboard (run-dashboard, Admin): on `/admin/moves`, ticked "Asks a question" on Suggest and saved ("Saved Suggest."). After a reload Suggest stays ticked and Calm doesn't; the `moves` table shows only Suggest ticked. At 390px the label first split into two columns; it now wraps as one line of text (fixed and checked again).
  - Chat path: real `create_app` inside the backend container on the worktree database, with the real reply model (DeepSeek). Only Telegram (recording channel), the timer and the scheduler were swapped, and the Understanding answers were scripted (the chat ID is made up; see the worktree Telegram limits). Suggest was ticked on the Dashboard first.
    - Repeat rule: message 1's Understanding made Suggest. Understanding 2 was offered `Calm, Ground, Reframe, Mirror, Plan steps, Push, Research` (no Suggest). Understanding 3 was offered Suggest again. The `understandings` rows are `(1, Suggest, -)`, `(2, -, -)`, `(3, -, -)`.
    - Drop rules: "my landlord STILL won't fix the heating" (Advice, lead Suggest, support Plan steps, high mood with no known cause). The reply instructions had the ask-why note and "Support it with: Plan steps", with no "Lead with:" and no Suggest how-to; the row is `(4, asked_why = t, -, Plan steps)`. Next, "and it's freezing in here" (lead Suggest plus a due Curiosity raised; no ask-why, since it was asked last time). The instructions had the Curiosity and no Suggest how-to; the row is `(5, -, -)` and the Curiosity is `raised`.
    - Woven-in Check-in (a due Check-in set with SQL): both decision calls were told "Your reply already asks them a question."; the stored `woven_check_in_prompt` holds the new wording.
  - Eval snapshot and overrides: the real run service and runner were run in the backend container with a stub chat model, so no paid calls were made (S$0.00) and the eval-runner container was stopped first. An Understanding run started with Variant B overriding Suggest's text and sending `asks_a_question: false`. The finished run's `moves_snapshot` has Suggest `true`, the rest `false`; Variant B's stored override has only the name and text. Pressing "Make Variant B live" on the Dashboard run page applied the text ("Changed by Variant B.") and Suggest is still `asks_a_question = t`.


## Completion

- Completed: 2026-11-18
- Commits:
  - `d553b87` Get-curious issue 01: "Asks a question" checkbox on Moves
  - `8ff7363` Get-curious issue 01: review fixes — one test helper, name the other-question check once, clearer filter name
  - `f79905b` Get-curious issue 01: Asks a question label wraps as one line of text at phone width
  - `e1ffaf5` Get-curious issue 01: renumber the asks-a-question migration to 0059, after issue 02's 0058
  - `aea45e3` Get-curious issue 01 done: archive issue with check, review and run evidence; CONTEXT.md Move lists Asks a question
  - `55c9dbf` Merge get-curious issue 01 into main
