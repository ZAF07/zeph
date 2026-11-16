# 05 — Check-in polish: Check in Now mid-Conversation is woven in

Status: completed

Track: whichever agent finishes first (needs both tracks).

## Parent

`.scratch/check-in-polish/PRD.md`

## What to build

Join Check in Now (04) with Woven-in Check-ins (02). When an Admin asks for a Check in Now for a User who is mid-Conversation, it is offered to the reply flow as a Woven-in Check-in instead of waiting for the Conversation to end.

- The reply flow's "is a Check-in due?" check counts a waiting Check in Now. For that User it goes past the Feature switch and the pause, matching 04.
- The "not struggling" code rule still applies.
- When woven in, the saved Check-in records the requesting Admin and is marked woven in. The request is cleared, and the next Due Time is "decided at + frequency gap".
- If no reply weaves it in, it goes out on its own once the Conversation ends, still as the Admin's Check in Now.

## Acceptance criteria

- [x] A Check in Now for a User mid-Conversation is offered to the woven-in Check-in call and, when chosen, woven into the reply. It is logged as woven in and as asked for by that Admin (end-to-end test).
- [x] It goes past the pause and the Feature switch, but never past "struggling".
- [x] If not woven in, it is sent on its own after the Conversation ends, logged with the Admin.
- [x] The request is cleared after either path, and the next Due Time is one gap after.
- [x] All backend and web checks pass.
- [x] Verified with `/run`: request a Check in Now while chatting through the webhook and see it woven into a reply.

## Blocked by

- `.scratch/check-in-polish/issues/02-woven-in-check-ins.md`
- `.scratch/check-in-polish/issues/04-check-in-now.md`

## Comments

### 2026-11-16 — done (agent, branch `check-in-polish-05-woven-check-in-now`)

What changed:
- `may_weave_check_in`: opted in, onboarded and not struggling always apply. A waiting Check in Now then counts as due and goes past the Feature switch and the pause; otherwise the old rule (due, Feature on, not paused).
- `WovenCheckIn` carries the Check in Now it is for. Saving it records the requesting Admin, sets the next Due Time to "decided at + gap" and clears that request in the same conditional statement (`add_woven_in`); a request asked for since is kept (shared `_clear_check_in_now_if_decided` with `add`). A reply that fails to send puts the request back and the Due Time stays as read.
- Not woven in: unchanged from issue 04 — the tick holds it back as waiting to be woven in, then sends it as the Admin's once the Conversation ends.
- Replaced issue 02's `test_a_waiting_check_in_now_is_not_woven_in_and_is_left_to_the_tick`.

Evidence per acceptance criterion:
- Woven in and logged with the Admin: `tests/test_woven_in_check_ins.py::test_a_check_in_now_mid_conversation_is_woven_into_the_reply_and_logged` (webhook, scripted chat model: reply carries the note; log sent / woven in / requested by the Admin; request cleared; next Due Time = decided at + 1 day).
- Past pause and Feature switch, never past struggling: `test_a_check_in_now_is_woven_in_past_the_pause_and_the_feature_switch` (User paused a week and Feature off for them; still paused after), `test_a_check_in_now_is_never_woven_in_while_the_user_is_struggling` (no call, nothing logged, request still waiting).
- Not woven in → on its own after the Conversation, with the Admin: `test_a_check_in_now_not_woven_in_goes_out_on_its_own_after_the_conversation` ("not now", tick mid-Conversation keeps it waiting, tick after the quiet gap sends it; log woven in false, requested by the Admin).
- Cleared after either path, next Due Time one gap after: asserted in the woven-in and the not-woven-in tests above; `test_a_woven_in_check_in_now_whose_reply_fails_to_send_keeps_waiting` (nothing logged, request waiting again, Due Time unchanged).
- Checks: backend 1183 passed, ruff, ruff format --check, mypy src clean. Web (no web changes): lint, format:check, typecheck clean, 455 passed.
- `/run` (worktree stack 3010/8010/5442): real app in the backend container on the worktree database with the real DeepSeek model; only Telegram (recording channel), scheduler (ticked by hand), timer and Clerk swapped. Pia opted in, connected, paused a week, 23:00 her time (Quiet Hours). She chatted; the Admin's Check in Now came back "requested"; the tick sent nothing and the Schedule showed "waiting_to_be_woven_in" with Check in Now waiting. Her next message ("making some tea now, the evening is really calm") got a reply that wove in "A present-moment pause" ("…Just for a second, notice the warmth of the cup in your hands and how quiet it actually is around you."). Check-in Log: sent, A present-moment pause, woven in, requested by "Run Admin". Request cleared, next Due Time exactly 1 day after the decision, still paused until 23 Nov.
- `CONTEXT.md`: Woven-in Check-in says a paused User can get one an Admin asked for with Check in Now, logged with the Admin.

Caveats (from code review, left as is):
- A tick already asking the Check-in model for a Check in Now (Conversation just ended) and a reply that weaves the same request in, if the User writes during that model call, could both send. The tick's save doesn't check the Due Time it read; scheduled Check-ins have had the same narrow race since issue 02. Fixing it means changing the tick's shared save path, so it is left for a follow-up.
- If a second Admin asks for a Check in Now in the seconds between a woven-in save and that reply failing to send, taking it back restores the first request (same as the tick's take-back).


## Completion

- Completed: 2026-11-16
- Commits: 8fec9a9 (implementation), fcd8014 (review fixes), a5af329 (archive, CONTEXT.md)
- Merge: ae17d21
