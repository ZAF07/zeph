# 42 — "Anyone would act the same" can match the new Conditions

Status: ready-for-agent
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

- [ ] A match naming an audience, stakes or state marks a fitting Observation situational, and an Observation with that Condition empty is not marked
- [ ] A catalog file naming a value outside a list is refused at load, and the last good catalog stays
- [ ] ACH.WORTH.PERF and CTRL.UNCERT.PLAN have new versions with high stakes, approved by the owner, and the old versions are kept
- [ ] An Observation of either, tagged high stakes, carries no weight in scoring and at the ready gate
- [ ] The two Tagging cases expect situational and pass in one run of those cases (estimate shown to the owner first; Run ID and cost in Comments)
- [ ] `docs/pattern-pipeline/README.md` drops the "can't be put as tags" limit, and `docs/pattern-catalog/README.md` lists the new fields
- [ ] `pytest`, `ruff`, `ruff format` and `mypy` pass, and it was checked in the running app (`/run`): a high-stakes story for one of the two Pattern Types is stored as situational

## Comments
