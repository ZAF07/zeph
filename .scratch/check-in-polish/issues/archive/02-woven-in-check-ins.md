# 02 — Check-in polish: Woven-in Check-ins

Status: completed

Track: A (User side).

## Parent

`.scratch/check-in-polish/PRD.md`

## What to build

A Check-in that comes due while a Conversation is open no longer just waits. Zeph may weave it into a reply, the way a friend drifts onto a side topic. If no reply finds a good moment, it goes out on its own after the Conversation ends, as today.

- **Standalone path while a Conversation is open:** the tick doesn't send. It saves the held-back state "waiting to be woven in", with a retry when the Conversation could end. The Due Time stays as it is.
- **In the reply flow, after the Understanding** (ADR-0009): the code checks all of these:
  - the Check-in is due
  - Check-ins work for the User (opted in and Feature on)
  - the User is not paused
  - the Understanding says they are not struggling

  If any check fails, no call is made. This is a code rule, not a model choice. Quiet Hours do **not** stop it.
- **The woven-in Check-in call:**
  - It runs alongside the Understanding's look-ups.
  - It uses the Check-in model setting (model and thinking) and a **new Admin-editable prompt** in Platform Settings (ADR-0004), separate from the standalone Check-in prompt.
  - It is given:
    - Persona and the User's local time
    - their recent Check-ins
    - their User Portrait, Memory Items and newest Conversation Summaries
    - the current Conversation's messages
    - this message's Understanding
    - the Kinds that may go: only Kinds without fixed behaviour (no photo or Curiosity Kinds)
  - It answers either "weave in" with one Kind's exact name and a one-line note on what to bring up, or "not now". An unknown Kind or an unusable answer means "not now".
- **The reply:** on "weave in", the reply call gets the Kind's description and the note, and weaves it in naturally, at most one per reply.
- **Once the reply is sent,** in one transaction (ADR-0008):
  - a Check-in is saved: outcome sent, the Kind, marked **woven in**
  - the Due Time moves on (issue 01's rules)
  - the held-back state is cleared

  If the reply isn't sent, nothing is logged and the Check-in stays due.
- **Afterwards:** the User's next message counts as its reply (existing reply window). Woven-in Check-ins never count toward the Ignore Threshold. They show in the User's "Recent check-ins" like any other.
- **Check-in Log** shows "woven in" (admin API and page). Never message text.
- **Model Call Log** (ADR-0010): the call shows as a Check-in step under that Message's trace. Its shape is the number of Kinds offered, weave in or not now, and the Kind.
- **Evals:** add eval cases for the woven-in decision: weave in when it fits, "not now" when the moment is wrong. **Eval runs cost money: confirm with the user before running.** Existing Understanding evals don't need re-running.

Terms: Woven-in Check-in, Held-back Check-in, Quiet Hours, Check-in Log (`CONTEXT.md`).

## Acceptance criteria

- [x] A Check-in due mid-Conversation gets woven into the reply when the model says "weave in", and is logged as sent, woven in, with its Kind (end-to-end via webhook, scripted chat model).
- [x] No woven-in Check-in call is made while the User is struggling or paused.
- [x] A woven-in Check-in can happen during Quiet Hours.
- [x] "Not now" or an unusable answer means nothing is woven in, and it stays due.
- [x] When no reply weaves it in, a standalone Check-in goes out after the Conversation ends.
- [x] The call is given the current Conversation, the Understanding, the User Portrait and only Kinds without fixed behaviour.
- [x] Woven-in Check-ins never count toward the Ignore Threshold.
- [x] A reply that fails to send logs no Check-in. The same Check-in is never sent twice.
- [x] The new prompt is editable on the admin Prompts/Platform Settings page.
- [x] The Check-in Log shows "woven in". The Model Call Log shows the step with its shape only.
- [x] Held-back state "waiting to be woven in" is saved while a Conversation is open (visible on the Check-in Schedule once issue 03 lands).
- [x] Tick reads stay flat as due Users grow (existing reads-per-tick test still passes).
- [x] New eval cases exist. Run only after the user OKs the cost.
- [x] All backend and web checks pass.
- [x] Verified with `/run`: post updates to the worktree's webhook and see a reply with the Check-in woven in.

## Blocked by

- `.scratch/check-in-polish/issues/01-check-in-rhythm.md`

## Notes for parallel work

Track B (issue 03) adds the held-back reason storage that the "waiting to be woven in" state uses. If 03 hasn't merged yet, add the storage here in the same shape the PRD gives (reason and until on the User's Check-in state). Whichever merges second reconciles it. Rebase, and renumber migrations if they clash.

