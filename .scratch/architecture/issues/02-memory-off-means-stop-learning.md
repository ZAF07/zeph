# 02 — User Memory off means "stop learning, keep using"

Status: ready-for-agent

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

- [ ] With either switch off, replies and Check-ins still use existing Memory Items, Conversation Summaries and Goals
- [ ] With either switch off, nothing new is saved after a Conversation or from onboarding
- [ ] Home shows Goals and Recently remembered whichever switch is off, with the right note
- [ ] Both notes are platform settings, seeded, editable in the admin area, and shown as set
- [ ] Tests for each switch combination; backend and Dashboard checks pass
- [ ] `/run`: with each switch off, a reply still uses a saved memory, nothing new is saved, and Home shows the note

## Blocked by

None.
