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
