# 37 — "Never again" after a deleted Pattern, the wording a User was told, and the ruled-out topics

Status: completed
Track: shared
Blocked by: 35 (same deletion paths)

## Parent

`30-owner-decisions-before-pattern-sharing-is-on.md`, answers 3, 4 and 12.

## What to build

1. **"Never again" mark (answer 4).** When a User deletes a Pattern they disagreed with or that didn't hold up, keep a mark: the User and the Pattern Type, none of their words. For a marked Pattern Type the tagging checks keep no Observation (first or second Pattern Type), also when a day is tagged again, and scoring never starts a Pattern. Delete My Data and Account Deletion remove the mark. Deleting a Pattern being tested or confirmed leaves no mark.
2. **The wording they were told (answer 12).** When a Pattern is shared, the approved wording used is saved on it (`patterns.shared_wording`). The Patterns tab shows that wording, and shows and can delete a told Pattern whose Pattern Type left the catalog.
3. **Ruled-out topics (answer 3).** The seed list becomes: abuse, sexual trauma, self-harm or suicide, eating and body image, addiction, sexuality and gender, mental health diagnoses. A migration updates a stored list that still equals the old seed list, and leaves an Admin's edit alone. A topic added later reaches new Observations only (documented as a limit).

## Acceptance criteria

- [x] After deleting a disagreed or closed Pattern, new stories of that Pattern Type keep no Observation and start no Pattern, with tests
- [x] Delete My Data removes the mark, with a test
- [x] A told Pattern shows the wording it was shared with, and one whose Pattern Type left the catalog can be seen and deleted, with tests
- [x] The ruled-out topics list is the owner's, on a fresh database and on one that still had the old seed list
- [x] `docs/pattern-pipeline/README.md` and `CONTEXT.md` say what changed
- [x] `ruff`, `ruff format`, `mypy` and `pytest` pass, and it was checked in the running app

## Comments

### 25 Nov 2026: built

**Checks.** ruff clean, ruff format clean, mypy clean (286 files), pytest 2584 passed; web: eslint, prettier and tsc clean, Vitest 989 passed (141 files).

**How it was checked in the running app.** On this worktree's stack (fresh database, migrated to 0109, seeds loaded). Dashboard pages were driven in a real browser as a signed-in Admin and User. The chat path was run by the real core services on the stack's database with only the chat model scripted, the chat channel recording, and the clock and scheduler moved by hand (a worktree can't reach Telegram), acting as the signed-in User so the browser showed the result. Not checked: the migrations on a copy of the main database (the main stack wasn't running); the tests cover them by downgrading and migrating again.

**Evidence per criterion**

- **After deleting a disagreed or closed Pattern, no Observation and no Pattern.** `test_a_deleted_pattern_they_disagreed_with_or_that_did_not_hold_up_never_returns` (both states), `test_scoring_starts_no_pattern_for_a_pattern_type_marked_never_again`; a confirmed one leaves no mark (`test_deleting_a_pattern_removes_it…`). Running app: as the User, deleted the "Didn't hold up" Pattern on the Patterns tab; `patterns_never_again` held CONF.AVOID.BELONG; a new Conversation with a story tagged for it kept no Observation and started no Pattern.
- **Delete My Data removes the mark.** `test_delete_my_data_removes_every_kind_of_data_but_keeps_the_account` (the table must hold a row before and none after).
- **The wording it was shared with; a Pattern Type gone from the catalog.** `test_a_pattern_shows_the_wording_it_was_told_in_even_after_its_type_is_gone`. Running app: `shared_wording` was saved at sharing and shown on the Patterns tab; with the Pattern Type renamed in the database to one not in the catalog, the tab still showed the Pattern with its wording, quotes and Predictions, and it could be deleted.
- **The ruled-out topics are the owner's.** `test_the_gate_numbers…` (seven topics on a fresh database), `test_the_migration_reloads_the_ruled_out_topics_unless_an_admin_changed_them`. Running app: the stack's stored list is the seven topics.
- **Docs.** `docs/pattern-pipeline/README.md`, `lifecycle.md`, `tagging.md`, `CONTEXT.md` (Pattern).
- **Checks pass; checked in the running app.** Above.

## Completion

- Completed: 2026-11-25
- Commit: efe99ea5 ("Merge pattern-30-owner-decisions-before-sharing: the owner's decisions before Pattern sharing is on", the merge of pattern-30-owner-decisions-before-sharing into main; work commits b4fdc35d, 351f74c8, ec11f7a8, e21f096b, f9225f60, 7522ee99, 45d716a0, cc0fd499, ff840919, 875f3175, 88bc0a4a)
