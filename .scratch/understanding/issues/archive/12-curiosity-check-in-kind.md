# 12 — "Something I've been wondering" Check-in Kind

Status: completed

## Parent

`.scratch/understanding/PRD.md`

## What to build

A new fixed-behaviour Check-in Kind opens a Conversation with one of the User's Curiosities. Like the photo Kind, Admins can edit its wording but not what it does. It is offered to the Check-in model only for a User with a waiting Curiosity whose day has come, the Curiosities Feature working, and under the Admin-set Curiosity Check-ins per week (start 1). Sending it marks that Curiosity raised; the User's reply starts a Conversation beginning with that Check-in, as today.

## Acceptance criteria

- [x] Seeded Kind with fixed behaviour; Admins can edit wording, not behaviour, and Users see it read-only like other Kinds
- [x] Offered only when a Curiosity is due, the Feature works and the weekly limit isn't reached
- [x] The sent Check-in uses that Curiosity and marks it raised
- [x] Weekly limit is an Admin setting
- [x] Shows in the Check-in Log with its Kind, as other Kinds do
- [x] Tests at the scheduler/webhook seam with fake clock and scripted Check-in model; checks pass
- [x] `/run`: a due User with a due Curiosity gets this Check-in

## Blocked by

- `.scratch/understanding/issues/11-curiosities.md`

Note: the Check-in decision is now a pure module (`.scratch/architecture/issues/archive/04-check-in-decision.md`, completed); offer this Kind through it.

## Comments

### 2026-11-14 — plan (branch `understanding-12-curiosity-check-in-kind`)

