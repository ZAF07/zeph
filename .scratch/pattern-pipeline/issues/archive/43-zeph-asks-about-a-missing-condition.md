# 43 — Zeph asks about a missing Condition, and "way" becomes Approach

Status: completed
Track: A
Blocked by: 41

## Parent

Issue 23, decisions D5, D6, D12, D13 and D15 (last paragraph). ADR-0031. Terms: **Condition**, **Approach**, **Exploration** in `CONTEXT.md`. Today's rules: `core/agenda.py` (`open_needs`, `next_way`, `aimed_question`) and "Explorations and the Agenda" in `docs/pattern-pipeline/README.md`.

## What to build

Code keeps count, for each suspected Pattern, of which Condition values it has seen and which it hasn't, and aims one question at an unseen value when the stories so far are one-sided. Zeph asks no more often than today.

- **Coverage table** (pure, worked out from the Pattern's Observations, never stored): for each Condition (relationship, power, stance, setting, audience, stakes, state) and each value, the number of clear stories for and clear stories against. Clear means not unclear, not situational, not excluded.
- **A "missing Condition" need** replaces "missing part of life". A Condition's value is an open need only when all hold:
  1. at least `condition_one_sided_stories` (2) clear stories for the Pattern have that Condition known and all share one value;
  2. another value of it has no clear story, for or against (that value is what to learn);
  3. only the most one-sided Condition is a need (the most stories behind it; ties go by a fixed order of Conditions);
  4. a useful try closes that value for good; tries with nothing rest the Exploration as today.
- **Order of needs:** unclear story, then counter-test, then missing Condition (the counter-test moves ahead of where "missing part of life" was).
- **Approaches for this need,** least pushy first: story follow-up → "would it have gone differently if…" (any Condition: "…if it had been just the two of you", "…if less was riding on it") → "this week, notice whether it's the same when…". No Thought Experiment for this need.
- **State is never named first:** for a state gap the instruction asks openly ("how were you doing going into that?"), only as a story follow-up or a "notice", and never offers a state.
- **The instruction** is written by code with the Condition and the value to learn, never the Pattern's name or the User's quote, as today; the model words it or leaves it when the moment is wrong. The Reply Plan and the Reply see the need in plain words, like today's needs.
- **Outcome and evidence:** as today. An answer to "would it differ" is a "what if" answer.
- **Rename:** `ExplorationWay` and the stored column on `exploration_tries` become Approach (a migration; mention it in the PR). Prompts, hints, the Agenda's text for the Reply Plan, Eval field `aimed_way` and docs follow. A prompt reload uses `reload_prompt_unless_edited`.
- **Number:** `condition_one_sided_stories` is a Platform Setting with a hint in the Patterns section, overridable in Eval Variants.
- **Directness** is not read here: the order is the same for every User (issue 40 changes that).
- **Understanding Eval:** 3 new Agenda cases, drafted for the owner to correct: a one-sided Pattern gets a question aimed at the unseen value; a Pattern that isn't one-sided gets none; a state gap is asked openly with no state named (a Judge rule).

Evals cost money: show the owner the estimate before any run, and run only the new cases.

## Acceptance criteria

- [x] The coverage table counts clear stories for and against per Condition value, and leaves out unclear, situational and excluded ones
- [x] A missing-Condition need opens only when rules 1 to 3 hold, with tests for: one story only, two stories with different values, the other value already seen against, two Conditions both one-sided
- [x] Home, work and social are handled by this rule; the old "missing part of life" need and its code are gone
- [x] The order of needs is unclear story, counter-test, missing Condition
- [x] A useful try closes that value and it is not asked again; a try with nothing leads to the next Approach after the wait, as today
- [x] The three Approaches are used in order for this need, and a Thought Experiment never is
- [x] For a state gap the instruction names no state and is never a "would it differ"
- [x] The instruction never holds the Pattern's name or the User's quote
- [x] The existing limits still hold with this need: never two Conversations in a row, the wait after nothing, resting, nothing while struggling
- [x] "Way" is renamed Approach in code, the stored column, prompts, hints, Evals and docs; existing tries keep their value through the migration
- [x] `condition_one_sided_stories` is on Platform settings with a hint and can be overridden in an Eval Variant
- [x] 3 new Agenda cases are in the seed and have run once, with the Eval Run ID, result and cost in Comments; the owner was shown the estimate first
- [x] `docs/pattern-pipeline/README.md`, `lifecycle.md` and the `CONTEXT.md` notes on Condition, Approach and Exploration say what is built
- [x] `pytest`, `ruff`, `ruff format` and `mypy` pass, and it was checked in the running app (`/run`): a User with a suspected Pattern seen only in a group gets, in a later Conversation, a question about one-to-one, and the trace page shows the need and the Approach

## For the owner afterwards (not acceptance criteria)

- Correct the 3 drafted Agenda cases.

## Comments

### 26 Nov 2026 — built, checked and closed

**What was built.** `core/condition_coverage.py`: the coverage table (`coverage_of`) and the pick of the one value worth asking about (`missing_condition`). `core/agenda.py`: the `MISSING_CONDITION` need in place of "missing part of life", the new order of needs, `approaches_for` (three Approaches for a Condition, two for state), `condition_question` (the instruction), and a try that keeps its Condition and value. `ExplorationWay` is `ExplorationApproach`. Migration 0111. `condition_one_sided_stories` on Platform settings. Three drafted Agenda cases; a made-up Observation can state audience, stakes and state going in.

**Migration (for the PR).** 0111 renames `exploration_tries.way` to `approach` and `part_of_life` to `condition_value`, adds `condition`, renames the stored values (`other_person` to `would_it_differ`; a `missing_part` try becomes `missing_condition` on `setting`), renames the same fields inside stored Understanding Eval Cases (an Admin's edits included), removes the seed case `agenda-missing-part-of-life-asked` unless edited, and reloads `reply_plan_prompt` unless edited. Going back deletes tries at a Condition other than setting.

**Decisions made while building.**
- Ties between one-sided Conditions go: audience, stakes, relationship, power, stance, setting, state going in. State is last because it is the most sensitive.
- The values asked about leave out online, acquaintance and stranger, as "part of life" left out online.
- Any clear Observation counts in the table, a "what if" answer too, so an answer fills the gap (D12).
- The Approach value `other_person` is now `would_it_differ`, since it also asks about stakes or audience.
- "Would it have gone differently if…" starts from the newest clear story for the Pattern that says the Condition. A state need starts from no story.
- A useful try at the state going in closes every state: the open question is the same whatever the value (found in review).
- The setting's lowest value is 2, so one story is never one-sided.
- Once the most one-sided Condition has nothing left to learn, the next one becomes the need.
- Stored Eval Cases are renamed in place, so an Admin's edited case still loads.

**Review.** Two reviews (standards, spec). Fixed: the state closing rule, the setting's lowest value, a leftover "way" in the Pattern exploring hint, docstrings. Left as judgement calls: state is special-cased in four small places; the Condition and value travel as a pair; `AgendaReader` reads the setting itself.

**Checks.** After the rebase on main (with issue 42): ruff clean, ruff format clean, mypy clean, pytest 2661 passed; web: eslint, prettier and tsc clean, Vitest 991 passed (141 files).

**Eval runs.** The owner was shown the estimate (S$0.02, up to about S$0.05) and said to run, then asked for Haiku, Opus 5.5 and DeepSeek pro as well. For that run the app's estimate was S$0.06; it doesn't price a Variant's model, and my own figure was about S$0.5.

| Run | Model | Passed | Cost |
|---|---|---|---|
| `fa78a26a-7b29-4a9e-9beb-f0b340227baf` | deepseek-v4.1-flash (live), cases as first drafted | 0 of 3 | S$0.02 |
| `fda65a7a-4135-4af7-8b66-b1e3139df1e4` | deepseek-v4.1-flash (live) | 2 of 3 | S$0.02 |
| `8a0bf7b9-8001-4383-833e-bf60d963df51` A | claude-haiku-5.5 | 1 of 3 | S$0.01 |
| `8a0bf7b9` B | claude-opus-5.5 | 2 of 3 | S$0.32 |
| `8a0bf7b9` C | deepseek-v4-pro | 1 of 3 | S$0.09 |

About S$0.47 in all. In every run code wrote the right aimed Curiosity and no reply named a state. The fails were the Reply Plan not picking the aimed Curiosity on a light opener (all but flash) and Judge rules. After the first run two cases were changed (an opener that leaves room for a question; the state rule judges only that no state is named). Details: `docs/pattern-evals/README.md` and issue 20, section 43.

**How it was checked in the running app.** On this worktree's stack (fresh database, migrated to 0111, seeds loaded), as a signed-in test Admin with Pattern noticing and exploring on, real models, and the chat channel swapped for the one that logs instead of sending (a worktree can't reach Telegram). Texts were posted to the Telegram webhook; each Conversation's times were moved back past the quiet gap and the running backend ended it itself. "Situations to be ready" was set to 9 so the Pattern stayed suspected. Two things were set by SQL and not by chat: the counter-test try was marked asked and useful (Zeph didn't pick it in the second Conversation), and later the "would it differ" try was marked asked and useful.

