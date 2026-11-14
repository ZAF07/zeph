# 08 — Life Threads and being reminded

Status: completed

## Parent

`.scratch/understanding/PRD.md`

## What to build

The heart of the feature. "My sister's wedding is next week" can bring back a falling-out with Mei from nine months ago, and the Companion may lead with "how are things with Mei now?".

- **Written at Conversation end:** Life Threads (`CONTEXT.md`) are added to or started — title, running story with dates, people or things, open or settled — and embedded. Each Thread raised in the Conversation records when, and how the User took it (engaged / brushed off / asked to drop it). Nothing new while User Memory doesn't work for the User.
- **Being reminded, every Message, no model call:** before the Understanding, the code finds the User's Threads by a direct match on people or things named in the recent User messages, and by meaning (last 2–3 User messages joined). Open Threads first, no age limit, above an Admin-set closeness bar, up to an Admin-set number.
- **The Understanding decides:** it sees the reminded Threads with when each was last raised and the reaction, and fills `threads_touched`, `bring_up` (lead with it / weave it in) and `left_alone` (with a reason). The reply gets what to bring up and how, and what to leave alone. A Thread raised in this Conversation isn't raised again; brushed off waits an Admin-set time; asked to drop it is never raised unless the User brings it up.
- A Thread in `bring_up` is marked raised when the reply is sent.
- Admins see a count of each User's Threads. Delete My Data and Account Deletion remove them.

## Acceptance criteria

- [x] Conversation end creates and updates Threads (scripted output), including open/settled and reactions to bring-ups
- [x] Reminded by name: a Message naming someone in a Thread brings it to the Understanding, however old
- [x] Reminded by meaning: a Message close to a Thread's story brings it; a weak match doesn't
- [x] Open Threads rank above settled ones
- [x] A Thread raised earlier in the Conversation, one brushed off too recently, and one asked to drop are not offered for bring-up (or are marked so the Understanding leaves them)
- [x] User Memory off: no new or updated Threads; saved ones still used
- [x] Closeness bar, number and brushed-off wait are Admin settings
- [x] Delete My Data and Account Deletion remove Threads (per-User table test)
- [x] Tests at the webhook seam with scripted chat model, fake embedder and fake clock; checks pass
- [x] `/run`: after a Conversation about a falling-out with a sister ends (timestamps shifted back), "my sister's wedding is next week" leads to the reply raising it

## Blocked by

- `.scratch/understanding/issues/04-understanding-call-with-seeded-needs.md`

## Comments

- Branch `understanding-08-life-threads`, worktree `ai-chat-companion-understanding-08` (ports 3220/8220/5652).
- Plan:
  - New `life_threads` table (migration 0030): title, story, people or things (plus lower-case name keys for matching), open or settled, last raised at and in which Conversation, last reaction, embedding.
  - Being reminded: one SQL query per Message finds the User's Threads whose people or things appear in the last 3 User texts, or whose story is close in meaning to them (above the bar). Open first, then name matches, then closest; up to the Admin number.
  - The Understanding sees the Threads numbered, with when each was last raised, the reaction, and a "don't bring it up" note when held back. The code also drops any bring-up of a held-back Thread.
  - The reply gets the stories that matter, what to bring up and how, and what to leave alone. Brought-up Threads are marked raised after the reply is sent.
  - Conversation end: a separate "Life Thread keeping" model call (own Admin prompt and model) adds and updates Threads and records reactions; skipped while User Memory doesn't work.
  - Settings: `life_threads_per_reply`, `life_threads_closeness_percent`, `life_thread_brushed_off_wait_days`. Admin Users page shows a Life Threads count.
- Decisions:
  - Name matching is done in Postgres with array overlap on `name_keys` (GIN index). The core turns each person or thing into lower-case keys (`name_keys`, which splits "Mei (sister)" into "mei" and "sister") and the User's last 3 texts into every run of 1–3 words (`name_phrases`). So "my sister's wedding" finds a Thread naming "sister". One query per Message does both name and meaning, open first, then named, then closest.
  - A name match counts whatever its closeness; only meaning matches face the closeness bar. The seed bar is 62, not 68 like older Summaries: with the real bge-small embedder, short messages about a Thread scored 65–71 against its story and unrelated ones up to about 55 (59 for "tired of work" vs a job-hunt story). "my sister's wedding is next week" scored only 58 against the falling-out story, so names do that work.
  - Brushed-off wait is `life_thread_brushed_off_wait_days` (seed 14, 1–365). Number is `life_threads_per_reply` (seed 3, 0–10). All three are on Settings → Memory.
  - Life Thread keeping is its own model call (step `life_threads` in the Model Call Log, prompt and model on Prompts and Models), run after the Conversation is marked processed. It sees the Threads the whole Conversation reminds the Companion of (up to 10) plus those brought up in it. If it fails, that is logged and it isn't retried, so no Thread is ever added twice. An unreadable answer is asked again once.
  - Threads are referred to by number in the Understanding form; saved forms keep each brought-up or left-alone Thread's ID and title. `threads_touched` is saved as titles.
  - Brought-up Threads are marked raised even while User Memory is off, so the Companion doesn't raise one twice in a Conversation. That only changes when it was raised, never the story. The last reaction stays until a Conversation end records a new one, so a brushed-off Thread raised again while User Memory is off still waits (review finding, fixed).
  - Migration 0030 deletes the stored `understanding_prompt` so the seed version that explains Threads loads on the next start (platform not live).
  - Being reminded adds one messages read and one embedding per Message.

## Evidence

