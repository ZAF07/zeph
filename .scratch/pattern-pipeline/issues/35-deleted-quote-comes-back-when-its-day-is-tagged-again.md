# 35 — A quote the User deleted is kept again when its day is tagged again

Status: ready-for-agent
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

- [ ] The bug no longer reproduces: the test above passes
- [ ] Quotes removed by deleting a Pattern or a Life Thread don't come back either, with tests
- [ ] The record holds none of the User's words, and goes with Delete My Data and Account Deletion
- [ ] `ruff`, `ruff format`, `mypy` and `pytest` pass
- [ ] Checked in the running app

## Comments