**Evidence per criterion**

- **Coverage table.** `tests/test_condition_coverage.py` (counts for and against per value; unclear, situational and excluded left out). Running app: two real stories, both tagged audience "group" by the tagging model, gave the need "one-to-one".
- **Rules 1 to 3.** `test_one_story_alone_is_not_one_sided`, `test_two_stories_with_different_values_are_not_one_sided`, `test_a_value_already_seen_against_is_not_what_to_learn`, `test_of_two_one_sided_conditions_only_the_one_with_most_stories_is_a_need`, and the tie test. Running app: with the setting at 3 the next Reply Plan read "Still to learn: nothing open now"; at 2 it read the one-to-one need. Relationship (colleague, friend) and setting (work, social) differed, so only audience was the need.
- **Home, work, social by this rule; old need gone.** `test_home_work_and_social_are_asked_about_by_the_same_rule`; no `MISSING_PART`, `part_of_life` or `PARTS_OF_LIFE` left in `src/` or `tests/`. Running app: a stored old-style try (missing part, work) came through the migration as a missing Condition on setting, work.
- **Order of needs.** `test_unclear_stories_come_first_then_a_counter_test_then_a_condition`. Running app: the first aimed Curiosity was the counter-test; the one-to-one question was written only after it was answered.
- **Useful closes the value; nothing leads to the next Approach after the wait.** `test_a_useful_try_closes_that_value_for_good_and_the_next_one_opens`, `test_a_condition_try_with_nothing_leads_to_the_next_approach_after_the_wait`. Running app: "honestly not sure" was judged brushed off; the next try was "would it differ", not before 29 Nov (3 days on). Once that try was useful the next need was "in front of others", and one-to-one was not asked again.
- **Three Approaches in order, never a Thought Experiment.** `test_a_condition_is_asked_by_three_approaches_and_never_a_thought_experiment`. Running app: story follow-up, then "would it differ".
- **State names no state, never "would it differ".** `test_a_state_gap_is_asked_openly_never_by_would_it_differ_and_names_no_state`, `test_a_useful_try_at_the_state_going_in_closes_every_state`. Eval runs (the real app code in the Eval runner): the instruction read "Ask about a recent time … and how they were doing going into it. Ask openly, and name no mood or state yourself", and the replies that asked it ("how were you feeling walking into that conversation?") named none.
- **No Pattern name or quote.** `test_every_aimed_question_is_written_by_code_without_the_pattern` (every Condition value and Approach). Running app: the stored questions and the reply ("I never asked how it goes for you one-on-one…") held neither.
- **The limits still hold.** `test_a_condition_is_never_asked_about_two_conversations_in_a_row`, `test_condition_tries_with_nothing_rest_the_exploration`, and the existing struggling tests. Running app: the Conversation that asked wrote no new try at its end; the next one did, with the wait. Resting and struggling were not run again in the app for this need (same code path as before).
- **Rename; tries keep their value.** `test_the_approach_migration_keeps_every_try_and_renames_stored_eval_cases`. Running app: the stack was put back to 0110, a try set to the old shape and the prompt edited; on restart the backend ran 0111, the try read missing_condition / would_it_differ / setting / work / useful, the edited prompt was kept and the log said "Kept the stored reply_plan_prompt". The trace page shows "story follow-up" as the Approach of the earlier try.
- **The setting.** `test_every_agenda_number_is_a_setting_with_a_hint_and_an_eval_override`. Running app: "Stories that make a Condition one-sided" is in the Patterns section with its hint; changed to 3 in the browser, saved, stored, and the next reply used it.
- **3 cases, run once, in Comments; the owner saw the estimate.** Above. `test_each_seeded_agenda_case_starts_with_the_agenda_it_expects` sets each up with the real Agenda code.
- **Docs.** `docs/pattern-pipeline/README.md`, `lifecycle.md`, `CONTEXT.md` (Condition, Approach, Exploration), `docs/pattern-evals/README.md`, `docs/thought-experiments/README.md`, ADR 0026 and 0031.
- **Checks pass; the /run check.** Above. A User whose Pattern was seen only in a group (team meeting, dinner with friends) was asked, in a later Conversation, "I never asked how it goes for you one-on-one. Like a disagreement with someone you actually care about, not a room full of people. Does that play out differently?". The trace page of that reply (`/admin/model-calls/…`, Reply Plan → Content) showed "Still to learn: how it goes for them one-to-one, with just one other person, not heard yet" and "Tried before: 23 Nov 2026, story follow-up: … (useful)".

**Not done.** The migration was not run on a copy of the main database (the main stack wasn't running). The Eval Variant override of the new setting was checked by test only.

## Completion

- Completed: 2026-11-26
- Commit: <to be filled in after the merge>