- **Conversation end creates and updates Threads, open/settled and reactions:** `tests/test_life_threads.py::test_a_conversation_end_starts_a_thread_and_naming_someone_in_it_brings_it_back` (a Thread is started), `test_conversation_end_updates_a_thread_and_shows_the_keeper_what_was_raised` (story changed, open → settled, reaction "engaged"; the keeper is shown the Thread marked "Brought up in this Conversation."), and the brushed-off and asked-to-drop tests (reactions recorded). A failing keeper still saves the Summary and isn't retried: `test_a_failing_thread_keeper_still_saves_the_summary_and_is_not_retried`.
- **Reminded by name, however old:** `test_a_conversation_end_starts_a_thread_and_naming_someone_in_it_brings_it_back` (270 days later, "Mei's wedding is next week!"); `test_a_person_written_with_a_note_in_brackets_is_found_by_either_word`; still found by name when embedding fails: `test_threads_are_still_found_by_name_when_embedding_fails`. Only the User's own Threads: `test_only_the_users_own_threads_are_found` (a mutation check confirmed it bites: with the `user_id` filter removed it fails).
- **Reminded by meaning; a weak match doesn't:** `test_a_message_close_in_meaning_to_a_story_brings_it_and_a_weak_match_does_not`.
- **Open above settled:** `test_open_threads_come_before_settled_ones_up_to_the_admin_set_number` (`[1] … (open`, `[2] … (settled`).
- **Held back:** `test_a_thread_raised_earlier_in_the_conversation_is_not_raised_again`, `test_a_brushed_off_thread_waits_the_admin_set_time_before_it_can_come_back`, `test_a_thread_they_asked_to_drop_is_never_offered_again` — each marked "Don't bring it up: …" for the Understanding, and a bring-up the model still picks is turned into "leave alone" in the reply. `test_raising_a_brushed_off_thread_again_with_user_memory_off_keeps_the_wait` (review finding). The reply gets what to bring up and how, and leave-alone without the story: `test_a_thread_brought_up_reaches_the_reply_with_how_and_its_story`, `test_a_thread_left_alone_reaches_the_reply_without_its_story`. A failed Understanding still gives the reply the Threads not held back: `test_a_failed_understanding_still_gives_the_reply_the_threads_not_held_back`.
- **User Memory off:** `test_with_user_memory_off_no_thread_is_kept_but_saved_ones_are_still_used` (no keeping call, no new Thread, the saved one still reminded).
- **Admin settings:** number (`test_open_threads_…_up_to_the_admin_set_number`), closeness bar (`test_the_admin_sets_how_close_a_story_must_be`), brushed-off wait (`test_a_brushed_off_thread_waits_the_admin_set_time…`, set to 30 days), all via `PATCH /api/admin/settings`. Dashboard: `web/src/components/PlatformSettingsForm.test.tsx` "shows and saves the Life Thread number, closeness bar and wait". Admin Life Thread count: `test_admins_see_how_many_life_threads_each_user_has` (count only, no story) and `web/src/components/AdminUsers.test.tsx`.
- **Delete My Data and Account Deletion:** `tests/test_data_deletion.py` per-User table tests; the setup now makes a Life Thread, so `life_threads` is one of the tables that must hold data before and none after (`test_delete_my_data_removes_every_kind_of_data_but_keeps_the_account`, `test_delete_account_removes_the_user_and_their_auth_account`).
- **Checks (`make check`):** `pytest` 828 passed, 9 deselected; `ruff check`, `ruff format --check`, `mypy` clean; `pnpm lint`, `format:check`, `typecheck` clean; `pnpm test` 355 passed.
- **/run in the worktree:** the real app ran in a one-off backend container with the real database, DeepSeek and the fastembed embedder; only the chat channel was a recorder, and the clock was moved back 270 days for the first Conversation (worktree Telegram can't send to a fake chat).
  - Conversation 1 (dated 17 Feb 2026): "my sister Mei and I had a massive fight today", "it's about money for mum's care home…", "we're not really speaking now…". At its end the real keeper started one Thread: "Fight with sister Mei over mum's care home money", people `Mei, sister, mum`, open, embedded.
  - Conversation 2 (today): "my sister's wedding is next week" reminded the Understanding of it by name ("sister"); the Understanding put it in `bring_up` with "lead"; the reply was told "Bring up… : lead with it." and Zeph said: "I'm thinking about the last time we talked — the fight over your mum's care home money, and the silence since. So the wedding isn't just a wedding. It's the first time you'll be in a room together." The Thread's `last_raised_at` was set.
  - The next message ("we still haven't properly talked. I'm dreading it") left it alone ("already brought it up in this Conversation"). At Conversation end the same Thread (no duplicate) gained the wedding in its story, and `last_reaction` became `engaged`.
  - The first run found two real problems, both fixed before the final run: the keeper wrote "Mei (sister)" as one name (now split into keys, and the prompt asks for each name on its own), and the seed closeness bar of 68 was above real scores (now 62; see decisions).
- **/code-review:**
  - Standards: no hard violations. Fixed: the duplicated embed-and-search code is now one helper, `read_form` renamed `model_form`, right-aligned admin columns come from one set. Kept: `life_threads.py` holds reminding and keeping together (one domain term, used together); the keeper's raw model entries are read field by field, as the other conversation-end readers do.
  - Spec: fixed the lost brushed-off wait (raising a Thread no longer clears its reaction) and the misplaced Personal Stickers seed comment. Kept, as recorded decisions: name matches skip the closeness bar; the Understanding prompt reload in migration 0030; `threads_touched` saved as titles.

## Completion

- Completed: 2026-11-14
- Commits: `5619848` (Life Threads and being reminded), `3ec3da5` (review fixes: keep the last reaction when a Thread is raised, one shared Thread search, seed comment)
