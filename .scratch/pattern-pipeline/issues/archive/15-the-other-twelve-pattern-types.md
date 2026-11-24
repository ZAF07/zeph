# 15 — The other twelve Pattern Types, and the Pattern Catalog guide

Status: completed
Track: B
Blocked by: 10

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 69, 70). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Write the remaining twelve Pattern Types in full, to the same standard as the three drafted, from the list in `.scratch/pattern-pipeline/grill-decisions.md` (decision 30): for each, the definition, if / then / function, five or so signs with strength and part, signs against, look-alikes with what tells them apart, exclusions, approved wording, Prediction wording and numbers. Our own words only: no copyrighted questionnaire items, no clinical language. The relationships ones get the longest exclusion lists. All start as draft.

Also write `docs/pattern-catalog/README.md`: what the catalog is, what each field does, how to change or add a Pattern Type, and what each change does to the system (e.g. a changed strength shifts scores on the next scoring; an archived Pattern Type stops being looked for).

An agent can draft both. The owner then reads each Pattern Type and marks it approved or sends it back; that part is why this issue is ready-for-human.

## Acceptance criteria

- [x] Twelve more Pattern Types load without error, three per area with relationships added, fifteen in all
- [x] Every look-alike named exists in the catalog, and each pair's "what tells them apart" reads both ways
- [x] No clinical terms and no copied questionnaire wording
- [x] `docs/pattern-catalog/README.md` exists and covers the fields, how to change one and what each change does
- [x] The owner has reviewed each Pattern Type and set its status
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `10-pattern-catalog-loads-and-admins-read-it.md`

## Comments

Plan (24 Nov 2026, branch `pattern-15-other-twelve`, worktree `ai-chat-companion-pattern-15`, ports 3030/8030/5462):

- Twelve new YAML files in `src/companion/seed/pattern_catalog/`, all `draft`, `0.1.0`, from decision 30. IDs: CONF.DEFEND.SELF, CONF.WITHDRAW.HURT, APPR.GIVE.NEEDED, APPR.CONFIRM.CHOICE, APPR.HIDE.BURDEN, CTRL.SELF.RELY, CTRL.OPEN.FREEDOM, ACH.ABSORB.PULL, ACH.GOAL.MOVE, REL.CHECK.SECURE, REL.DISTANCE.INDEP, REL.MOOD.FIX.
- Look-alikes go both ways: when A names B, B names A with the same difference from its own side. The six pairs in decision 30 are included. The three drafted types get new look-alikes, so each gets a new version (a stored version never changes): CONF.AVOID.BELONG 0.3.0, CTRL.UNCERT.PLAN 0.2.0, ACH.WORTH.PERF 0.2.0.
- New tests on the real seed: fifteen load, three per area; every look-alike pair is named both ways; no clinical terms in any text the model or a User may see (frameworks are references for the owner and are left out).
- `anyone_would_when` tags only where a tag says it well (e.g. pushing back at a hostile stranger).
- Tagging Eval: `test_the_tagging_seed_covers_each_kind_of_case_for_every_pattern_type` needs a case for and against for every Pattern Type, so 24 short new cases (one for, one against per new type) go in `seed/evals/cases/tagging.yaml`, drafted for the owner like the first 44.
- Design fixture JSON regenerated from the API; `web/design/reference/AdminPatternCatalog.html` updated to fifteen cards (it still showed CONF at 0.1.0); pixel test run.
- `docs/pattern-catalog/README.md`: what the catalog is, each field and what it does, how to change or add one, what each change does.
- The owner's review (approve or send back each type) is theirs: asked at the end, before archiving.

Decisions made while building (24 Nov 2026):

