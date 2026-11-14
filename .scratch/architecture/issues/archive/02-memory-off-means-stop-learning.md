# 02 — User Memory off means "stop learning, keep using"

Status: completed

## Parent

Architecture review, 14 Nov 2026, point 2 (Home Goals gating). Decided in a `/grill-with-docs` session. `CONTEXT.md` (User Memory) is already updated.

## What to build

Whichever switch is off (the User's own or the Admin's), the Companion stops learning but keeps using what it already has. The Admin's switch has the final say. The User can always see and delete their memories on the Dashboard.

- Keeps working while off (change): memory recall for replies (`core/memory_retrieval.py`), memories and Goals in Check-ins (`core/check_ins.py`).
- Stays stopped while off (no change): saving after a Conversation (`core/post_conversation.py`), saving onboarding answers (`core/user_memory.py`).
- Home always shows Goals and Recently remembered, with a note when memory is off.
- Two new admin-editable platform settings (ADR-0004), seeded from data files, editable on the admin settings page, sent by the backend with the User's data so the Dashboard holds no wording of its own:
  - `memory_paused_note` (User's switch off): "**Memory is paused.** Zeph won't learn anything new, but still uses what it already knows about you. Delete any memory you don't want Zeph to use."
  - `memory_not_available_note` (Admin's switch off): "**Memory isn't available on your account.** Zeph won't learn anything new, but still uses what it already knows about you. Delete any memory you don't want Zeph to use."
- Shown on Home, the Memories page and next to the switch. Replaces `HomeMemoryPausedNote`'s hardcoded text.

## Decisions

- Both switches mean the same thing: stop learning, keep using (if anything is saved).
- Only these two Dashboard notes become editable now; a general "Dashboard wording" pattern waits until more text needs it.
- Later, not now: deleting memories in chat, depending on tier (tiers don't exist yet).
- Note: the Photo Viewing switch is separate and unchanged (with it off, Shared Photos aren't used).

## Acceptance criteria

- [x] With either switch off, replies and Check-ins still use existing Memory Items, Conversation Summaries and Goals
- [x] With either switch off, nothing new is saved after a Conversation or from onboarding
- [x] Home shows Goals and Recently remembered whichever switch is off, with the right note
- [x] Both notes are platform settings, seeded, editable in the admin area, and shown as set
- [x] Tests for each switch combination; backend and Dashboard checks pass
- [x] `/run`: with each switch off, a reply still uses a saved memory, nothing new is saved, and Home shows the note

## Blocked by

None.

## Comments

- Built test-first: the new backend tests (replies, Check-ins and Home with each switch off, the two notes, the admin settings) and the Dashboard tests were red before the code changed, then green.
- Keeps using while off: the User Memory gate was removed from `MemoryRetrieval.recall` and `CheckInService._memory`; `describe_check_in` drops the "User Memory is off" line. Saving still stops: `post_conversation.py` and `UserMemoryService.remember_onboarding` are unchanged.
- Shared Photos are part of User Memory, so replies now still use them while memory is off (Photo Viewing still decides on its own). `tests/test_send_photo_back.py` was flipped to match.
- Notes: `memory_paused_note` and `memory_not_available_note` are seeded in `platform_settings.yaml`, editable on Platform settings, and picked in core by `UserMemoryService.memory_note` (the Admin's note wins). The backend sends the picked note as `memory_note` on `/api/me` and `/api/home`. The Dashboard's `MemoryNote` (was `HomeMemoryPausedNote`) shows it on Home, Memories and by the switch on Account & privacy, with `**bold**` shown as bold. Existing databases get the new keys on start (the seed inserts missing keys only).
- Also changed: Home no longer hides memories when off, and `user_memory_enabled` was dropped from the Home response (nothing read it). Memory Items are no longer dimmed on Memories while off, since they are still used. The User Memory Feature description says "stops learning, still uses what it knows".
- Not changed, open question: Check-in Kinds keep their rule. With User Memory off, only Kinds "allowed without User Memory" are offered, and Kinds that send a Shared Photo aren't. So a Check-in sees the memories, but "A follow-up" and "A look back at a photo" stay blocked. The issue doesn't mention Kinds and CONTEXT.md's Check-in Kind entry still says this, so I left it. If "keep using" should cover these Kinds too, that's a follow-up issue.
- Checks after rebasing on `origin/main` (issue 01's ReplyGate): `ruff check`, `ruff format --check`, `mypy` ("no issues found in 97 source files"), `pytest` 609 passed (9 deselected evals); `pnpm lint`, `format:check`, `typecheck`, `vitest` 322 passed, `pnpm build` OK.
- `/run` (worktree stack on ports 3110/8110, real DeepSeek, signed-in Clerk test User, two saved memories: Preferences "Loves cold-water swimming at dawn" and Goals "Swim every morning before work"):
  - User's switch turned off with the Memories page switch: Memories and Home both showed "**Memory is paused.** Zeph won't learn anything new…", and Home still listed the Goal and both memories. A message posted to `/telegram/webhook` was recorded. Telegram refused the fake chat at "typing", so the app's real `MemoryRetrieval` was run in the backend container for that Conversation; it returned the Preferences memory. When the Conversation ended it was processed with no summary and no new Memory Items.
  - Admin's switch off for the User (User's own back on): Home showed the seeded "**Memory isn't available on your account.** …" note with memories listed. Recall for a new message returned both memories. After it ended: processed, still 0 summaries and the same 2 Memory Items.
  - Platform settings showed both notes with their seeded text. The "isn't available" note was edited and saved, and Account & privacy then showed the edited text in bold next to the disabled switch.
- `/code-review`: no hard standards violations. Fixed: tests for the Admin's switch off with the User's on, onboarding with the Admin's switch off, and Goals on Home; the unused Home field; simpler `memory_note`. The Check-in Kinds point is the open question above.

## Completion

- Completed: 2026-11-14
- Commit: to be filled in after merge

