# 08 — Life Threads and being reminded

Status: ready-for-agent

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