- **Look-alikes both ways, in one style:** each `tells_apart` says "this one…; the other…". The three old pairs between the first three types were reworded the same way (review finding).
- **Versions:** the three drafted types got new versions for their new look-alikes (CONF.AVOID.BELONG 0.3.0, CTRL.UNCERT.PLAN 0.2.0, ACH.WORTH.PERF 0.2.0). Later edits on this branch (review fixes, approval, wording) went into those same versions, and the twelve new ones stay at 0.1.0, because none of them had been loaded anywhere but this worktree's own database. Production's stored 0.2.0 / 0.1.0 / 0.1.0 stay as older versions.
- **Owner review (24 Nov 2026):** Zaf read all fifteen, said "looks good", and asked to drop "avoidance". All fifteen are `approved`, `approved_by: Zaf`, `approved_on: 2026-11-24`. CONF.AVOID.BELONG is now named "Softening disagreement to protect belonging"; its "anyone would" and ACH.WORTH.PERF's "then" no longer say "avoidance". The clinical-terms test now also bans "avoidance".
- **Reference and baseline:** `web/design/README.md` says agents don't edit `reference/` or `baseline/`; Zaf chose to keep this branch's update of `AdminPatternCatalog.html` and its baseline (rebuilt on this machine with `shoot.cjs`, this page only).
- **Tagging Eval:** 24 cases added so every Pattern Type has a case for and against (the seed test asks for it). Not run (Zaf: skip for now; it costs money). The first 44 cases were written for a three-type catalog; with fifteen, some may now come back tagged as one of the new look-alikes. Worth a run once Zaf has corrected the cases.
- **Archived is still tagged today:** the tagging step reads every Pattern Type whatever its status; the guide says so. Only the Ready gate and sharing will read status.
- **A test fixed in place:** `test_loading_the_same_files_again_changes_nothing` compared `SELECT *` rows with no order; with fifteen Pattern Types Postgres returned them in another order after the second load. Both reads now order by ID and version.

Evidence (24 Nov 2026, worktree stack on 3030/8030, build `ef2c110` rebased on main `2046df9`):

- **Fifteen load, three per area.** Backend start log has no "can't be loaded"; `pattern_types` holds 15 current rows, all approved. Upgrade path, as production will take it: main's three files were loaded first, then the new files on restart; CONF 0.2.0, CTRL 0.1.0 and ACH 0.1.0 stayed as not current, the new versions became current. Admin Pattern Catalog page: "15 Pattern Types", 15 cards at 1280 and 390, no page errors, no sideways scroll. Tests: `test_the_fifteen_pattern_types_in_the_repo_are_approved_three_per_area`, `test_the_fifteen_pattern_types_are_loaded_on_start`.
- **Look-alikes exist and read both ways.** The loader refuses a look-alike that isn't in the catalog; `test_every_look_alike_in_the_repo_is_named_back_by_the_other_pattern_type` passes. On the page with "Expand all", every card lists its look-alikes with the other type's name and ID, and each pair says the same difference from both sides (read for all 15; e.g. REL.CHECK.SECURE ↔ APPR.CONFIRM.CHOICE "checks whether the bond is still okay; the other checks whether they chose right" and back). The six pairs in decision 30 are all there.
- **No clinical terms, no copied questionnaire wording.** `test_no_pattern_type_in_the_repo_uses_clinical_terms_outside_its_frameworks` checks every field a model or User may read (names, definitions, signs, look-alikes, anyone would, exclusions, wording) for a list of clinical words, now including "avoidance"; the page text has no "avoidance". All signs and wording were written fresh; questionnaires and theories are only named under `frameworks`.
- **Guide.** `docs/pattern-catalog/README.md`: what the catalog is, a table of every field with what reads it today, writing rules, how to change one (new version, both sides of a look-alike, fixture and reference, Tagging Eval, deploy), how to add one, a table of what each change does (e.g. a changed strength shifts scores on the next scoring; archived is still looked for today and stops being looked for once built), review status. Claims checked against `core/observations.py` and `core/pattern_scoring.py` in the spec review.
- **Owner set each status.** All 15 approved by Zaf on 24 Nov 2026; the page shows 15 "Approved" chips and 15 "Approved by Zaf on 24 Nov 2026. May be shared once ready." lines, no "Draft".
- **Checks.** `make check` on `ef2c110`: ruff and ruff format clean, mypy "no issues found in 247 source files", pytest 2037 passed, Prettier, ESLint and `tsc` clean, Vitest 953 passed. Pixel test (copy of `compare.cjs` that blocks Clerk's protect probes, as before): "PASS AdminPatternCatalog 0.00% differs, height 3669 vs 3669". The running app seeds all 68 Tagging cases.

- **After the last rebase** (main `ce2e125`, build `5527a45`): `make check` again all clean, pytest 2058 passed, Vitest 953 passed; `make restart` built and started, 15 approved Pattern Types current, no load errors.

## Completion

- Completed: 2026-11-24
- Commit: <to be filled in after merge>