- Check-in Kinds get a second fixed flag, `raises_curiosity` (like `sends_shared_photo`: Admins can't set it; a Kind they add never has it). The seed file gets a sixth Kind, "Something I've been wondering".
- Migration 0035 (0034 was taken by issue 13 on main): adds the flag, `check_ins.curiosity_id` (set null if the Curiosity is deleted), and on an existing install adds the Kind last unless one has its name.
- New setting `curiosity_check_ins_per_week` (start 1, 0–7) on Settings under Curiosities. "Per week" means the last 7 days, counted from sent Check-ins of a Kind that raises a Curiosity.
- The pure decision (`decide_check_in`) offers that Kind only when Curiosities works for the User, they have a waiting Curiosity whose day has come in their time zone, and fewer than the weekly limit were sent in the last 7 days. The facts are read in bulk for every due User.
- The Check-in model then also sees the due Curiosities, numbered (question, why, sensitivity), and must name one as `"curiosity": <number>` when it picks the Kind; a missing or wrong number is an unusable answer (tried again next tick), like photos. The ask sits in code, so the stored Check-in prompt is unchanged.
- Once the message counts as sent, the Curiosity is marked raised (no Conversation yet). When the User's reply starts the Conversation with that Check-in, the Curiosity is linked to it, so it counts toward the per-Conversation limit and the keeper records how they took it at Conversation end.
- Admin card shows "Asks something Zeph has been wondering"; Users see the Kind on their Check-ins page like the others. The Check-in Log shows its Kind name as today.

### 2026-11-14 — evidence

- `make check` on the branch rebased on `origin/main` (b3a4c3c, with issue 13): ruff, ruff format, mypy pass; pytest 904 passed; web lint, Prettier, typecheck pass; Vitest 372 passed. `pnpm build` passes (with `.env` loaded).
- Pure decision tests (`tests/test_check_in_decision.py`): a due Curiosity offers the Kind; Curiosities off, or the weekly limit reached, doesn't; User Memory off still offers it.
- Seam tests `tests/test_curiosity_check_in.py` (14, through `scheduler.tick()` and the webhook, fake clock, scripted Check-in model): the model sees the due Curiosities numbered with question, why and sensitivity and the `"curiosity"` ask; the sent Check-in asks it, is saved with its Kind (User page and Check-in Log) and marks it raised; a reply starts a Conversation with the Check-in, links the Curiosity to it (the Understanding sees "raised 1 of at most 1", nothing offered), and the keeper records "engaged" at its end; not offered before its day, with Curiosities off, or over the weekly limit (offered again after 7 days); due on its day in the User's time zone while UTC is still the day before; the weekly limit follows the Admin setting (2 allows a second, 0 none); a missing, out-of-range or `true` number sends nothing and is tried again; a refused send leaves it waiting, a timed-out send (counts as sent) marks it raised; Admins see `raises_curiosity`, can rename it (flag stays), can't set it on an added Kind; Users see the Kind; migration: an existing install gets it last, a fresh install from the seed. Older tests updated for the sixth Kind. Vitest: the admin card says "Asks something Zeph has been wondering"; the Settings form shows and saves "Most Curiosity Check-ins per week".
- `/run` (worktree stack, real DeepSeek; only the chat channel was a recorder, since worktree Telegram can't send to a fake chat; the real app ran in a one-off backend container with a manual scheduler; due times and Conversation times shifted with SQL instead of waiting):
  - Fresh database: migrations ran on start; six Kinds, "Something I've been wondering" last with `raises_curiosity`; `curiosity_check_ins_per_week` seeded at 1. After rebasing (migration renumbered to 0035), a fresh database ran 0034 (issue 13) then 0035 on start.
  - A signed-in User "Sam" (Singapore, Saturday 20:45) with a Telegram link to a fake chat, one Curiosity due (presentation, not before 13 Nov) and one not yet (wedding fitting, 20 Nov). The running backend first tried the Check-in itself: Telegram refused the fake chat ("chat not found"), the Check-in was taken back and the Curiosity stayed waiting.
  - On the next tick the Check-in model was offered the new Kind and only the due Curiosity, chose it on its own and wrote "hey Sam, saturday evening and I'm randomly thinking about it — how did the board presentation go on Thursday?"; saved as sent with its Kind and Curiosity; the Curiosity marked raised with no Conversation.
  - A reply posted to the webhook started a Conversation beginning with the Check-in; the Check-in was marked replied and the Curiosity linked to that Conversation. After shifting the Conversation's time past the quiet gap, the real keeper recorded "engaged" (and saved a new follow-up Curiosity).
  - With the wedding Curiosity made due and Sam due again, the Kind wasn't offered (1 sent this week, limit 1); a follow-up was sent instead. After raising the limit to 2 on the Settings page, the next tick offered the Kind with only the wedding Curiosity (the model chose a casual hello that time).
  - Admin pages (Playwright, signed-in Admin): the Check-in Log lists the Check-in with Kind "Something I've been wondering" and "Replied"; the Kind's card says "Asks something Zeph has been wondering / Only when a Curiosity is due, within the weekly Curiosity Check-in limit" at 1280 and 390 px; the Settings field showed 1, saved 2 and kept it after reload; no page errors.
  - Repeated after the review fixes and rebase on a fresh database (User inserted by SQL): the Kind was sent, the due Curiosity raised, the other still waiting.
  - Cleaned up: both run Clerk users (and one left by a timed-out sign-in try) deleted with their rows; the worktree database is removed at teardown.
- Code review (`/code-review`, Standards and Spec in parallel): no hard rule breaks; nothing missing. Fixed: the "waiting and due" filter is one shared function (`due_curiosities`); added tests for the User's time zone and a send that may have arrived.

### Decisions

- Like the photo Kind, the Kind is marked by a fixed `raises_curiosity` flag, so Admins can rename it; Admins can't set it, and a removed one can't be added back from the admin area.
- "Per week" is the last 7 days, counted from sent Check-ins of a Kind with the flag (rolling, by the time it was sent). A removed Kind's past sends drop out of the count, which doesn't matter since it can't be offered again.
- The Curiosity is marked raised only once the message counts as sent (a refused or blocked send leaves it waiting). The mark is its own write after the send; if it fails, the Curiosity could be asked again. Rare and harmless, left as is.
- A reply inside the reply window links the Curiosity to its Conversation, so it uses up that Conversation's Curiosity (limit 1) and the keeper records how the User took it. A reply after the window starts a Conversation without the Check-in, as today, so that Curiosity stays raised with no recorded reaction; it still shows to the keeper later as "asked recently, not known how they took it".
- Not changed from review: one boolean per fixed Kind behaviour (a Kind could in theory have both flags, but only the seed or a migration sets them); the instruction for the model sits in code beside the numbered list, like the photo one, so the stored Check-in prompt needs no reset; `shared_photos` and `due_curiosities` travel together through three functions; the window of 7 days is fixed in code.

## Completion

- Completed: 2026-11-14
- Commit: <to be filled in after merge>
