# 41 — Conditions are tagged on Observations: audience, stakes, state going in

Status: completed
Track: A
Blocked by: none

## Parent

Issue 23 (`23-situations-vary-on-more-than-people.md`) holds every decision with its reason: read D4, D7, D8, D14, D16 and D17 first. ADR-0031. Terms: **Condition** in `CONTEXT.md`. How tagging works today: `docs/pattern-pipeline/tagging.md`.

## What to build

An Observation gains three Conditions beside relationship, power, setting and stance. The tagging step fills them, code checks them, and they are stored. Nothing reads them yet (issues 42, 43 and 44 do).

- **Lists** (closed, in `core/models.py` beside the others):
  - audience: one-to-one, group, in front of others (people watching who aren't part of it).
  - stakes: low, high (high: something that matters to the User could be lost).
  - state going in: worn out, under pressure, low, steady (how the User was before it happened, not after).
- **Tagging prompt:** given the three lists with one line each on what they mean. A Condition is filled only when the User's story says it; otherwise it is left empty, never guessed. One value per Condition: when a story gives two, the one it leans on, or empty when the model can't tell. State is as of when the story happened, from the User's own words in this Conversation. The prompt's lists are built from the enums if issue 31 has done that; otherwise follow what is there.
- **Checks (`plan_observations`):** a Condition with a value outside its list drops the Observation, as for today's tags (counted under "Dropped by code"). Empty is valid.
- **No state after a crisis:** Observations from a Conversation with a Safeguard Event are kept with state empty, whatever the model answered.
- **Storage:** three nullable columns on `observations` (a migration; mention it in the PR). No data migration: nothing was kept before (D16).
- **Privacy:** nothing new on "Things you said that Zeph kept", nothing new for Admins. The Conditions go with their Observation.
- **Prompt reload:** the migration reloads `pattern_tagging_prompt` with `reload_prompt_unless_edited`.
- **Tagging Eval:** a case may state the Conditions it expects for an Observation, "must be empty" included; when stated they must match for the case to pass, and the Case Result shows expected and kept Conditions. About 10 new seed cases, drafted for the owner to correct: each new Condition said, so tagged (3); nothing said, so all empty (2); the User says how they felt after, so state stays empty (2); two people and a group, audience against relationship (1); two cases of high stakes said plainly (2; issue 42 turns them into "anyone would" cases).

Evals cost money: show the owner the estimate before any run, and run only the new cases.

## Acceptance criteria

- [x] The three lists exist as closed lists, and an Observation holds one value or none for each
- [x] The tagging prompt explains the three Conditions, says to leave one empty when the story doesn't say it, and says state is before the event, from the User's own words
- [x] An Observation with a Condition outside its list is dropped and counted; one with empty Conditions is kept
- [x] An Observation from a Conversation with a Safeguard Event is stored with state empty
- [x] The Conditions are stored and read back with the Observation; deleting the Observation removes them
- [x] "Things you said that Zeph kept" and the Admin pages show nothing new
- [x] A migration that reloads the tagging prompt keeps an Admin's edit
- [x] A Tagging Eval case can expect Conditions, including "must be empty", and fails when they don't match
- [x] About 10 new Tagging cases are in the seed, and the new cases have run once, with the Eval Run ID, score and cost in Comments
- [x] The owner was shown the estimate before the run
- [x] `docs/pattern-pipeline/README.md` and `tagging.md` say what was built
- [x] `pytest`, `ruff`, `ruff format` and `mypy` pass, and a real Conversation end was checked in the running app (`/run`): a story that says an audience, stakes and a state is stored with them, and one that says none is stored with them empty

## For the owner afterwards (not acceptance criteria)

- Correct the drafted Tagging cases (`docs/pattern-evals/adding-tagging-cases.md`).

## Comments

### 26 Nov 2026 — built, checked and closed

**What was built.** Three closed lists (`Audience`, `Stakes`, `StateGoingIn` in `core/models.py`) and three fields on `SituationTags`. `read_tags` checks all seven Conditions from one list (`CONDITION_LISTS`), which also writes the lists into the model's input. `TaggingContext.had_safeguard_event` empties state. Migration 0110 adds three nullable columns and reloads `pattern_tagging_prompt` unless edited. A Tagging case's expected Observation may state `audience`, `stakes` and `state_going_in` (a value or `empty`); the Case Result shows a Conditions line. Ten `cond-` seed cases.

**Decisions made while building.**
- The field, column and JSON key are all `state_going_in` ("state" alone reads like a lifecycle state).
- A Condition written as `""` counts as empty, like null.
- "A Conversation with a Safeguard Event" is read as: the User had a Safeguard Event at or after the Conversation's first message. A Safeguard Event has no link to its Conversation. See the finding in issue 20.
- The kept Conditions show on a Case Result only when the case states some or some were kept, so older results look the same.
- After the first Eval run the prompt got two more lines (one other person is not "one-to-one"; a small matter is not "low" stakes, unless said). They go past "one line each", and follow D4.
- The standards review's judgement calls were left: `happened_from` beside `happened_since` (they differ by one sign), and the three names written out in a few places.

**Checks.** ruff clean, ruff format clean, mypy clean (287 files), pytest 2596 passed; web: eslint, prettier and tsc clean, Vitest 991 passed (141 files).

**Eval runs (the owner was shown each estimate first, and asked for the three-model comparison).**

| Run | Tagging model | Passed | Cost |
|---|---|---|---|
| `7f09461a-5f0d-4d27-a7f1-8add3e27b712` | deepseek-v4.1-flash (live), first prompt | 7 of 10 | S$0.078 (estimate S$0.04) |
| `bd350ed4-9db8-4beb-9fa7-891240b37c2c` A | deepseek-v4.1-flash (live) | 9 of 10 | about S$0.06 |
| `bd350ed4` B | claude-opus-5.5 | 9 of 10 | about S$0.81 |
| `bd350ed4` C | claude-haiku-5.5 | 10 of 10 | about S$0.02 |

Estimates shown: S$0.04 for the first run; for the second, the app's S$0.22 and my own S$1.20 by the price list (real: about S$0.90). In the second run no Condition was wrong on any model; the two fails were a "hers" in a context line (flash) and an unclear look-alike (Opus). What the first run showed and the rest is in `docs/pattern-evals/README.md` and issue 20.

**How it was checked in the running app.** On this worktree's stack (fresh database, migrated to 0110, seeds loaded), as a signed-in test Admin with Pattern noticing on. Stories were posted to the Telegram webhook, the Conversation's times were moved back past the quiet gap, and the running backend ended each Conversation itself with the real model. A worktree can't reach Telegram, so no reply was sent; the Conversation end doesn't need one. The Safeguard Event was a row added by hand, since the Crisis Reply can't be sent there.

**Evidence per criterion**

- **Three closed lists; one value or none each.** `core/models.py`; `test_an_observation_holds_the_conditions_the_story_says_and_none_it_does_not`.
- **The prompt.** `pattern_tagging_prompt` in the seed; `test_the_seeded_tagging_prompt_says_to_leave_an_unsaid_condition_empty`. Running app: the stack's stored prompt held the new text, and the model followed it (below).
- **Off its list dropped and counted; empty kept.** `test_an_observation_with_a_condition_off_its_list_is_dropped_and_counted` (4 kinds), and the stored test below ("huge" stakes dropped). Running app: the trace page showed tagged 1, dropped 0 for a story with all three.
- **Safeguard Event → state empty.** `test_no_state_is_kept_from_a_conversation_with_a_safeguard_event`, `test_a_conversation_with_a_safeguard_event_keeps_observations_without_a_state` (seen red without the rule). Running app: "I was already feeling really low that morning … just the two of us on the phone" in a Conversation with a Safeguard Event was stored with audience one-to-one and state empty.
- **Stored and read back; deleted with the Observation.** `test_the_conditions_a_story_says_are_stored_with_its_observation_and_others_empty`. Running app: the all-hands story was stored with audience "in front of others", stakes "high", state "worn out"; the brother-and-film story with all three empty. Deleting quotes on "Things you said" in the browser removed their rows (3 → 1; my script pressed delete twice).
- **Nothing new for Users or Admins.** No User or Admin API reads the Conditions (only the Eval API, for made-up Users). Running app: "Things you said" showed quote, day and Zeph's note only; the Users page and the trace page were unchanged. An Admin's own trace content holds the model's raw answer, as before (issue 20).
- **The migration keeps an Admin's edit.** `test_the_migration_that_adds_conditions_keeps_a_tagging_prompt_an_admin_edited`. Running app: with the stored prompt edited and the stack put back to 0109, the backend ran 0110 again, kept the edit and logged "Kept the stored pattern_tagging_prompt".
- **A case can expect Conditions, "must be empty" included.** `test_a_tagging_case_that_expects_conditions_passes_only_when_they_match`; `TaggingResultPanel.test.tsx`. Running app: the Case Result of `cond-stakes-friend-owes-deposit` showed the expected and kept Conditions in the browser, and the case form opened.
- **About 10 cases, run once, in Comments; the owner saw the estimate.** Above.
- **Docs.** `docs/pattern-pipeline/README.md`, `tagging.md`, `docs/pattern-evals/README.md`, `adding-tagging-cases.md`, `CONTEXT.md`, ADR 0031's status.
- **Checks pass; a real Conversation end was checked.** Above.

**Not done.** The migration was not run on a copy of the main database (it adds three empty columns and uses the tested reload helper).

## Completion

- Completed: 2026-11-26
- Commit: <merge commit, filled in after the merge>
