# 16 — Existing Patterns move across, and free noticing becomes unmatched Patterns

Status: completed
Track: B
Blocked by: 12

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 28, 57, 86). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Production has a real User with Patterns kept under the old rules. A migration keeps every one: confirmed stay confirmed and visible, suspected become unmatched (they were hidden anyway), closed stay closed. A one-off pass, run by an Admin command, matches each to a Pattern Type where one fits.

The Pattern keeping step changes job: it no longer starts, confirms or closes catalog Patterns (code does, from Observations). It only notes what recurs across two or more Life Threads and fits no Pattern Type, as an unmatched Pattern with its evidence. Unmatched Patterns are never ready or shared and stay hidden, but still come to mind and the Read may think with them, as today. When a Pattern Type is added, an Admin command tags stored unmatched evidence again against it.

## Acceptance criteria

- [x] After the migration every existing Pattern and its evidence is still there; confirmed ones still show on the Dashboard exactly as before
- [x] Existing suspected Patterns are unmatched and hidden; closed ones stay closed
- [x] The matching pass links a Pattern to a Pattern Type only where it fits, and reports what it did
- [x] The keeping step writes only unmatched Patterns; it can't change a catalog Pattern's state
- [x] An unmatched Pattern still comes to mind and can shape the Read, and is never offered as a Pattern
- [x] Tagging again against a new Pattern Type turns matching unmatched evidence into Observations, checked like any other
- [x] The migration is tested against a database holding old-style Patterns
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `12-patterns-scored-and-moved-by-code.md`

## Comments

Plan (24 Nov 2026, branch `pattern-16-existing-patterns-move`, worktree `ai-chat-companion-pattern-16`):

- **Unmatched is a state of a written Pattern.** `PatternState` gains `unmatched`, used only by Patterns with no Pattern Type (the ones the keeping step writes). It is not one of the seven states code moves a catalog Pattern between.
- **Migration (0092).** Every old suspected Pattern becomes unmatched; confirmed and closed are left as they are; no row or evidence is removed. `patterns` gains `matched_pattern_type_id`. `pattern_keeping_prompt` is reloaded from the seed.
- **Keeping step.** Starts only unmatched Patterns (two or more Threads, as before) and adds evidence only to unmatched ones. It no longer reads reactions, confirms or closes. It is shown the Pattern Types so it leaves those to tagging. It never sees a catalog Pattern.
- **In replies.** An unmatched Pattern still comes to mind and the Reply Plan may build its Read on it, but code drops any try to offer it: only a confirmed Pattern can be offered.
- **Matching (Admin command).** `python -m companion.pattern_matching_terminal` (`make match-patterns`, `TYPES=ID,ID` for only some Pattern Types). For each written Pattern not matched yet, one model call says which Pattern Type it fits, or none; code keeps the answer only when the ID is in the catalog. A match is a link (`matched_pattern_type_id`); the Pattern, its words, state and evidence stay as they are. Then the Conversations behind its evidence whose messages are still kept are tagged again against that Pattern Type with the normal checks, and the User's Patterns are scored again (cause `evidence_tagged_again`). Closed ones are linked but not tagged again. Only for Users for whom Pattern noticing works and who pressed "Got it". The same command with `TYPES=` is the "tag again when a Pattern Type is added" step. It prints counts and IDs, never a User's words.
- **Admins** see an "Unmatched Patterns" count per User.

Decisions made while building (24 to 25 Nov 2026):

