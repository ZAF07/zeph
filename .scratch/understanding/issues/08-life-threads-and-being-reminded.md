# 08 — Life Threads and being reminded

Status: in-progress

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

- [ ] Conversation end creates and updates Threads (scripted output), including open/settled and reactions to bring-ups
- [ ] Reminded by name: a Message naming someone in a Thread brings it to the Understanding, however old
- [ ] Reminded by meaning: a Message close to a Thread's story brings it; a weak match doesn't
- [ ] Open Threads rank above settled ones
- [ ] A Thread raised earlier in the Conversation, one brushed off too recently, and one asked to drop are not offered for bring-up (or are marked so the Understanding leaves them)
- [ ] User Memory off: no new or updated Threads; saved ones still used
- [ ] Closeness bar, number and brushed-off wait are Admin settings
- [ ] Delete My Data and Account Deletion remove Threads (per-User table test)
- [ ] Tests at the webhook seam with scripted chat model, fake embedder and fake clock; checks pass
- [ ] `/run`: after a Conversation about a falling-out with a sister ends (timestamps shifted back), "my sister's wedding is next week" leads to the reply raising it

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
