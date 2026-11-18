# 03 — Get curious Move and the venting line

Status: completed

## Parent

`.scratch/get-curious/PRD.md`

## What to build

A new Move, **Get curious**, lets Zeph get to know the User: one natural question about something they just said, to learn something new about them, go a little deeper, or check something it isn't sure of.

- **Seed Move.** Its "when it fits" covers the User mentioning something about their life (plans, people, sleep, routines, work) that Zeph knows little about, half-knows, or isn't sure it has right. Its "how to do it" says:
  - ask one short, light question about something they just said, the way a curious friend would;
  - prefer what Zeph doesn't know yet, or a guess it holds;
  - checking something it thinks it knows is fine when it isn't sure;
  - it can be practical and kind ("you a coffee person?"), never a quiz;
  - let it go after a short answer.

  It needs no Feature, and "asks a question" (issue 01) is ticked.
- **Needs.** Ask more and Get it done rule it out; the other Needs allow it.
- **The venting line.**
  - Be heard's "when it fits" becomes roughly: "They're letting out something painful or frustrating, staying on it or coming back to it, often with strong words, and want it to land with someone, not to be fixed… A hard thing mentioned in passing (tired, busy day, a small annoyance) is not this: that's an update." Keep its existing Goal-slip sentence.
  - Just chatting's "when it fits" adds "including passing mentions of everyday hard things, like poor sleep or a long day."
- **Running platform.** The migration:
  - adds Get curious only if no Move with that name exists, ignoring case, placed last, with the box ticked;
  - adds the rule-outs to Ask more and Get it done if they still exist;
  - updates the Be heard and Just chatting wording only where it still matches the old seed word for word.

  The seed files get the same changes.
- **Evals.** Two new Understanding Eval cases in the seed. **Don't run them**; Evals cost money and the owner decides when.
  - The passing update: after a morning Check-in, "It's going to be a long day" then "5 hours sleep only". Expect Just chatting, with Get curious as lead or supporting.
  - A real vent: "ugh I'm so done, my boss tore my work apart again in front of everyone". Expect Be heard, and no question about why they feel it.

## Parallel work: avoid clashes

Issue 04 runs at the same time in another worktree.
- **Migration number:** use the next free number. If 04 merges first with the same number, renumber yours during the rebase and point it at theirs.
- **Files:** you own the Needs and Moves seeds. 04 owns the Curiosity-keeping and Portrait prompts in the platform settings seed.
- **Understanding Eval cases seed:** both add cases at the end. When rebasing, keep both.

## Acceptance criteria

- [x] Get curious is in the Moves seed with "asks a question" ticked; a new install has it, ruled out by Ask more and Get it done and allowed by the rest
- [x] Be heard and Just chatting seed wording draw the venting line as above
- [x] The migration adds Get curious with its rule-outs to an existing database, and leaves one that already has a "Get curious" Move as it is
- [x] The migration updates unchanged Be heard and Just chatting wording and leaves edited wording alone (migration test, as in the Moves migration test)
- [x] Get curious is offered to the Understanding under Just chatting and not under Ask more (webhook test)
- [x] The two Understanding Eval cases are in the seed and load (seed loading test); they are not run
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] `/run`: after the migration, the Dashboard Moves page shows Get curious with the box ticked and the Needs pages show the new rule-outs and wording. In the running app, sending "It's going to be a long day" / "5 hours sleep only" gets an Understanding of Just chatting with Get curious, and a reply with one natural question (one real Message, not an Eval Run)

## Blocked by

- `.scratch/get-curious/issues/01-asks-a-question-checkbox-on-moves.md`

## Comments

