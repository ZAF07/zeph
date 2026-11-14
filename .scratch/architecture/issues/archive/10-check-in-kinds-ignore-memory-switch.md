# 10 — Check-in Kinds ignore the User Memory switch

Status: completed

## Parent

Follow-up to issue 02 (User Memory off means "stop learning, keep using"), decided with the user on 14 Nov 2026. `CONTEXT.md` (Check-in Kind) is already updated.

## What to build

User Memory off only means "don't learn anything new about me from now on". Memories already saved, and not deleted by the User, are used everywhere, Check-ins included. So the User Memory switch no longer limits which Check-in Kinds can be sent.

- Every Check-in Kind can go to a User whichever User Memory switch is off (the User's or the Admin's).
- Kinds that send a Shared Photo go to a User who has Shared Photos and has Photo Viewing working. User Memory no longer matters for them.
- Remove "allowed without User Memory" completely. It has no meaning now:
  - the Kind field and its database column (new migration)
  - the admin API and the "Allowed when memory is off" box on the Check-in Kinds admin page
  - the seed data and its comments (`seed/check_in_kinds.yaml`)
- Check the reply note for Features that aren't available (`reply_features_unavailable_note`). With the Admin's switch off it names "User Memory", which could lead the Companion to say it can't remember things it still uses. Make sure the reply only says it can't learn new things.

## Decisions

- Memory off = "stop learning". Never "stop using". This applies to every place saved memories are read.
- Photo Viewing stays separate: with it off, Shared Photos aren't used.

## Acceptance criteria

- [x] With either User Memory switch off, every Check-in Kind can be chosen, and the Check-in still sees saved memories
- [x] With either switch off, a "look back at a photo" Kind is offered when the User has Shared Photos and Photo Viewing works
- [x] With Photo Viewing off, photo Kinds aren't offered
- [x] "Allowed without User Memory" is gone from the code, the database (migration), the admin page and the seed data
- [x] With the Admin's switch off, a reply never claims it can't remember saved memories
- [x] Tests for each switch combination; backend and Dashboard checks pass
- [x] `/run`: with each switch off, a follow-up Check-in about a saved memory is sent, and the admin Check-in Kinds page has no memory box

## Blocked by

None. Touches `core/check_ins.py`, as issue 04 does. Doing this first leaves issue 04 with fewer rules to move.

## Comments

- Built test-first: the new backend tests (every Kind and the look-back Kind with the User's, the Admin's and both switches off; Photo Viewing off by the User or Admin; the migration; the reply note) and the Dashboard tests were red before the code changed, then green.
- Kinds: `CheckInService.list_kinds` (was `kinds_for(user)`) returns every Kind. `_shared_photos` checks only Photo Viewing. `_memory` already ignored the switch (issue 02).
- Removed "allowed without User Memory": `CheckInKind`/`CheckInKindDetails` field, `check_in_kinds.allowed_without_user_memory` column (migration `0023`, downgrade adds it back as true for every Kind), admin API request/response, the "photo Kind needs User Memory" refusal, the admin card's switch, `seed/check_in_kinds.yaml` and its comment. The photo Kind's card now says "Only for Users with Photo Viewing on and a Shared Photo".
- Reply note: `FeatureDetails.reply_note_name` names User Memory in `reply_features_unavailable_note` as "learning new things about them (you still remember and use everything you already know about them)", so with the Admin's switch off the reply doesn't say it can't remember. The wording lives in code next to the Feature names, not as an admin setting.
- Checks: `ruff check`, `ruff format --check`, `mypy` ("no issues found in 98 source files"), `pytest` 615 passed (9 deselected evals); `pnpm lint`, `format:check`, `typecheck`, `vitest` 322 passed, `pnpm build` compiled.
- `/run` (worktree stack on 3120/8120, copy of the main database via `make db-copy`, real DeepSeek):
  - Migration: main's database was at 0022; the copy upgraded to 0023 on start, the column is gone and all 5 Kinds kept.
  - Admin Check-in Kinds page: no memory box, 0 switches; editing and saving "A follow-up" worked ("Saved A follow-up."); the photo Kind shows the Photo Viewing line.
  - Check-ins: a signed-in test User with a saved Challenges memory ("Had a big job interview at a design studio yesterday…"). The real `CheckInService` was run in the backend image with Postgres and DeepSeek, Telegram swapped for a recorder (the worktree can't message real chats; backend stopped so its scheduler couldn't race).
    - User's switch off (turned off on Account & privacy): all 5 Kinds offered, memory seen, DeepSeek chose **A follow-up**: "Been thinking about that interview yesterday — how did it go?…", saved as sent.
    - Admin's switch off (Features page, User's switch back on): all 5 Kinds offered, **A follow-up** sent: "How did the interview go yesterday?…".
  - Reply with the Admin's switch off (real DeepSeek, Persona + response prompt + memory + the real unavailable note): asked "does that mean you forgot everything about me?", it said "No, I still remember what we've talked about before… What's turned off is me picking up new things about you going forward."
- `/code-review`: Standards — no hard violations; fixed `kinds_for` taking an unused User (now `list_kinds()`) and the doubled reply-note-name lookup (`FeatureDetails.name_in_reply_note`). Spec — nothing missing, no scope creep; noted the reply-note wording lives in code.

## Completion

- Completed: 2026-11-14
