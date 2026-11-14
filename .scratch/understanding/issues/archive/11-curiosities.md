# 11 — Curiosities

Status: completed

## Parent

`.scratch/understanding/PRD.md`

## What to build

The Companion has things it's been meaning to ask (`CONTEXT.md` "Curiosity").

- **New Feature "Curiosities"** (for everyone and per User, like Personal Stickers). When it doesn't work for a User, none are made or raised; none are deleted.
- **Written at Conversation end:** what to ask and why, a "not before" day or anytime, sensitivity, and the Memory Item or Thread it came from. Raised ones get how the User took them; ones no longer relevant are closed. The "waiting at once" limit drops the oldest. Not while User Memory doesn't work for the User; waiting ones are still used.
- **Raised in Conversations:** the Understanding sees waiting Curiosities whose day has come, with how many were already raised in this Conversation, and may put one in `bring_up` (open with it, weave it in) or leave it for a better moment. At most the Admin-set number per Conversation (start 1). Marked raised when the reply is sent.
- **Internal:** not shown to Users, not in User Memory. Deleting the source Memory Item or Thread removes its Curiosities. Delete My Data and Account Deletion remove them.
- Settings: raised per Conversation, waiting at once. (Curiosity Check-ins per week comes with issue 12.)

## Acceptance criteria

- [x] Conversation end creates, updates and closes Curiosities (scripted output), honouring the waiting limit
- [x] A Curiosity is offered to the Understanding only once its day has come, and not after the per-Conversation limit is reached
- [x] Raised Curiosities record the reaction at the next Conversation end
- [x] Deleting the source Memory Item or Thread removes its Curiosities
- [x] Feature off (for everyone or one User): none made or raised
- [x] User Memory off: none made; waiting ones still offered
- [x] No Dashboard or User API exposes them; Delete My Data and Account Deletion remove them
- [x] Checks pass
- [x] `/run`: "big presentation Thursday" in one Conversation; after it ends and Thursday passes (timestamps shifted), the next Conversation raises it

## Blocked by

- `.scratch/understanding/issues/08-life-threads-and-being-reminded.md`

## Comments

