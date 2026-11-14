# 06 — Older Conversation Summaries found by meaning

Status: completed

## Parent

`.scratch/understanding/PRD.md`

## What to build

"How did that job interview go?" works however long ago it was. Every Conversation Summary is embedded when written. When the Understanding's `look_up_past` has phrases, they are searched against the User's own Summaries; matches above an Admin-set closeness bar, up to an Admin-set number, go into the reply with their dates (beyond the newest few that always go in). An empty `look_up_past` searches nothing.

## Acceptance criteria

- [x] New Summaries are embedded when written
- [x] A `look_up_past` phrase brings a matching old Summary into the reply call; a weak match adds nothing
- [x] Only the User's own Summaries are searched
- [x] Closeness bar and number are Admin settings
- [x] Deleting a Summary (or Delete My Data / Account Deletion) removes its embedding
- [x] Tests at the webhook seam with the fake embedder; checks pass
- [x] `/run`: a fact from an old Summary (timestamps shifted back) comes up when asked about

## Blocked by

- `.scratch/understanding/issues/04-understanding-call-with-seeded-needs.md`

## Comments

- Branch `understanding-06-older-summaries`, worktree `ai-chat-companion-understanding-06` (ports 3200/8200/5632).
- Decisions:
  - The embedding is a nullable column on `conversation_summaries` (migration 0029), so deleting a Summary row (one at a time, Delete My Data, Account Deletion) removes its embedding with it. Summaries written before this change have none and are only seen as one of the newest few (platform not live, so no backfill).
  - The closeness bar is a whole-number percent of cosine similarity (`older_summaries_closeness_percent`, seed 68), so it fits the existing whole-number fields on the admin Settings page. With the real bge-small embedder, real matches scored 0.70–0.81 and unrelated ones up to 0.64. The number is `older_summaries_per_reply` (seed 3, 0–10). Both are on Settings → Memory.
  - All `look_up_past` phrases are searched in one query. A Summary counts if it is close enough to any phrase, and results are ordered closest first. The newest Summaries already in the reply are left out.
  - A failed embedding when a Summary is written still saves the Summary. A failed search leaves older Summaries out and the reply still goes. Both are logged.
  - Migration 0029 also deletes the stored `understanding_prompt`, so the seed version that explains `look_up_past` loads on the next start. This discards Admin edits to that prompt, which is fine because the platform isn't live yet.
  - Older Summaries go into the reply's memory section as "Older Conversations that may matter:", each with its date and mood, after "Recent Conversations".

## Evidence

- **New Summaries are embedded when written:** `tests/test_older_summaries.py::test_new_summaries_are_embedded_when_written`. If embedding fails, the Summary is still saved: `test_a_summary_is_still_saved_when_embedding_it_fails`.
- **A `look_up_past` phrase brings in a matching old Summary, and a weak match adds nothing:** `test_a_look_up_past_phrase_brings_an_old_summary_into_the_reply_with_its_date` (the 4th-newest Summary arrives with its date, and the newest ones are not repeated) and `test_a_weak_match_adds_nothing`. An empty `look_up_past` searches nothing: `test_an_empty_look_up_past_searches_nothing`.
- **Only the User's own Summaries are searched:** `test_only_the_users_own_summaries_are_searched`, where another User's Summary would otherwise match. A mutation check confirmed the test bites: with the `user_id` filter removed, this test fails.
- **Closeness bar and number are Admin settings:** `test_the_admin_sets_how_many_older_summaries_go_in_and_how_close_they_must_be` (set through `PATCH /api/admin/settings`). On the Dashboard: `web/src/components/PlatformSettingsForm.test.tsx` "shows and saves the older Conversation limit and closeness bar".
- **Deleting removes the embedding:** `test_a_deleted_summary_is_no_longer_found` (deleted through the Dashboard API, and the row with its embedding is gone). Delete My Data and Account Deletion delete the whole rows, which the existing `tests/test_data_deletion.py` checks.
- **Checks:** `pytest` 799 passed, 9 deselected; `ruff check`, `ruff format --check` and `mypy src` are clean. `pnpm lint`, `format:check` and `typecheck` are clean; `pnpm test` 344 passed.
- **/run in the worktree:** a Telegram send from a fake chat fails in a worktree. So the real app ran in a one-off backend container with the real database, DeepSeek and the fastembed embedder, with only the chat channel swapped for a recorder.
  - An Admin had four Conversations, each processed by the real post-conversation step, and all four Summaries were saved with `embedded=True`.
  - The Summaries' dates were moved back to 15 Sep, 30 Sep, 15 Oct and 30 Oct. The interview one, "They had a job interview at Northwind for a senior product designer role… second-guessing the 140k salary figure…", was the oldest, so it was outside the newest 3.
  - Asked "do you remember what salary number I gave in that job interview a while back?":
    - the Understanding gave `look_up_past: ['job interview salary expectations', 'senior product designer interview salary 140k']`;
    - the reply's instructions (the Admin's full-content trace) held "Older Conversations that may matter:\n- 15 Sep 2026: They had a job interview at Northwind…";
    - Zeph answered "I remember you mentioned 140k — that was the figure you gave when they pressed you on it at the Northwind interview."
  - Asked "did I ever tell you about my trip to Japan?": `look_up_past: ['trip to Japan']` added nothing, and Zeph said "I don't think you have — nothing about Japan in what I remember."
- **/code-review:**
  - Standards: no hard violations. Fixed: the unused defaults for `look_up_past` and `leave_out` are now required.
  - Kept as they are: the embedding passed beside the Summary rather than on it (it's a storage detail), and the separate embed-and-log blocks (each logs its own message).
  - Spec: nothing missing. The Understanding prompt reload is deliberate (see the decisions above).
