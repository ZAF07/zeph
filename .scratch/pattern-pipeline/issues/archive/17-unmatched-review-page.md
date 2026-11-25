# 17 — Admins review what Zeph keeps noticing that fits no Pattern Type

Status: completed
Track: B
Blocked by: 16

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 84, 85). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

An Admin page lists what keeps turning up unmatched, so the catalog can grow. To protect privacy each entry is a general description with no User details (no names, quotes, places or dates) and how many Users it appeared for. The description is written when the unmatched Pattern is kept, about the way of acting and never about the person, and like descriptions are grouped by meaning. The Admin marks each entry: new Pattern Type, folded into an existing one (naming it), or dropped. Writing the YAML stays manual. The model-suggestions feature is out of scope (parked in the decisions file).

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [x] The page lists unmatched entries with a general description and a count of Users, most Users first
- [x] No entry shows a User's name, quote, or any detail that could identify them; a test checks the description is built only from the general wording
- [x] Like descriptions from different Users are grouped into one entry
- [x] An Admin can mark an entry as new Pattern Type, folded into a named Pattern Type, or dropped, and filter by that
- [x] A dropped entry doesn't return unless it appears for more Users
- [x] A non-Admin can't reach the page or its API
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `16-existing-patterns-move-across-and-unmatched-patterns.md`

## Comments

Plan (25 Nov 2026, branch `pattern-17-unmatched-review-page`, worktree `ai-chat-companion-pattern-17`):