- Branch `understanding-11-curiosities`, worktree `ai-chat-companion-understanding-11` (ports 3210/8210/5642).
- Plan:
  - New `curiosities` table (migration 0033, after the User Portrait's 0032): what to ask, why, not-before day (or none), sensitivity (low / medium / high), state (waiting / raised / closed), reaction, source Memory Item or Life Thread, raised at and in which Conversation. The source columns are foreign keys with `ON DELETE CASCADE`, so every way a Memory Item or Thread is deleted (Dashboard, "forget that" in chat, a memory processing "remove") takes its Curiosities with it.
  - New Feature **Curiosities** (on for everyone at the start, like the other non-plan Features; not in the reply's "unavailable" note, since Users don't know about it).
  - Conversation end: a separate "Curiosity keeping" model call (own Admin prompt and model, step `curiosities` in the Model Call Log), run after Life Thread keeping, only while User Memory and Curiosities work. It sees today's date, the User's Memory Items and the Threads the Conversation touches (to name a source), the waiting Curiosities and those raised in this Conversation, recently raised ones (so it doesn't ask again), and the Conversation. It adds new ones, edits or closes waiting ones, and records how the User took raised ones. Over the waiting limit, the oldest waiting ones are closed.
  - Reply: before the Understanding, the code lists waiting Curiosities whose day has come (in the User's time zone), with how many were raised in this Conversation and the limit; none once the limit is reached or when the Feature is off. The Understanding may put one in `bring_up` as `{"curiosity": n, "how": ...}`; the code caps it at what's left of the limit. The reply gets the question, why, and how to bring it up. It is marked raised after the reply is sent.
  - Settings: `curiosities_per_conversation` (1), `curiosities_waiting_limit` (10) on Settings; prompt and model on Prompts and Models.
  - Delete My Data and Account Deletion delete them; no Dashboard or User API returns them.
- Decisions:
  - Curiosities is on for everyone to start (it isn't a plan extra yet), and not in the reply's "Features unavailable" note, since Users don't know about it.
  - Curiosity keeping is its own model call (step `curiosities`), run after Life Thread keeping so it can name a new Memory Item or Thread as the source. It sees the Memory Items, the Threads the Conversation touches (up to 10, plus those raised in it), the waiting Curiosities and those raised in this Conversation (one numbered list), and the last 10 raised in earlier Conversations with reactions ("asked recently, don't ask again"). A failure is logged and not retried; an unreadable answer is asked again once.
  - Sources are foreign keys with `ON DELETE CASCADE`, so every delete path counts (Dashboard, "forget that" in chat, a Conversation-end "remove", redoing onboarding). New ones whose source was deleted while the model ran aren't added (the sources are locked `FOR SHARE` while saving).
  - The waiting limit closes the oldest waiting ones (state `closed`, same as "no longer relevant"), rather than deleting them.
  - A "not before" day the model writes that can't be read skips the new Curiosity (better than asking too early); null means any day. Odd sensitivity reads as low.
  - Raised is final: a raised Curiosity is never offered again. Its reaction is recorded only at the end of the Conversation it was raised in, and only while User Memory works ("none of this runs while User Memory doesn't work"), so one raised with User Memory off keeps no reaction (spec review finding, kept on purpose).
  - The Understanding sees the count "raised N of at most M"; once M is reached it is offered none, and the code also caps `bring_up` at what is left.
  - Review findings kept as they are: `ThreadReaction` is reused for Curiosity reactions (docstring widened, not renamed); the JSON answer reader and "ask twice" loop mirror the other Conversation-end keepers; two rare races (a dropped new one can still close an older one; two replies at once in one Conversation) are left, since one User's replies run one at a time.

## Evidence

- **Conversation end creates, updates and closes Curiosities, honouring the waiting limit:** `tests/test_curiosities.py::test_a_conversation_end_saves_a_curiosity_offered_once_its_day_has_come` (created; the keeper sees "Today: Wednesday 11 Nov 2026" and the Conversation), `test_a_conversation_end_updates_and_closes_waiting_curiosities` (new day and why; another closed), `test_the_waiting_limit_closes_the_oldest_waiting_curiosities` (limit 2: the oldest closed), `test_an_unreadable_curiosity_or_one_for_an_unknown_number_is_skipped`, `test_a_failing_curiosity_keeper_still_saves_the_summary_and_is_not_retried`.
- **Offered only once its day has come, and not after the per-Conversation limit:** `test_a_conversation_end_saves_a_curiosity_offered_once_its_day_has_come` (not on Thursday, `[1] …` on Friday, in Singapore time), `test_no_curiosity_is_offered_once_the_admin_set_number_was_raised` (limit 2 via `PATCH /api/admin/settings`: "raised 1 of at most 2", then none; two picked at once count), `test_a_curiosity_brought_up_reaches_the_reply_and_is_marked_raised` (reply told "Open with it. Why you wonder: …", saved as raised with when and the Conversation; not offered on the next message).
- **Raised ones record the reaction at the next Conversation end:** `test_a_raised_curiosity_records_how_the_user_took_it_when_the_conversation_ends` (the keeper sees "[1] (brought up in this Conversation) …"; reaction `engaged`; the next keeper sees it under "asked recently").
- **Deleting the source removes its Curiosities:** `test_deleting_the_memory_item_or_thread_a_curiosity_came_from_removes_it` (through `DELETE /api/memory-items/{id}` and `DELETE /api/life-threads/{id}`; an unsourced one stays).
- **Feature off (everyone or one User):** `test_with_curiosities_off_for_everyone_none_are_made_or_offered_or_deleted`, `test_with_curiosities_off_for_one_user_none_are_offered_to_them` (back on, offered again). Feature listed: `tests/test_features.py`.
- **User Memory off:** `test_with_user_memory_off_none_are_made_but_waiting_ones_are_still_raised` (no keeping call; the waiting one still reaches the reply and is raised).
- **Not exposed; Delete My Data and Account Deletion remove them:** `test_no_dashboard_or_user_api_shows_curiosities` (`/api/me`, memory items, Life Threads, summaries, admin users and a User's Features). `tests/test_data_deletion.py`: the setup now makes a Curiosity, so `curiosities` is one of the per-User tables that must hold data before and none after Delete My Data and Account Deletion.
- **Settings:** `web/src/components/PlatformSettingsForm.test.tsx` "shows and saves the Curiosity limits"; "Curiosity keeping" on Prompts and Models (`tests/test_admin_settings.py`).
- **Checks:** `make check`: `pytest` 858 passed, 9 deselected; `ruff check`, `ruff format --check`, `mypy` clean; `pnpm lint`, `format:check`, `typecheck` clean; `pnpm test` 364 passed (51 files).
- **/run in the worktree:** the real app ran in a one-off backend container on the worktree's own database (migration 0033 applied on start) with DeepSeek and the fastembed embedder; only the chat channel was a recorder and the clock was set back to Monday 9 Nov 2026 for the first Conversation (worktree Telegram can't send to a fake chat; the main stack wasn't running, so an onboarded Admin was inserted with SQL instead of `make db-copy`).
  - Conversation 1 (Mon 9 Nov): "ugh I have a big presentation to the board on Thursday and I'm so nervous", "it's the budget for my team. if it goes badly we might lose two people". At its end the real keeper saved one Curiosity: "How did Thursday go — did the budget land okay?", not before 2026-11-13, sensitivity high, sourced from the new Memory Item and the new "Board presentation on team budget" Thread.
  - Conversation 2 (now, Sat 14 Nov): "hey zeph". The Understanding was shown "(raised 0 of at most 1 in this Conversation): [1] How did Thursday go — did the budget land okay? …" and chose `{"curiosity": 1, "how": "lead"}`. Zeph replied "Hey! How's it going?" / "How'd Thursday go — did the budget land okay?". The Curiosity became `raised`.
  - Next message ("it actually went really well! they approved the whole budget"): the Understanding was shown "(raised 1 of at most 1 …): None." At the Conversation's end the reaction became `engaged`. Both `curiosities` model calls are in the Model Call Log, no errors.
  - After rebasing onto main (with the User Portrait, issue 10) the run was repeated on a fresh database. It found a real gap: the Understanding chose "weave" for "hey zeph", the reply was told "Ask it when it fits what they're talking about", answered only "Hey. How are you doing?", and the Curiosity was still marked raised, so it was used up without being asked. Fixed: choosing a Curiosity now means asking it in this reply. "Weave" tells the reply "Ask it in this reply, after answering what they said, tied to it where you can", and the Understanding prompt says to put one in `bring_up` only when Zeph should ask it in this very reply (`test_a_curiosity_woven_in_is_still_asked_in_this_reply`). Rerun twice: "weave" gave "Hey you. Good to see you." / "How did it go with the board on Thursday?", and "lead" gave "Hey you. I've been thinking about Thursday — how did it go with the board?". Both were then marked raised.
- **/code-review:**
  - Standards: no hard breaches. Fixed: the copied `read_text` now comes from `life_threads`. Kept (see decisions): `ThreadReaction` reused, keeper reader and retry loop mirror the other keepers, the Feature check for keeping sits in post-conversation like the User Memory check.
  - Spec: nothing missing, no real scope creep (the "asked recently" list keeps the keeper from asking twice). Kept, as recorded decisions: no reaction while User Memory is off; the two rare races; onboarding redo cascading.

## Completion

- Completed: 2026-11-14
- Commits: `cf613a4` (Curiosities, with review fix and CONTEXT.md)