- **A match is a link, not a change.** Making the old Pattern itself the Pattern of the Pattern Type was dropped: it has no Observations, so scoring would delete or close it. The link is saved only after its evidence was tagged again, so a failed run is done again by the next (found in review). Recorded in ADR-0024.
- **One command for both jobs.** `make match-patterns` is the one-off pass; `make match-patterns TYPES=ID` is "tag again when a Pattern Type is added". A model call first says whether the Pattern fits, so Conversations are only tagged again where it does.
- **Keeping is shown the Pattern Types only for a User tagging runs for** (Pattern noticing works and they pressed "Got it"). For everyone else it is shown none, so what recurs is still kept as an unmatched Pattern instead of nowhere (found in review; this is the live User today).
- **Offering.** Code drops a Reply Plan's `offer_pattern` unless the Pattern is confirmed. Keeping no longer reads reactions at all.
- **Skipped Users.** Users without Pattern noticing, or not told yet, are not matched at all; the command says so and is run again later.
- **The command builds its own matcher** (`build_pattern_matcher`), like the Eval command, instead of reading it off the app (found in review). It exits 1 when a User's run failed and 2 for an unknown Pattern Type.
- **Migration is 0092** (main's 0091 landed first). It reloads `pattern_keeping_prompt`, so an Admin's edit to it is lost.
- **Shared files touched:** `Makefile` (new `match-patterns` target), the platform settings seed, `tests/fakes.py` and `tests/conftest.py` (scripted matching answers).

Evidence (25 Nov 2026, worktree stack on 3030/8030, one made-up User only, real DeepSeek model through OpenRouter; build `c53cd94` before the rebase, where the migration was still numbered 0091):

- **Every Pattern and its evidence still there; confirmed ones show exactly as before.** The database held 6 Patterns: a confirmed and a closed written one (2 evidence lines each), an unmatched one the real keeping step wrote, and two of Pattern Types. Taken back to revision 0090 (`alembic downgrade`), the table had no `matched_pattern_type_id` and the written ones read `confirmed`, `closed`, `suspected`; a raw old `suspected` row with 2 evidence lines and an Admin-edited keeping prompt were added by SQL. Starting the backend ran the migration. A `diff` of every Pattern joined to its evidence (ID, words, Pattern Type, agreed day, reaction, evidence day, line, Thread) before and after: no row differs. The Memories page's Patterns tab showed the confirmed Pattern, "You agreed with this on 19 Nov" and its two lines, the same before and after (screenshots looked at). Tests: `test_the_migration_keeps_every_old_pattern_and_makes_suspected_ones_unmatched`.
- **Suspected are unmatched and hidden; closed stay closed.** After the migration both old `suspected` rows read `unmatched`, the closed one `closed`, the confirmed one `confirmed`; the suspected Pattern of a Pattern Type stayed `suspected`. The Patterns tab showed only the confirmed one. Admin Users panel: "Confirmed Patterns 1, Noticed 1, Suspected 1, Closed 1, Unmatched Patterns 2", no Pattern words on the page. The keeping prompt was the new seed again. Tests: the migration test; `test_a_user_sees_only_confirmed_patterns_newest_agreed_first_with_evidence` in `tests/test_patterns_dashboard.py`.
- **Matching links only where it fits, and reports.** `make match-patterns TYPES=CTRL.UNCERT.PLAN`: "4 Patterns looked at, 0 matched", each "fits no Pattern Type". `TYPES=NOT.A.TYPE`: "No Pattern Type NOT.A.TYPE in the Pattern Catalog", exit 2. `make match-patterns` (whole catalog): the confirmed "Treats rest as something to be earned…" linked to ACH.WORTH.PERF, the other three "fits no Pattern Type"; its evidence days had no Conversation, reported as "1 evidence days with no messages left". Run again: the two linked Patterns were not asked about. Every Pattern kept its words, state and evidence. The Prompts & models page lists "Pattern matching · Only when an Admin runs the matching command". Tests: `tests/test_pattern_matching.py` (28 tests).
- **Keeping writes only unmatched Patterns; can't change a catalog Pattern.** A seeded Conversation (jokes in a work meeting and at dad's hospital check-up; a Saturday lost to a bike) ended by the quiet gap; the scheduler ran the real chain. Tagging and code made APPR.HIDE.BURDEN `suspected` and ACH.ABSORB.PULL `noticed`; the keeping step wrote one Pattern, `unmatched`: "When things get serious or heavy, they reach for jokes and make light of the moment", with a line from each of two Threads. At a second Conversation end the keeping call was given the Pattern Types (names, no IDs) and the five written Patterns only; it added one evidence line to the unmatched jokes Pattern (2 → 3); the confirmed, closed and catalog Patterns and the move log were unchanged. Tests: `test_the_keeping_step_cant_change_a_pattern_of_a_pattern_type`, `test_keeping_never_confirms_or_closes_a_pattern_whatever_the_model_writes`, `test_keeping_adds_nothing_to_a_confirmed_or_closed_pattern`.
- **Unmatched comes to mind, shapes the Read, never offered.** The real reply path run in a backend container on the real database with only the chat channel swapped for a recording one (a fake Telegram chat can't be sent to). Text: "Priya just moved the audit deadline up… I spent the whole standup doing a comedy bit about it. What do you think is going on with me?" The Reply Plan was given four Patterns in mind under "An unmatched one is only your guess: your Read may think with it, but never offer it or say it as a pattern", three marked `(unmatched)`. Its form: `patterns_used` = the jokes Pattern, `pattern_offered` = null, Read said; shape `pattern_used: true, pattern_offered: false`. Reply sent: "This is the third time now — the hospital, the meeting, standup. The comedy bit isn't you not caring…". Tests: `test_an_unmatched_pattern_shapes_the_read_but_is_never_offered`, `test_an_offered_pattern_reaches_the_reply_as_zephs_view` (confirmed only).
- **Tagging again against a new Pattern Type makes Observations, checked like any other.** ACH.ABSORB.PULL's Observation and Pattern were deleted (as if the Pattern Type were new) and an unmatched "When something grabs them, everything else goes quiet…" was seeded with evidence on the Conversation's day. `make match-patterns TYPES=ACH.ABSORB.PULL`: "5 Patterns looked at, 1 matched, 1 Conversations tagged again, 1 Observations kept". Kept: sign I2, for, quote "once I started rebuilding my old bike on Saturday I forgot to eat, skipped lunch and dinner, and missed drinks with Sam without even noticing the time" (word for word in the User's text), day 24 Nov, Thread "Rebuilding old bike". Scoring noticed ACH.ABSORB.PULL again, logged with cause `evidence_tagged_again`. The Model Call Log has the run under trace kind `pattern_matching`, the tagging call with shape `tagged 1, dropped 0`. Tests: `test_matched_evidence_is_tagged_again_into_observations_checked_like_any_other` (two entries dropped by the checks), `test_a_conversation_tagged_again_twice_keeps_each_quote_once`, `test_evidence_whose_messages_message_retention_deleted_is_not_tagged`.
- **Migration tested against old-style Patterns.** `tests/test_unmatched_patterns_migration.py` takes the database back before the migration, checks the rows read `suspected`, `confirmed`, `closed`, inserts a raw old `suspected` row with evidence, migrates, and checks every Pattern, its evidence, the Dashboard answer and the reloaded prompt.
- **Review.** Standards and spec reviews run. Fixed: link saved only after tagging; keeping no longer hides Pattern Types' ground from Users with no tagging; own matcher builder instead of app state; report text moved out of the core; days with no messages reported; exit 1 on a failed User; simpler offer check; raw old row in the migration test. Left, logged in issue 20: a push-back on a confirmed old Pattern is no longer recorded; a Pattern keeps its first match; old evidence past Message Retention can't become Observations; an unreadable matching answer reads as "fits no Pattern Type".
- **Not run:** the pixel test. No component or reference changed; the Prompts & models page only gains one more core service row from data.
- **Checks** (after rebasing on main, migration renumbered 0092): `make check`: ruff clean, ruff format clean (711 files), mypy clean (253 files), pytest 2093 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 137 files, 953 tests passed.

## Completion

- Completed: 2026-11-25
- Commit: 35e3503 (merge "Merge pattern-16-existing-patterns-move: old Patterns move across (suspected become unmatched), Pattern keeping only notes unmatched Patterns, and an Admin matching command links Patterns to Pattern Types and tags their evidence again"; work in 0cff435 "Pattern pipeline 16: old Patterns move across (suspected become unmatched), Pattern keeping only notes unmatched Patterns, and an Admin matching command links Patterns to Pattern Types and tags their evidence again", 36b15a3 "Pattern pipeline 16: review fixes (a match is saved only after its evidence is tagged, keeping sees the Pattern Types only while tagging runs for the User, the command builds its own matcher, reports days with no messages left and exits 1 on a failed User)", 8139e45 "Issue 16 done: migration is 0092 after main's 0091, evidence, issue archived, findings for the owner in issue 20")
