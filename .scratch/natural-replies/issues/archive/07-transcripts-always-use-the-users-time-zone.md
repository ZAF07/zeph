# 07 — Transcripts always use the User's time zone

Status: completed
Track: B
Blocked by: None - can start immediately

## Parent

`.scratch/natural-replies/archive/PRD.md` (follow-up from issue 04)

## What to build

The transcript helpers in `src/companion/core/transcripts.py` (`readable_content`, `to_transcript_lines`) and `to_chat_history` in `core/response_composition.py` take `time_zone: str | None = None`. Callers that leave it out get UTC without anyone noticing. The end-of-Conversation steps do leave it out: `patterns.py`, `life_threads.py`, `curiosities.py`, `move_outcomes.py`, `personal_stickers.py`, `post_conversation.py`. So a Replied-to Text's day ("from 3 Nov") can be a day off for a User far from UTC, near midnight.

- Make `time_zone` a required argument (no default) on those helpers, so mypy fails on any caller that forgets it, now or later.
- Pass the User's time zone (`snapshot.user.time_zone`) at every caller. UTC stays only for a User with no time zone set, which `format_day` already handles.
- No behaviour change for the live reply path, which already passes it.

## Acceptance criteria

- [x] The helpers have no `time_zone` default; mypy passes on `src/`.
- [x] Every caller passes the User's time zone.
- [x] Test: a Replied-to Text sent at 23:30 UTC shows the next day in the transcript of a Conversation-end step (e.g. Life Threads keeping) for a User in Singapore (fake chat model prompts); all Python checks pass.
- [x] `/run`: in a worktree, a User in Singapore replies to a text sent near UTC midnight, the Conversation ends (shift timestamps, don't wait), and the end step's prompt in the Model Call Log shows the Singapore day.

## Blocked by

None - can start immediately.

## Comments

**Done, 24 Nov 2026.** Evidence per criterion:

- No defaults: `readable_content`, `to_transcript_lines` (`core/transcripts.py`) and `to_chat_history` (`core/response_composition.py`) take `time_zone: str | None` with no default; `mypy src` clean (218 files).
- Every caller passes it: Day Summary (`describe_conversation`, `describe_earlier_conversations`), Life Threads, Patterns (incl. `describe_days_behind_evidence`), Curiosities, Move Outcomes and Personal Stickers (`describe_stickers`) all pass `snapshot.user.time_zone`; the reply path, Safeguard and Recent Messages already did. Grep of `src/` finds no caller left without it.
- Test: `test_conversation_end_steps_show_the_replied_to_day_in_the_users_time_zone` (Singapore User, Replied-to Text at 23:30 UTC on 3 Nov 2025, the Day Summary and Life Threads keeping prompts say "from 4 Nov 2025"). Red before the fix (showed 3 Nov), green after. `pytest` 1648 passed; `ruff check`, `ruff format --check`, `mypy` clean.
- `/run` in the worktree: real backend, Postgres and chat model. Seeded a Singapore Admin User and Telegram link with SQL, posted a reply update to `/telegram/webhook` replying to a Companion text sent 22 Nov 2026 23:30 UTC (the reply itself failed at Telegram, as expected for a fake chat; the text saved with its Replied-to Text). Shifted the Conversation's times back 2 hours; the real scheduler ended it. The Model Call Log prompts for `conversation_end`, `life_threads`, `patterns` and `curiosities` all show `Person: (replying to the Companion's text from 23 Nov 2026, "have you told your mum about the job yet?") not yet, scared tbh`, the Singapore day (UTC would say 22 Nov).
- `docs/message-pipeline/README.md` decision 20 no longer says the end steps use UTC.

Decisions and caveats:

- Model Call Log content is kept only for an Admin's own chat, so the `/run` User was made an Admin for the second Conversation.
- Move Outcomes and Personal Stickers did not run in the `/run` (no Reply Plan moves, no stickers); they use the same `to_transcript_lines` and mypy holds them to the required argument.
- The test checks two end steps, not all six; the rest share the helper.

## Completion

- Completed: 2026-11-24
- Commit: <to be filled in after merge>

