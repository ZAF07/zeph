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
