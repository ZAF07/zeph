# 40 — The directness setting also sets how Zeph asks

Status: completed
Track: A
Blocked by: 43 (it renames "way" to Approach and changes the same code)

## Parent

`.scratch/pattern-pipeline/PRD.md`. Design: `docs/pattern-pipeline/README.md`. Decided by the owner (Zaf) on 25 Nov 2026 in the grill for issue 23 (its decision D15). It changes decision 7 in `.scratch/pattern-pipeline/grill-decisions.md`, which said the setting is only about the Read.

## Does it need a grilling session?

Not a full one. The shape is decided (below). Four small questions are left, each with a suggested answer. Confirm them with the owner before planning, then set this to `ready-for-agent`.

## The problem

A User sets how direct Zeph is: gentle, balanced or direct. Today that only changes how soon and how plainly Zeph says its Read. The Agenda never reads it, so a "direct" User and a "gentle" User get the same questions in the same order. A User who picks "direct" expects it to cover how Zeph asks too, and a "gentle" User deserves more room.

## What was decided

Directness changes where an Exploration starts and how long it waits. Nothing else.

| | Gentle | Balanced (today) | Direct |
|---|---|---|---|
| First Approach | story follow-up | story follow-up | "would it have gone differently if…" |
| "Would it differ" Approach | skipped: follow-up, then "notice" | used second | used first |
| Wait after a try with nothing | longer | 3 days (`exploration_wait_days`) | shorter |

Fixed for everyone, whatever the setting:

- Backing off after brush-offs; "drop it" is final.
- Nothing while they are struggling.
- Zeph never names a state first (issue 23, D12).
- Never two Conversations in a row on the same Exploration.
- The ready gate: directness never changes whether a Pattern may be shared.

Also decided:

- It applies to every Exploration need (unclear story, counter-test, missing Condition), not only Conditions.
- The Dashboard's words for the setting must also say it affects how Zeph asks, so Users know what they are choosing. The chat settings tool's description too.
- The waits are Admin-set numbers with hints, overridable in Eval Variants.

## Why

- Owner: the setting should also affect how pushy Zeph is.
- "Direct" must not become a licence to interrogate, so only the start and the wait move; every backing-off rule stays fixed.
- Turned down: keeping the same order for everyone and letting only the wording follow directness. It leaves a gentle User with the same questions as a direct one.

## Open questions, answered by the owner (Zaf) on 26 Nov 2026

1. The waits for gentle and direct: **5 days and 2 days** (balanced stays 3).
2. The Thought Experiment Approach: **unchanged**. It comes after "would it differ"; for gentle, after the story follow-up.
3. Does directness also change the fewest replies between two Curiosities, and the tries before an Exploration rests? **Yes, both change.** (The suggested answer was no.) The backing-off rules themselves stay fixed: the spacing still doubles after brush-offs, and "drop it" still rests an Exploration at once.
4. A User changes the setting while a question waits: **the waiting one stays**; the new setting applies from the next try.

## What to build

- **Order of Approaches, by setting:**
  - gentle: story follow-up → Thought Experiment → "this week, notice…" ("would it differ" is never used);
  - balanced: story follow-up → "would it differ" → Thought Experiment → "notice" (today);
  - direct: "would it differ" → story follow-up → Thought Experiment → "notice".
  The rules per need stay: a missing Condition never gets a Thought Experiment, and the state going in gets only story follow-up and "notice", for every setting (Zeph never names a state first).
- **Three numbers, each per setting.** Balanced keeps today's key and value. Starting numbers for the last two were picked by the agent, for the owner to correct:

  | | Gentle | Balanced | Direct |
  |---|---|---|---|
  | Wait after a try with nothing (days) | 5 | 3 | 2 |
  | Tries with nothing before resting | 3 | 4 | 5 |
  | Fewest replies between Curiosities | 4 | 3 | 2 |

  Six new Platform Settings with hints, overridable in Eval Variants. The fewest replies between Curiosities covers every Curiosity, not only aimed ones.
- **A setting changed mid-way:** a waiting aimed Curiosity is left as written; the next one is written under the new setting.
- **Words:** the Account page's help text, the chat tool `change_directness` (description and what the model is told back) and `reply_settings_instructions` say the setting also changes how Zeph asks. A migration reloads the Copy slot and the prompt unless an Admin edited them. The reference files `Account.html` and `M-Account.html` get the new help text.
- **Not changed:** the Reply Plan's own line on directness (still about the Read), the ready gate, sharing, struggling, never two Conversations in a row.

## Acceptance criteria