- 2026-11-18 (agent, branch `get-curious-03-move-venting`): started. Seeds first (TDD at the agreed seams: Moves seed/webhook, migration, Eval seed loading), then migration, then Eval cases.
- 2026-11-18 evidence, per criterion:
  - Get curious in the seed, ticked, rule-outs: `moves.yaml` adds Get curious last with `asks_a_question: true` and no Feature; `needs.yaml` adds it to Ask more and Get it done. Tests: `test_a_fresh_install_has_get_curious_asking_a_question`, `test_a_fresh_install_has_the_starter_moves_and_rule_outs_in_order`, `test_the_understanding_is_shown_the_moves_and_which_each_need_allows` (Be heard, Think it through, Advice, Accountability and Just chatting allow it; Get it done and Ask more show "none").
  - Venting line: Be heard's "when it fits" now says "letting out something painful or frustrating, staying on it or coming back to it, often with strong words … A hard thing mentioned in passing (tired, busy day, a small annoyance) is not this: that's an update", keeping the Goal-slip sentence; Just chatting adds "including passing mentions of everyday hard things, like poor sleep or a long day".
  - Migration `0061_get_curious_move.py` (first written as 0060; renumbered during the rebase after issue 04 merged its 0060; `down_revision = "0060"`). It adds Get curious only when Moves exist and none is called Get curious, ignoring case (a fresh install gets it from the seed instead, or the seed wouldn't load), last with the box ticked, ruled out by Ask more and Get it done if they exist; it updates Be heard and Just chatting only where the old seed wording matches word for word. Tests: `test_the_get_curious_migration_adds_it_last_ticked_with_its_rule_outs`, `test_the_get_curious_migration_leaves_an_existing_one_and_edited_wording_alone`, `test_the_get_curious_migration_adds_no_move_to_a_database_without_moves`.
  - Offered under Just chatting, not Ask more (webhook): `test_get_curious_is_offered_under_just_chatting_and_not_under_ask_more` (its how-to-do-it is in the Just chatting reply and saved as lead; under Ask more it's dropped and nothing is saved).
  - Eval cases (not run, no Eval Run started): `passing-update-gets-curious` (morning Check-in line and "It's going to be a long day" as earlier lines, then "5 hours sleep only" → Just chatting, lead Get curious, rule `one_light_question`) and `real-vent-is-heard` ("ugh I'm so done, my boss tore my work apart again in front of everyone" → Be heard, `asked_why: false`, rule `no_why_question`). The earlier lines are there because Get curious can't be made two replies in a row; the case checks the lead Move only, since Just chatting allows only Suggest and Research besides it (noted in the case). Test: `test_the_understanding_cases_draw_the_line_between_an_update_and_a_vent`; `test_every_seed_case_fits_its_eval_s_case_shape` passes.
  - Checks (after rebasing on issue 04): `uv run pytest` 1319 passed; `uv run ruff check .` all passed; `uv run ruff format --check .` 455 files formatted; `uv run mypy src` no issues in 185 files; `web/`: `pnpm lint` clean, `pnpm format:check` clean, `pnpm typecheck` clean, `pnpm test` 486 passed in 68 files. An earlier full run failed three tests that listed the old Moves (`test_admin_moves`, two in `test_eval_runner`); fixed. One run hit a Docker timeout making the test container while the stack was building; it was rerun.
- 2026-11-18 review: Standards found no hard breaches. Fixed: migration renumbered to 0061 after issue 04's 0060, the seed lookup helpers (`when_it_fits`, `need_when_it_fits`) moved next to their twins, the old-wording constants moved to the top of the migration test, a clearer name (`asks_a_question_by_name`). Kept: the old wording written out in both the migration and its test (a migration stays frozen; same as `OLD_ACCOUNTABILITY_HOW_TO_REPLY`). Spec found nothing missing or wrong; added the note in the passing-update case on why it checks only the lead Move.
- 2026-11-18 `/run` (worktree stack, rebuilt after the rebase):
  - Migration on an existing platform: the worktree database was put back to a 0059 platform (Get curious removed, old Be heard and Just chatting wording, `alembic_version` 0059), then the real `migrate` ran 0060 (issue 04) and 0061. Result: Get curious at sort order 8, `asks_a_question = t`, ruled out by Ask more and Get it done; both Needs have the new wording. Then, with Get curious renamed "get Curious" and Be heard set to "Admin edited wording" and the version at 0060, migrating again left both as they were (restored afterwards).
  - Dashboard (run-dashboard, Admin): `/admin/moves` lists Calm … Research, Get curious, and only Get curious has "Asks a question" ticked. `/admin/needs` shows the new Be heard and Just chatting wording; Get curious is ticked under ruled-out Moves for Get it done and Ask more, and not ticked for Be heard, Think it through or Just chatting. No page errors.
  - Real Message (not an Eval Run): real `create_app` in the backend container on the worktree database with the real models (DeepSeek); only Telegram (recording channel; the chat ID is made up), the timer and the scheduler were swapped. A real morning Check-in was sent first (Check in Now, local time 08:31): "Morning — how's your week going so far?". Then "It's going to be a long day" → Understanding Just chatting, lead Get curious; reply "Mm, one of those. What's on it today?" (one natural question). Then "5 hours sleep only" → Just chatting (not Be heard), no Move: Get curious wasn't offered, as it was made the reply before (issue 01's rule), so the reply asked nothing ("Ugh, that's a rough place to start from. Everything feels twice as heavy on five hours." / "Hope there's at least some coffee within reach."). The same run before the rebase gave the same Understandings ("Long one, yeah. What's filling it up?").


## Completion

- Completed: 2026-11-18
- Commits:
  - `70c2e75` Get-curious issue 03: Get curious Move and the venting line
  - `2a8647c` Get-curious issue 03: CONTEXT.md Need draws the line between being heard and a passing update
