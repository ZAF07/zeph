# 42 — "Anyone would act the same" can match the new Conditions

Status: completed
Track: A
Blocked by: 41

## Parent

Issue 23, decision D11. ADR-0031, ADR-0025 (a catalog change is a new version). How to change a Pattern Type: `docs/pattern-catalog/README.md`.

## What to build

A Pattern Type's `anyone_would_when` can name audience, stakes and state, so code can tell which Observations carry no weight. Today it can match only relationship, power, setting and stance, which is why ACH.WORTH.PERF's and CTRL.UNCERT.PLAN's "anyone would" (high stakes) can't be put as tags.

- `SituationMatch` gains audiences, stakes and states; an Observation fits when, for every tag the match names, its own value is one listed (the rule as today). An empty Condition never fits a match that names it.
- The catalog loader reads the new fields and refuses a value outside its list.
- ACH.WORTH.PERF and CTRL.UNCERT.PLAN each get a new version with `anyone_would_when` high stakes. **The owner approves each new version** before it is marked approved (ADR-0025).
- The ready gate already judges "situational" by the catalog now, so nothing changes there.
- The Admin Pattern Catalog page shows `anyone_would_when` if it does by then; otherwise leave it, as today.
- The two high-stakes Tagging cases from issue 41 now expect situational.

## Acceptance criteria

- [x] A match naming an audience, stakes or state marks a fitting Observation situational, and an Observation with that Condition empty is not marked
- [x] A catalog file naming a value outside a list is refused at load, and the last good catalog stays
- [x] ACH.WORTH.PERF and CTRL.UNCERT.PLAN have new versions with high stakes, approved by the owner, and the old versions are kept
- [x] An Observation of either, tagged high stakes, carries no weight in scoring and at the ready gate
- [x] The two Tagging cases expect situational and pass in one run of those cases (estimate shown to the owner first; Run ID and cost in Comments)
- [x] `docs/pattern-pipeline/README.md` drops the "can't be put as tags" limit, and `docs/pattern-catalog/README.md` lists the new fields
- [x] `pytest`, `ruff`, `ruff format` and `mypy` pass, and it was checked in the running app (`/run`): a high-stakes story for one of the two Pattern Types is stored as situational

## Comments

### 26 Nov 2026 — built, checked and closed

**What was built.** `SituationMatch` gains `audiences`, `stakes` and `states`; `is_situational` checks them with the same rule, so an empty Condition never fits a match that names it. The catalog loader reads `audience`, `stakes` and `state_going_in` in an `anyone_would_when` match and refuses a value outside its list. ACH.WORTH.PERF and CTRL.UNCERT.PLAN are at 0.4.0 with `anyone_would_when: [{stakes: [high]}]`. The two high-stakes Tagging cases expect situational. No migration, no prompt change, no Dashboard change.

**Decisions made while building.**
- The catalog field is `state_going_in`, the name issue 41 uses everywhere.
- **The owner approved both 0.4.0 versions in chat on 26 Nov 2026**, so both have `approved_on: 2026-11-26`. The test that all fifteen were approved on 24 Nov now names these two for 26 Nov.
- An empty list in a match (`stakes: []`) is now refused at load, for the old four tags too. Before, it made a match that fits every Observation (found in the spec review).
- The design fixture and `AdminPatternCatalog.html` show v0.4.0 for the two cards (shared design files: the version text only, as the catalog guide's step 4 asks).
- The Admin Pattern Catalog page still doesn't show `anyone_would_when`, so it was left.
- The standards review's judgement calls were left: the seven tag names are written out in three places, and `SituationMatch.states` (the issue's name) holds states going in.

**Checks.** After the rebase on main: pytest 2618 passed, ruff clean, ruff format clean, mypy clean (280 files). Web (before the rebase, which brought no web change): eslint, prettier and tsc clean, Vitest 991 passed.

**Eval run (the owner picked five cases and saw the estimate first: about S$0.05 from me, S$0.0202 from the app).**

| Run | Tagging model | Result | Cost |
|---|---|---|---|
| `50e37290-219e-4978-9c46-a4ffb2fda601` | deepseek-v4.1-flash (live) | 2 passed, 2 failed, 1 error | S$0.0305 |

`cond-high-stakes-visa-interview` and `cond-high-stakes-mortgage-decision` passed: stakes high, situational. The two older `ctrl-anyone-` cases failed as they did before this issue (a "for" and nothing, where they expect a sign against); `ach-anyone-lost-big-bid` got no answer from the provider and was not run again. See issue 20.

**How it was checked in the running app.** On this worktree's stack (fresh database), as a signed-in test Admin with Pattern noticing on. Stories were posted to the Telegram webhook, the Conversation's times were moved back past the quiet gap, and the running backend ended each Conversation itself with the real model. A worktree can't reach Telegram, so no reply was sent. The last story and the catalog checks were done again on the final code after the review fixes.

**Evidence per criterion**

- **A match naming a Condition marks a fitting Observation; an empty one is not marked.** `test_situational_means_the_tags_fit_one_anyone_would_situation` (9 new rows), `test_a_high_stakes_story_of_a_pattern_type_that_says_so_is_situational`. Running app: four stories tagged stakes high were stored situational; one tagged stakes low was not.
- **A value outside a list is refused and the last good catalog stays.** `test_a_wrong_anyone_would_when_is_refused_with_a_reason`, `test_a_condition_outside_its_list_is_refused_and_the_last_catalog_kept`. Running app: the backend's own load step on a folder with `stakes: [huge]` (and `stakes: []`) printed both problems and "The backend starts with the catalog as it was last loaded"; the stored rows were unchanged.
- **New versions with high stakes, approved, old ones kept.** `test_the_two_high_stakes_pattern_types_say_so_as_tags`, the approval test. Running app: after the 0.3.0 files were loaded and the backend restarted on this branch, `pattern_types` held 0.4.0 current and 0.3.0 kept for both. Approved by the owner in chat.
- **A high-stakes Observation of either carries no weight in scoring and at the gate.** `test_a_high_stakes_story_is_stored_situational_and_adds_no_points`, `test_high_stakes_stories_block_where_anyone_would_act_the_same_then`. Running app: the real scoring and gate code, run in the backend container on the stored Observations, gave each high-stakes one 0 points; CTRL.UNCERT.PLAN scored 0 points, 0 situations; ACH.WORTH.PERF scored 140 points, 1 situation, all from the low-stakes story. With the stored mark taken off, scoring counted them and the gate's "without situational" score still did not. The gate was not driven to "ready" in the running app: that needs three situations and a counter-test.
- **The two Tagging cases expect situational and pass in one run.** Above.
- **Docs.** `docs/pattern-pipeline/README.md` (limit dropped, a "Built" paragraph), `docs/pattern-catalog/README.md` (the fields, what a change does), `tagging.md`, `docs/pattern-evals/README.md`, `CONTEXT.md`, ADR 0031's status.
- **Checks pass; a high-stakes story is stored as situational.** Above: "If I don't get this job we lose the visa…" was stored as ACH.WORTH.PERF 0.4.0, I3, stakes high, situational.

**For the owner (in issue 20).** A sign against told with high stakes also counts for nothing (CTRL.UNCERT.PLAN's D2); a guessed "high" now costs evidence, so check the production tagging prompt after the deploy; the two `ctrl-anyone-` cases need new expectations.

## Completion

- Completed: 2026-11-26
- Commit: <filled in after the merge>