## Comments

### 2026-11-16 — plan (agent, branch `check-in-polish-02-woven-in`)

- Held-back reason `in_conversation` is renamed `waiting_to_be_woven_in` (migration 0048, renumbered 0049 on rebase, updates stored rows). Mid-Conversation the tick keeps the Due Time as it is and saves "until" = when the Conversation could end.
- New core module `woven_check_ins.py`: the code rule (due, opted in + Feature on, not paused, not struggling), the call (Check-in model + new `woven_check_in_prompt`), reading the answer, and the reply section. `ReplyService` runs the call in a background thread next to the memory and Knowledge look-ups.
- Saving: the Check-in (sent, Kind, `woven_in`) and the next Due Time are saved in one statement **before** the reply is delivered, only if the Due Time is still the one read (so a tick or a second reply can't log it twice). If composing or delivering the reply fails, it is taken back and stays due. This is the standalone "save, then send" rule, so a failed save never sends it and it is never sent twice.
- Reply detection: the User's next message in the open Conversation claims a woven-in Check-in's reply (same reply window). The Ignore Threshold count passes over woven-in Check-ins.
- Model Call Log: new `check_in_shape` (Kinds offered, woven in or not, Kind) on the newest Check-in call of the Message trace.
- Evals: Understanding cases gain `check_in_due` and a per-Message `woven_in` expectation.

### 2026-11-16 — done (agent)

Evidence per acceptance criterion:

- Woven in and logged: `tests/test_woven_in_check_ins.py::test_a_check_in_due_mid_conversation_is_woven_into_the_reply_and_logged` (webhook, scripted chat model: reply gets the Kind's description and note, log shows sent / A follow-up / woven in, Due Time + 1 gap, held-back cleared).
- No call while struggling or paused: `test_no_woven_in_call_is_made_while_the_user_is_struggling`, `..._while_check_ins_are_paused` (also before the Due Time and with the Feature off).
- Quiet Hours: `test_a_check_in_can_be_woven_in_during_quiet_hours`.
- Not now / unusable answer: `test_not_now_or_an_unusable_answer_weaves_nothing_and_it_stays_due` (not now, photo Kind, unknown Kind, empty note, no JSON, model error).
- Standalone after the Conversation: `test_when_no_reply_weaves_it_in_it_waits_then_goes_out_after_the_conversation`.
- Call input: `test_the_woven_in_call_is_given_the_conversation_understanding_and_portrait` (Conversation, Understanding, Portrait, local time, only the four plain Kinds).
- Ignore Threshold: `test_woven_in_check_ins_never_count_toward_the_ignore_threshold`.
- Failed send / never twice: `test_a_reply_that_fails_to_send_logs_no_check_in_and_it_stays_due`, `test_a_reply_that_fails_after_its_first_part_keeps_the_woven_in_check_in`, `test_a_woven_in_check_in_whose_save_fails_is_not_woven_in`, `test_a_woven_in_check_in_is_not_woven_in_again_nor_sent_on_its_own`. Saved conditionally on the Due Time read (`add_woven_in`), so a tick or second reply can't log it twice.
- Editable prompt: `test_the_woven_in_check_in_prompt_is_editable_by_admins`; seen on `/admin/prompts` (Check-ins card, "Woven-in Check-in prompt").
- Check-in Log / Model Call Log: `test_the_model_call_log_shows_the_woven_in_step_with_its_shape_only`, `tests/test_admin_check_ins.py`; `CheckInLog.test.tsx`, `ModelCallTraceView.test.tsx`; seen on `/admin/check-in-log` ("Sent · Woven in") and the trace page (Kinds offered 4, Decision Weave in, Kind chosen).
- Held-back state: tick test above (`waiting_to_be_woven_in`, until = Conversation end, Due Time unchanged); seen on `/admin/check-in-schedule` ("Waiting to be woven in, until 14:37"). Migration 0049 renames stored `in_conversation`.
- Tick reads flat: `tests/test_check_in_hold_back.py::test_reads_per_tick_stay_the_same_as_due_users_grow` passes.
- Evals: 3 new Understanding cases (`check-in-woven-in-at-an-easy-pause`, `check-in-not-now-while-asking-for-help`, `check-in-not-now-mid-story`) with `check_in_due` and `woven_in`; editable on the case form (ADR-0014). Runner path tested in `tests/test_eval_runner.py::test_an_understanding_case_checks_whether_the_due_check_in_was_woven_in`. Run on 2026-11-16 with the owner's OK (see below).
- Checks: backend 1162 passed, ruff, ruff format --check, mypy clean. Web: lint, format:check, typecheck clean, 449 passed.
- `/run` (worktree stack, 3010/8010): real app in a backend container on the worktree DB, real DeepSeek model, only Telegram/scheduler/timer swapped. Message before the Due Time: no woven-in call. Due Time moved 30 min back + tick: held back `waiting_to_be_woven_in` until the Conversation could end, Due Time kept. Light message during Quiet Hours: model chose "A present-moment pause"; reply "take a sec to actually clock it…"; logged sent / woven in / no message text; Due Time +24 h; next message marked it replied. (A first run's model said "not now" twice, which the prompt allows.)

Caveats (from code review, left as is):
- Taking a woven-in Check-in back clears "waiting to be woven in" until the next tick saves it again.
- A message sent while the woven-in reply is still being written counts as its reply.
- The woven-in call runs in its own one-thread pool per reply, as the spec asks it to run next to the look-ups.

### 2026-11-16 — rebased onto issue 04 (Check in Now)

- Issue 04 merged first with migration 0048, so this issue's migration is now 0049 (revises 0048). The worktree database, rolled back to 0047, migrated 0047 → 0048 → 0049 cleanly; a stored `in_conversation` reason became `waiting_to_be_woven_in`.
- Conflicts kept both sides: Check-ins carry `requested_by` and `woven_in`; the Check-in Log shows "Asked for by …" and "Woven in" under the outcome.
- Issue 04's `decide_check_in_now` held a mid-Conversation Check in Now back as `in_conversation`; it now uses `waiting_to_be_woven_in` (same retry time). A reply doesn't weave in a Check-in while a Check in Now waits, so the tick still sends that one as the Admin's (no double send). Weaving a Check in Now in is issue 05. Test: `test_a_waiting_check_in_now_is_not_woven_in_and_is_left_to_the_tick`.
- Checks after the rebase: backend 1179 passed, ruff, ruff format --check, mypy clean. Web: lint, format:check, typecheck clean, 455 passed.
- `/run` repeated on the merged code (same in-container script, real DeepSeek): no call before the Due Time; tick held back `waiting_to_be_woven_in` until the Conversation could end with the Due Time kept; during Quiet Hours the model wove in "A casual hello" ("How was the rest of the week, beyond it just being long?"), logged sent / woven in, Due Time +24 h, next message marked it replied.

### 2026-11-16 — eval run (owner OK'd the cost)

Ran on a fresh worktree stack of merged main (7c72b0f), real DeepSeek. The command picked the whole Understanding eval, so all 15 cases ran: 14 passed.
- `check-in-woven-in-at-an-easy-pause`: PASS (wove in the due Check-in).
- `check-in-not-now-while-asking-for-help`: PASS (Need Advice; said not now).
- `check-in-not-now-mid-story`: PASS (said not now).
- `reminded-of-sister`: FAIL on the Judge rule `raises_sister_naturally` (the Understanding brought Mei up, the reply didn't). It has no Check-in due, so no woven-in call runs there. Reruns: merged main 2 of 3 passed, pre-merge main (4b20b7f) 1 of 1 passed. It's a flaky reply, not caused by this change.

## Completion

- Completed: 2026-11-16
- Commits: 273a6bb (implementation), efd619c (review fixes), 7cc21b6 (archive), ac7e807 (rebase onto issue 04, migration 0049)
- Merge: 668fc93
