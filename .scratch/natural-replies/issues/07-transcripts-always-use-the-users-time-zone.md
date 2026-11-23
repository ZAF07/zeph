# 07 — Transcripts always use the User's time zone

Status: ready-for-agent
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

- [ ] The helpers have no `time_zone` default; mypy passes on `src/`.
- [ ] Every caller passes the User's time zone.
- [ ] Test: a Replied-to Text sent at 23:30 UTC shows the next day in the transcript of a Conversation-end step (e.g. Life Threads keeping) for a User in Singapore (fake chat model prompts); all Python checks pass.
- [ ] `/run`: in a worktree, a User in Singapore replies to a text sent near UTC midnight, the Conversation ends (shift timestamps, don't wait), and the end step's prompt in the Model Call Log shows the Singapore day.

## Blocked by

None - can start immediately.

## Comments
