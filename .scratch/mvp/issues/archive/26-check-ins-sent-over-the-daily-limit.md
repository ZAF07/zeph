# 26 — Users over the daily message limit still get Check-ins

Status: completed

## Parent

`.scratch/mvp/PRD.md` (a caveat left in `issues/archive/13-usage-limits.md`)

## Symptom

Once a User reaches the Daily Message Limit, their messages get the Limit Reply ("I'm honestly wiped for today…"). But the Check-in scheduler doesn't look at the limit, so the Companion can still message the User first later that same day.

That reads oddly in character: Zeph says it needs a rest, then reaches out anyway. If the User replies to that Check-in, they get the Limit Reply again.

Check-ins also cost tokens (they go into the User's Usage), so they keep adding cost after the limit.

## What the spec says

Nothing. Issue 13 and the PRD cover the limit for incoming messages only. Check-ins aren't mentioned.

## Decisions (from `/grill-with-docs`, 2026-11-13)

- **Used up = count reached.** A User has used up today's Daily Message Limit once their message count for their day has reached it, even if no message was turned away yet. (A reply would get the Limit Reply straight away.)
- **No Check-ins for the rest of that day.** This covers the "would you like fewer?" message too. The limit is checked before the Check-in model is asked, so no tokens are spent.
- **One Skipped Check-in per day, User stays due.** Unlike other skips, it does not wait a full frequency gap. The User stays due, so a Check-in can come on their next day (still respecting Quiet Hours, pause, etc.). Only one such skip is recorded per User per day, not one per scheduler tick.
- **Both sides see why.** Admin reason in the Check-in Log: "User had used up today's Daily Message Limit". The User's "Recent check-ins" shows "Skipped — you'd reached today's message limit" (fixed Dashboard text, not Admin-set). Other skips still show "Skipped — gave you some space".
- **Check-ins don't count toward the limit.** A reply to a Check-in counts as one of the User's messages, as now.
- **No "near the limit" rule.** A User below the limit gets Check-ins as normal.
- A limit skip doesn't count toward the Ignore Threshold (skips are already passed over).
- No ADR: easy to reverse. Glossary updated (Skipped Check-in, Daily Message Limit).

## Acceptance criteria

- [x] A due User whose message count for their day has reached the Daily Message Limit gets no Check-in; one Skipped Check-in is recorded with the limit reason, and the User stays due.
- [x] Further scheduler ticks that same User-day record no more limit skips and send nothing.
- [x] On the User's next day (outside Quiet Hours, not paused, no open Conversation), the Check-in is decided as normal.
- [x] A due User at the Ignore Threshold who has used up the limit gets no "would you like fewer?" message that day; they get the limit skip instead, and the question can come on their next day.
- [x] The Check-in model is not called for a User who has used up the limit.
- [x] A User one message below the limit gets Check-ins as normal; sending a Check-in doesn't change their message count.
- [x] Admins see the limit reason for the skip in the Check-in Log.
- [x] The User's "Recent check-ins" on the Dashboard shows "Skipped — you'd reached today's message limit" for a limit skip, and "Skipped — gave you some space" for other skips.
- [x] A limit skip doesn't count toward the Ignore Threshold.
- [x] Verified in the running app (`/run`).

## Comments

- 2026-11-13: Grilled with docs. Decisions and acceptance criteria above; ready to implement.
- 2026-11-13 — done on branch `mvp-26-limit-check-ins`. What changed and the evidence:
  - Limit check: `UsageLimiter.has_used_up_daily_message_limit` (`core/usage.py`) says the limit is used up once the User's message count for their day has reached it, read through the new `UsageRepository.count_messages`. `CheckInService._check_in_if_due` (`core/check_ins.py`) checks it after the feature, pause, Quiet Hours, Telegram link and open Conversation checks, and before the Ignore Threshold and the Check-in model.
  - Limit skip: `_skip_for_daily_limit` saves a Skipped Check-in with the reason `DAILY_LIMIT_SKIP_REASON` ("User had used up today's Daily Message Limit") and next due time `now`, so the User stays due. `_has_limit_skip_today` stops a second one on the same User-day. `CheckIn.skipped_for_daily_limit` (`core/models.py`) spots a limit skip. The Dashboard API sends it as `skipped_for_daily_limit` on each recent Check-in, never the reason text.
  - Dashboard: `recentCheckInTitle` (`web/src/lib/check-ins.ts`) shows "Skipped — you’d reached today’s message limit" for a limit skip, and "Skipped — gave you some space" for other skips.
  - Tests (`tests/test_check_ins_over_daily_limit.py`):
    - `test_a_user_who_used_up_the_limit_gets_one_limit_skip_and_stays_due`: one skip over three ticks, nothing sent, no model call, Admin log reason, and a normal Check-in on the next day.
    - `test_a_user_one_message_below_the_limit_gets_check_ins_as_normal`: the Check-in is sent and the message count stays 1.
    - `test_a_user_at_the_ignore_threshold_over_the_limit_is_asked_about_fewer_next_day`.
    - `test_a_limit_skip_does_not_count_toward_the_ignore_threshold`: passed before the change too, since skips were already passed over. It guards against that changing.
    - Web: `src/lib/check-ins.test.ts` (both titles), and `CheckInsSettings.test.tsx` (a limit skip in the Recent check-ins list).
  - Checks (`make check` steps): ruff, ruff format, mypy (96 files), pytest 590 passed, ESLint, Prettier, tsc, Vitest 317 passed.
  - `/run` (worktree stack on 3060/8060): an Admin test User with Check-ins on, UTC, no Quiet Hours, a fake Telegram link (chat 999000111), `daily_usage.message_count` set to 200 (the seeded limit) and the next due time 5 minutes ago.
    - The 15:26:53 tick saved one Skipped Check-in with reason "User had used up today's Daily Message Limit". At 15:29:32, after more ticks, there was still only one, and the next due time stayed at 15:26:53, so the User is still due.
    - tokens_in and tokens_out stayed 0 (the model was not called), and the backend logged no errors.
    - The Check-ins page showed "Skipped — you’d reached today’s message limit · Fri 13 Nov · Skipped". The Admin Check-in log showed "Run check · Skipped · User had used up today's Daily Message Limit". Neither page had errors.
    - The next-day send was not run live, because it would call the real model and send to a made-up chat. The first test above covers it.
  - Code review (Standards and Spec): no hard Standards breaches and no Spec gaps. Fixed: a clearer method name (`has_used_up_daily_message_limit`), a shared `_count` helper in the Postgres usage repository, and a named `_has_limit_skip_today` check.
  - Glossary: the Skipped Check-in entry now gives the Admin reason text separately from the User's text.
  - Caveats:
    - A limit skip is spotted by its reason text, the same way as the blocked skip, so changing that text would stop old rows from being recognised.
    - The once-a-day check looks only at the newest Check-in. If an Admin raises the limit mid-day so a Check-in goes out, then lowers it again, a second limit skip can be recorded that day.

## Completion

- Completed: 2026-11-13
- Commit: <filled in after merge>
