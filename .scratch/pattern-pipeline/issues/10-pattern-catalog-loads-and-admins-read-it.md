# 10 — The Pattern Catalog loads from YAML and Admins can read it

Status: ready-for-agent
Track: B
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 64, 65, 67). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Pattern Types live in the repo as YAML and are loaded into the database on deploy (ADR-0025). Each has a stable ID, a version, one of five areas (conflict, approval, control, achievement, relationships), a definition, its if / then / function, signs (each with a strength and the part it shows), signs against, look-alikes with what tells them apart (including what anyone would do), exclusions (each saying whether evidence is ignored or counted but not shared), approved wording, Prediction wording, its own numbers, and a status (draft, approved with who and when, or archived).

The loader refuses a malformed Pattern Type and says why. Past versions are kept. Admins read every Pattern Type on a new read-only Dashboard page. This issue ships the three already drafted in the source catalog doc (linked from `.scratch/pattern-pipeline/grill-decisions.md`), all as draft.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] The three drafted Pattern Types are YAML in the repo and load into the database when the backend starts
- [ ] A Pattern Type missing a required field, naming an unknown look-alike or using a value outside a fixed list stops the load with a clear message
- [ ] Changing a Pattern Type's version keeps the old version's row
- [ ] Admins see each Pattern Type with all its details and status on the Dashboard, with no way to edit
- [ ] A non-Admin can't reach the page or its API
- [ ] Nothing in the reply path changes yet
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

None - can start immediately

## Comments