- [x] A gentle User's Exploration starts with a story follow-up and never uses "would it differ"; a balanced User's is as before; a direct User's starts with "would it differ"
- [x] The Thought Experiment Approach keeps its place: after "would it differ", and for gentle after the story follow-up
- [x] This holds for all three needs (unclear story, counter-test, missing Condition), and the state going in is never asked by "would it differ", whatever the setting
- [x] The wait after a try with nothing is 5, 3 and 2 days for gentle, balanced and direct
- [x] An Exploration rests after 3, 4 and 5 tries with nothing in a row for gentle, balanced and direct; "drop it" still rests it at once for everyone
- [x] The fewest replies between two Curiosities is 4, 3 and 2 for gentle, balanced and direct, and still doubles while Zeph backs off
- [x] A waiting aimed Curiosity stays as written when the User changes the setting; the next try follows the new setting
- [x] The six new numbers are on Platform settings with hints and can be overridden in an Eval Variant
- [x] The Account page's help text, the chat tool's description and the settings instructions say the setting also changes how Zeph asks; an Admin's edited text is kept by the migration
- [x] Unchanged for every setting: never two Conversations in a row, nothing while struggling, the ready gate
- [x] `docs/pattern-pipeline/README.md`, `lifecycle.md`, `docs/message-pipeline/README.md`, `CONTEXT.md` and decision 7 in `grill-decisions.md` say what is built
- [x] `pytest`, `ruff`, `ruff format`, `mypy` and the web checks pass, and it was checked in the running app (`/run`): a gentle, a balanced and a direct User with the same suspected Pattern get a different first Approach and a different wait, and the Account page shows the new words

## Comments

### 26 Nov 2026 — built, checked and closed

**What was built.** `core/agenda.py`: the order of Approaches per setting (`APPROACH_ORDER_BY_DIRECTNESS`, `approaches_for(need, directness)`, `approach_after`, `next_approach`), and `agenda_numbers(settings, directness)` picks the wait and the tries before resting. `core/curiosities.py`: the fewest replies between Curiosities per setting. Six new Platform Settings with hints, on the Dashboard's Platform settings page. The Account help text, the `change_directness` tool and `reply_settings_instructions` say the setting covers asking. Migration 0112. `Account.html`, `M-Account.html` and their baselines. Docs and ADR 0033.

**Migration (for the PR).** 0112 changes no table. It reloads `reply_settings_instructions` through `reload_prompt_unless_edited`, and removes the Copy slot `account.directness.help` only where it still holds the old seed text, so the new text loads. An Admin's edit of either is kept. The six numbers load from the seed.

**Decisions made while building.**
- Direct's order is "would it differ" → story follow-up → Thought Experiment → "notice". The decision said only that "would it differ" is first and the Thought Experiment keeps its place.
- Starting numbers the owner didn't give: rest after 3 / 4 / 5 tries, 4 / 3 / 2 replies between Curiosities.
- The fewest replies between Curiosities is one rule for every Curiosity, so directness moves all of them.
- After a change of setting the next try steps on from the last Approach in the new order. A try by an Approach the new setting never uses is not repeated, also when it was useful.
- No new Eval cases: a made-up Eval User is always balanced. No Eval was run, so nothing was spent on Evals.
- The balanced rows on Platform settings now end in ": balanced", so the three read as a set.

**Review.** Two reviews (standards, spec). Fixed: one naming for the per-setting maps, the Agenda's directness is a required field, the tool's words no longer promise different wording of questions, tests for the wait, resting and never two in a row at every setting, hints cut to two sentences. Left as judgement calls: directness is handed to the Agenda twice (as its own field and through the numbers); `approach_after` has a second branch for an Approach the setting never uses.

**Checks.** After the rebase on main (with issue 44): ruff clean, ruff format clean, mypy clean, pytest 2731 passed; web: eslint, prettier and tsc clean, Vitest 991 passed (141 files).

**How it was checked in the running app.** On this worktree's stack (fresh database, migrated to 0112, seeds loaded), as a signed-in test Admin with Pattern noticing and exploring on, real models, and the chat channel swapped for the one that logs instead of sending. Texts were posted to the Telegram webhook; each Conversation's times were moved back past the quiet gap and the running backend ended it itself. "Situations to be ready" was 9 so the Pattern stayed suspected. Set by SQL and not by chat: the two clear stories for CONF.AVOID.BELONG (and later an unclear one, and their audience and state), each try marked asked and brushed off (or useful), and the Exploration cleared between settings. The setting was changed on the Account page in the browser for the first rounds, by SQL for the last two.

**Evidence per criterion**

