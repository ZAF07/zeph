# 15 — The other twelve Pattern Types, and the Pattern Catalog guide

Status: ready-for-human
Track: B
Blocked by: 10

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 69, 70). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Write the remaining twelve Pattern Types in full, to the same standard as the three drafted, from the list in `.scratch/pattern-pipeline/grill-decisions.md` (decision 30): for each, the definition, if / then / function, five or so signs with strength and part, signs against, look-alikes with what tells them apart, exclusions, approved wording, Prediction wording and numbers. Our own words only: no copyrighted questionnaire items, no clinical language. The relationships ones get the longest exclusion lists. All start as draft.

Also write `docs/pattern-catalog/README.md`: what the catalog is, what each field does, how to change or add a Pattern Type, and what each change does to the system (e.g. a changed strength shifts scores on the next scoring; an archived Pattern Type stops being looked for).

An agent can draft both. The owner then reads each Pattern Type and marks it approved or sends it back; that part is why this issue is ready-for-human.

## Acceptance criteria

- [ ] Twelve more Pattern Types load without error, three per area with relationships added, fifteen in all
- [ ] Every look-alike named exists in the catalog, and each pair's "what tells them apart" reads both ways
- [ ] No clinical terms and no copied questionnaire wording
- [ ] `docs/pattern-catalog/README.md` exists and covers the fields, how to change one and what each change does
- [ ] The owner has reviewed each Pattern Type and set its status
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

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
