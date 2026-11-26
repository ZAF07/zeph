# 35 — A quote the User deleted is kept again when its day is tagged again

Status: completed
Track: shared
Blocked by: none

## Parent

Found while checking question 5 of `30-owner-decisions-before-pattern-sharing-is-on.md` (20 → 13).

## Symptom

A User deletes a quote on "Things you said that Zeph kept". An Admin later runs `make match-patterns`, which tags old Conversations again. The deleted quote is kept again as an Observation and counts toward a Pattern. Expected: a quote the User deleted is never kept again. The same holds for quotes removed by deleting a Pattern or a Life Thread.

Nothing remembers that the quote was deleted: `PatternTagger.tag_again` (`core/observations.py`) only skips quotes that are still kept.

## Repro

Deterministic. `tests/test_pattern_matching.py::test_a_quote_the_user_deleted_is_not_kept_again_when_its_day_is_tagged_again`: match a Pattern (keeps "I forgot to eat"), delete that quote through `DELETE /api/kept-quotes/{id}`, match a second Pattern with evidence on the same day. Result before the fix: `observations_kept == 1`, expected 0.

## Fix

Keep a small record per deleted quote: the User, the Conversation, a hash of the message it was in and where in it the quote sat (never the words). The tagging checks drop an Observation whose quote shares any words with one on that record, so a longer or shorter cut doesn't come back either ("Dropped by code"). Written when a User deletes a kept quote, a Pattern they were told, or a Life Thread. Removed by Delete My Data and Account Deletion.

## Acceptance criteria

- [x] The bug no longer reproduces: the test above passes
- [x] Quotes removed by deleting a Pattern or a Life Thread don't come back either, with tests
- [x] The record holds none of the User's words, and goes with Delete My Data and Account Deletion
- [x] `ruff`, `ruff format`, `mypy` and `pytest` pass
- [x] Checked in the running app

## Comments

### 25 Nov 2026: fixed

**Confirmed cause.** Nothing remembered that a quote was deleted: `PatternTagger.tag_again` only skipped quotes still kept, so `make match-patterns` kept a deleted quote again.

**Fix.** `deleted_quotes` (migration 0105) keeps, per deleted quote, the User, the Conversation, a hash of the message it was in and where in it the quote sat. `check_observation` drops any quote that shares words with one on record (`DropReason.DELETED_BY_USER`). Written by `UserMemoryService` when a kept quote, a told Pattern or a Life Thread is deleted. The first version hashed the quote itself; the review showed a longer or shorter cut of the same words would slip through, so it now matches by position. Life Thread deletion now locks the User like the other two.

**Checks.** ruff clean, ruff format clean, mypy clean (286 files), pytest 2584 passed; web: eslint, prettier and tsc clean, Vitest 989 passed (141 files).

**How it was checked in the running app.** On this worktree's stack (fresh database, migrated to 0109, seeds loaded). Dashboard pages were driven in a real browser as a signed-in Admin and User. The chat path was run by the real core services on the stack's database with only the chat model scripted, the chat channel recording, and the clock and scheduler moved by hand (a worktree can't reach Telegram), acting as the signed-in User so the browser showed the result. Not checked: the migrations on a copy of the main database (the main stack wasn't running); the tests cover them by downgrading and migrating again.

**Evidence per criterion**

- **The bug no longer reproduces.** `test_a_quote_the_user_deleted_is_not_kept_again_when_its_day_is_tagged_again` was red (1 kept) and is green, now also with a longer cut of the same words. Running app: as the User, pressed "Delete quote: With Sam I say what I think" on Things you said (4 quotes → 3); `deleted_quotes` held one row (hash, span 61 to 88, no words); `tag_again` on that Conversation with its whole text as the quote kept nothing (Observations 3 before, 3 after).
- **Quotes removed with a Pattern or a Life Thread don't come back.** `test_a_quote_that_went_with_a_deleted_life_thread_is_not_kept_again` (re-tags the day), and the record counts in `test_deleting_a_pattern_removes_it…` and the Life Thread test. Running app: deleting the told Pattern in the browser left 5 records.
- **No words kept; goes with Delete My Data and Account Deletion.** `test_a_quote_the_user_deleted_is_dropped_in_longer_or_shorter_words_too`; `test_delete_my_data_removes_every_kind_of_data_but_keeps_the_account` now needs a row in `deleted_quotes` and finds none after.
- **Checks pass; checked in the running app.** Above.

## Completion

- Completed: 2026-11-25
- Commit: efe99ea5 ("Merge pattern-30-owner-decisions-before-sharing: the owner's decisions before Pattern sharing is on", the merge of pattern-30-owner-decisions-before-sharing into main; work commits b4fdc35d, 351f74c8, ec11f7a8, e21f096b, f9225f60, 7522ee99, 45d716a0, cc0fd499, ff840919, 875f3175, 88bc0a4a)