- **First Approach per setting.** `test_directness_sets_the_first_approach_of_an_exploration`, `test_a_gentle_user_is_never_asked_would_it_differ`. Running app, same Pattern, counter-test need: balanced wrote a story follow-up, then "would it differ"; direct wrote "would it differ" first, then a story follow-up; gentle wrote a story follow-up, then "notice", and never "would it differ".
- **The Thought Experiment keeps its place.** `test_directness_sets_the_order_of_approaches_for_every_need`, `test_a_gentle_users_unclear_story_gets_a_thought_experiment_second`. Running app: a gentle User with an unclear story got a story follow-up, then a Thought Experiment ("Put this made-up situation to them, keeping its words: …").
- **Every need; state never by "would it differ".** The same tests, and `test_a_state_gap_is_asked_openly_never_by_would_it_differ_and_names_no_state` for all three settings. Running app, direct User: a missing Condition (audience) was asked by "would it differ" first; a one-sided state going in was asked by a story follow-up reading "…how they were doing going into it. Ask openly, and name no mood or state yourself".
- **Waits of 5, 3 and 2 days.** `test_directness_sets_the_wait_and_the_tries_before_resting`, `test_the_next_try_waits_as_long_as_their_directness_says`. Running app, a try brushed off on 26 Nov: the next was not before 1 Dec (gentle), 29 Nov (balanced), 28 Nov (direct).
- **Rests after 3, 4 and 5; "drop it" at once.** `test_it_rests_after_as_many_tries_with_nothing_as_their_directness_says`, `test_asked_to_drop_rests_it_at_once_whatever_the_directness`. Running app: the gentle User's Exploration rested after its third try with nothing. Balanced, direct and "drop it" were not run in the app (same code path, the number differs).
- **Replies between Curiosities 4, 3 and 2; still doubles.** `test_directness_sets_the_fewest_replies_between_curiosities`, `test_a_direct_users_spacing_still_doubles_after_brush_offs`. Running app, right after a Curiosity was asked, the Reply Plan's input (Model Call Log) was offered the waiting one on reply 3 for direct, reply 4 for balanced and reply 5 for gentle, and not before. Doubling was not run in the app.
- **A waiting one stays.** `test_a_waiting_aimed_curiosity_stays_when_the_user_changes_directness`, `test_after_they_turn_direct_the_next_try_steps_on_in_the_direct_order`. Running app: with a gentle "notice" try waiting for 1 Dec, the setting was changed to balanced on the Account page; after the next Conversation end the same try was still waiting, unchanged.
- **Six numbers on Platform settings, with hints and an Eval override.** `test_every_agenda_number_is_a_setting_with_a_hint_and_an_eval_override` (now eleven keys), `test_every_editable_setting_comes_with_a_short_hint`, `PlatformSettingsForm.test.tsx`. Running app: the nine rows showed 5 / 3 / 2, 3 / 4 / 5 and 4 / 3 / 2 with their hints; "Wait after a try with nothing: gentle" was changed to 6 in the browser, saved and stored (then put back to 5). The Eval override was checked by test only.
- **The words; an Admin's edit is kept.** `test_the_account_page_says_directness_also_changes_how_zeph_asks`, `test_the_chat_tool_says_directness_also_changes_how_zeph_asks`, `test_an_existing_install_gets_the_words_on_how_zeph_asks`, `test_an_admins_own_words_on_directness_are_kept_by_the_migration`. Running app: the Account page showed the new help text; "you ask me a lot of questions. can you ease up and ask less?" made the reply call `change_directness` and the User became gentle ("I've dialled that back, so I'll ask less from now on"). The stack was put back to 0111 with the old help text and an edited prompt; on restart 0112 loaded the new help text, kept the prompt, and the log said "Kept the stored reply_settings_instructions". The pixel test passed for Account (0.17%) and M-Account (0.38%), run from a copy of `compare.cjs` that blocks Clerk's probe requests, which never finish on this machine.
- **Unchanged for every setting.** `test_no_directness_is_asked_two_conversations_in_a_row`, the existing struggling and ready gate tests (neither reads directness; `ready_gate.py` and `pattern_sharing.py` are untouched). Not run again in the app.
- **Docs.** `docs/pattern-pipeline/README.md`, `lifecycle.md`, `docs/message-pipeline/README.md`, `docs/thought-experiments/README.md`, `CONTEXT.md` (Persona, settings change, Approach), decision 7 in `grill-decisions.md`, ADR 0033.
- **Checks pass; the /run check.** Above.

**Not done.** No Eval case covers gentle or direct. The migration was not run on a copy of the main database. Findings for the owner are in issue 20, section 40.

## Completion

- Completed: 2026-11-26
- Commit: <merge commit, recorded after the merge>
