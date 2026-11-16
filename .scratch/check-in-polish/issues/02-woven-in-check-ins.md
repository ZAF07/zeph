# 02 — Check-in polish: Woven-in Check-ins

Status: in-progress

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

- [ ] A Check-in due mid-Conversation gets woven into the reply when the model says "weave in", and is logged as sent, woven in, with its Kind (end-to-end via webhook, scripted chat model).
- [ ] No woven-in Check-in call is made while the User is struggling or paused.
- [ ] A woven-in Check-in can happen during Quiet Hours.
- [ ] "Not now" or an unusable answer means nothing is woven in, and it stays due.
- [ ] When no reply weaves it in, a standalone Check-in goes out after the Conversation ends.
- [ ] The call is given the current Conversation, the Understanding, the User Portrait and only Kinds without fixed behaviour.
- [ ] Woven-in Check-ins never count toward the Ignore Threshold.
- [ ] A reply that fails to send logs no Check-in. The same Check-in is never sent twice.
- [ ] The new prompt is editable on the admin Prompts/Platform Settings page.
- [ ] The Check-in Log shows "woven in". The Model Call Log shows the step with its shape only.
- [ ] Held-back state "waiting to be woven in" is saved while a Conversation is open (visible on the Check-in Schedule once issue 03 lands).
- [ ] Tick reads stay flat as due Users grow (existing reads-per-tick test still passes).
- [ ] New eval cases exist. Run only after the user OKs the cost.
- [ ] All backend and web checks pass.
- [ ] Verified with `/run`: post updates to the worktree's webhook and see a reply with the Check-in woven in.

## Blocked by

- `.scratch/check-in-polish/issues/01-check-in-rhythm.md`

## Notes for parallel work

Track B (issue 03) adds the held-back reason storage that the "waiting to be woven in" state uses. If 03 hasn't merged yet, add the storage here in the same shape the PRD gives (reason and until on the User's Check-in state). Whichever merges second reconciles it. Rebase, and renumber migrations if they clash.

## Comments

### 2026-11-16 — plan (agent, branch `check-in-polish-02-woven-in`)

- Held-back reason `in_conversation` is renamed `waiting_to_be_woven_in` (migration 0048 updates stored rows). Mid-Conversation the tick keeps the Due Time as it is and saves "until" = when the Conversation could end.
- New core module `woven_check_ins.py`: the code rule (due, opted in + Feature on, not paused, not struggling), the call (Check-in model + new `woven_check_in_prompt`), reading the answer, and the reply section. `ReplyService` runs the call in a background thread next to the memory and Knowledge look-ups.
- Saving: the Check-in (sent, Kind, `woven_in`) and the next Due Time are saved in one statement **before** the reply is delivered, only if the Due Time is still the one read (so a tick or a second reply can't log it twice). If composing or delivering the reply fails, it is taken back and stays due. This is the standalone "save, then send" rule, so a failed save never sends it and it is never sent twice.
- Reply detection: the User's next message in the open Conversation claims a woven-in Check-in's reply (same reply window). The Ignore Threshold count passes over woven-in Check-ins.
- Model Call Log: new `check_in_shape` (Kinds offered, woven in or not, Kind) on the newest Check-in call of the Message trace.
- Evals: Understanding cases gain `check_in_due` and a per-Message `woven_in` expectation.