- **General description.** The Pattern keeping step writes a `general` line with each new unmatched Pattern: the way of acting only, no names, quotes, places or dates. For an unmatched Pattern kept earlier with none (the live User's), it is asked for one too. Code drops a description holding a digit, a quote mark or the User's name; the Pattern is still kept and is asked about again next time. Saved as `patterns.general_description`. The keeping prompt is reloaded from the seed.
- **Entries, grouped by meaning.** New table `unmatched_entries` (description, embedding, mark, Pattern Type folded into, Users when marked, when). No User ID on it. When a Pattern gets its general description, code embeds it and links the Pattern to the closest entry at or over a new Admin-set bar (`unmatched_grouping_closeness_percent`), or starts a new entry with that description. The entry's words are only ever a general description.
- **Count.** Users with an unmatched Pattern linked to the entry that the matching command hasn't linked to a Pattern Type. Entries with no Users left aren't listed.
- **Marks.** To review, new Pattern Type, folded (naming a Pattern Type in the catalog), dropped. Saved with the User count at that time. A dropped entry reads as "to review" again only when its count is above that number.
- **API.** `GET /api/admin/unmatched-patterns?mark=` (most Users first) and `PUT /api/admin/unmatched-patterns/{id}/mark`, Admins only.
- **Page.** `/admin/unmatched-patterns`, card-list template with the table template's filter pills: one card per entry (description, mark tag, Users), open to set the mark and the Pattern Type. New reference `AdminUnmatchedPatterns.html`, baseline, menu link.
- **Migration 0096.** Adds the column, table and link. No User data is removed.

Decisions made while building (25 Nov 2026):

- **Grouping is one at a time.** `join_or_add` finds the closest entry or adds one under a database lock, so two Conversations ending together can't start two entries for the same thing (found in review).
- **Stricter code check.** A description is also dropped for a capital letter after its first word (a person, place, company or month) or a single quote mark; the User's name only counts when written with a capital, so a User called Will or Joy doesn't lose every description (found in review).
- **The bar is 80.** Measured with the real embedder: the same way in other words 74 to 88, a different way up to 78, opposites about 91. So opposites can be lumped and a loose paraphrase listed twice. Logged in issue 20.
- **Every entry is listed from one User up**, as the issue asks. With few Users this can point at one. Logged in issue 20.
- **A dropped entry that came back** shows a "Back after a drop" tag. It is still stored as dropped, so it reads as dropped again if its count falls back.
- **Entries with no Users left** are hidden but kept, so their mark holds if they turn up again.
- **Old unmatched Patterns get a description at that User's next Conversation end.** No backfill command.
- **Menu link sits after Thought Experiments**, below the 800px cut of the sidebar, so no other baseline changed.
- **Design files.** As issues 05, 10 and 14 did: new reference `AdminUnmatchedPatterns.html` from card-list parts plus the table template's filter pills, its baseline, lines in `routes.json` and `manifest.json`, the menu link on the other 13 admin references. Logged in issue 20 for the owner.
- **Shared files touched:** migration 0096 (reloads `pattern_keeping_prompt`, so an Admin's edit to it is lost), the platform settings seed, `tests/conftest.py` (the new table is emptied between tests), `web/src/lib/dashboard-menu.ts`, `thought_experiment_api.py` (shared Pattern Type choices helper).
- **Review (standards and spec).** Fixed: the lock, a vector index on entries, the stricter check and name rule, shared Pattern Type choices, query key, fixture for the mark call, clearer names. Left, logged in issue 20: opposites grouping, one-User entries, what the code check can't catch, the dropped rule's count-only test.

Evidence (25 Nov 2026, worktree stack on 3030/8030, three made-up Users only (Tessa, Ravi, Noor) seeded with SQL; their Conversations ended by the running backend's scheduler with the real DeepSeek model through OpenRouter and the real embedder; signed-in Admin in a real browser (Playwright). The first pass ran on the first commit; after the review fixes the database was taken back to 0095, the stack rebuilt, and the checks run again):

- **Lists entries with a general description and a count, most Users first.** The real keeping step wrote for Tessa (jokes in an audit meeting and at her dad's hospital check-up) the Pattern "When a room turns serious, they reach for a joke…" with the general description "Makes jokes when things get serious.", and for Noor "Says yes to requests and later backs out." The page showed each as a card with "1 User"; after Ravi, "Makes jokes…" showed "2 Users" and came first. Looked at at 1280 and 390 (no sideways scroll, no page errors). Pixel test (git-ignored copy of `compare.cjs` blocking Clerk's protect probes): `PASS AdminUnmatchedPatterns 0.02% differs, height 816 vs 816`, `PASS AdminThoughtExperiments 0.07%`, `PASS AdminPatternCatalog 0.00%`. Platform settings shows "Unmatched grouping bar", 80, with its hint. Tests: `test_an_unmatched_pattern_is_listed_as_its_general_description_with_a_user_count`, `test_like_descriptions_from_different_users_are_one_entry_most_users_first`, `UnmatchedPatternsManager.test.tsx` (8).
- **No User detail; built only from the general wording.** The API answer as Admin held only `id`, `description`, `user_count`, `mark`, `folded_into_pattern_type_id`, `dropped_before`; `unmatched_entries` has no User column. The Users' Patterns and evidence name Priya, Anika, Deepak, a hospital and an audit; none of it was on the page or in the table. Tests: `test_an_entry_shows_only_the_general_wording_never_the_users_pattern_or_evidence`, `test_a_description_with_the_users_name_a_quote_or_a_number_is_dropped` (15 cases), `test_a_pattern_whose_description_was_dropped_is_kept_and_asked_about_again`.
- **Like descriptions from different Users are one entry.** Ravi's real description, "Deflects serious moments with jokes and silliness.", joined Tessa's entry (2 Users) at the bar of 80. After the rebuild, the three old Patterns (now with no description, as the live User's are) were each given one at the next Conversation end ("needs a general description" path), and Ravi's "Deflects with jokes or silly voices when a conversation turns serious." again joined Tessa's "Makes jokes the moment a room turns serious"; three Conversations ended in the same tick made two entries, not three. Tests: the grouping test above, `test_two_like_patterns_of_one_user_count_that_user_once`, `test_a_description_that_cant_be_embedded_is_grouped_at_the_next_conversation_end`.
- **Mark and filter.** In the browser: marked "Makes jokes…" dropped ("Saved the mark."; it left To review and showed under Dropped), marked Noor's entry "Folded into a Pattern Type" → CONF.AVOID.BELONG (Save stayed off until one was picked; shown under Folded as "Folded into CONF.AVOID.BELONG"), later marked the jokes entry New Pattern Type (shown under that pill as "To become a new Pattern Type"); All showed both. Tests: `test_an_admin_marks_an_entry_and_filters_by_the_mark`, `test_a_mark_that_makes_no_sense_is_refused`.
- **A dropped entry doesn't return unless it appears for more Users.** Dropped at 1 User. Tessa then showed the same way again (her Pattern went from 2 to 4 evidence lines): To review stayed empty ("Nothing to review"), the entry stayed under Dropped. When Ravi's Pattern joined it: it was back under To review with "Back after a drop" and "2 Users", and Dropped was empty. Tests: `test_a_dropped_entry_comes_back_only_when_it_appears_for_more_users`, `test_only_a_dropped_entry_with_more_users_reads_as_to_review_again`, `test_a_pattern_the_matching_command_linked_or_a_deleted_one_is_not_counted`.
- **Non-Admins can't reach the page or API.** Signed in as a plain User: `/admin/unmatched-patterns` landed on Home with no Admin menu; with that User's token the list answered 403 "Admins only" and the mark route 403. As Admin both answered 200. Test: `test_only_admins_can_reach_the_unmatched_entries`.
- **Migration on a database with data.** From 0095 with 3 Patterns and 9 evidence lines and an Admin-edited keeping prompt, starting the backend ran 0096: a diff of every Pattern joined to its evidence shows no row changed, the prompt is the new seed, the entries table has its vector index. Test: `test_the_migration_keeps_every_pattern_and_its_downgrade_only_drops_the_review`.
- **Checks** (rebased on main at `52a7f2b`): `make check`: ruff clean, ruff format clean (733 files), mypy clean (263 files), pytest 2226 passed (one hint-length test failed on the first full run, fixed, and its file run again); `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 140 files, 973 tests passed.
- **Not run:** Evals (they cost money; none was needed).

## Completion

- Completed: 2026-11-25
- Commit: <filled in after the merge>
