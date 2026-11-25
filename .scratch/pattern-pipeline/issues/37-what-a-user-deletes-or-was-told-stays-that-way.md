# 37 — "Never again" after a deleted Pattern, the wording a User was told, and the ruled-out topics

Status: ready-for-agent
Track: shared
Blocked by: 35 (same deletion paths)

## Parent

`30-owner-decisions-before-pattern-sharing-is-on.md`, answers 3, 4 and 12.

## What to build

1. **"Never again" mark (answer 4).** When a User deletes a Pattern they disagreed with or that didn't hold up, keep a mark: the User and the Pattern Type, none of their words. For a marked Pattern Type the tagging checks keep no Observation (first or second Pattern Type), also when a day is tagged again, and scoring never starts a Pattern. Delete My Data and Account Deletion remove the mark. Deleting a Pattern being tested or confirmed leaves no mark.
2. **The wording they were told (answer 12).** When a Pattern is shared, the approved wording used is saved on it (`patterns.shared_wording`). The Patterns tab shows that wording, and shows and can delete a told Pattern whose Pattern Type left the catalog.
3. **Ruled-out topics (answer 3).** The seed list becomes: abuse, sexual trauma, self-harm or suicide, eating and body image, addiction, sexuality and gender, mental health diagnoses. A migration updates a stored list that still equals the old seed list, and leaves an Admin's edit alone. A topic added later reaches new Observations only (documented as a limit).

## Acceptance criteria

- [ ] After deleting a disagreed or closed Pattern, new stories of that Pattern Type keep no Observation and start no Pattern, with tests
- [ ] Delete My Data removes the mark, with a test
- [ ] A told Pattern shows the wording it was shared with, and one whose Pattern Type left the catalog can be seen and deleted, with tests
- [ ] The ruled-out topics list is the owner's, on a fresh database and on one that still had the old seed list
- [ ] `docs/pattern-pipeline/README.md` and `CONTEXT.md` say what changed
- [ ] `ruff`, `ruff format`, `mypy` and `pytest` pass, and it was checked in the running app

## Comments
