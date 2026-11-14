# 04 — Understanding call with seeded Needs

Status: ready-for-agent

## Parent

`.scratch/understanding/PRD.md`

## What to build

Before every reply the Companion makes an **Understanding** (`CONTEXT.md`). One cheap model call replaces today's memory-retrieval (category picking) call, so a reply still takes two model calls.

- **Needs** become platform data, seeded with Be heard, Think it through, Advice, Accountability, Ask more (the fallback, undeletable) and Just chatting, each with "when it fits" and "how to reply". (The admin page is issue 05.)
- The Understanding call sees: the Admin-editable Understanding prompt, the Needs, Goals, the names of Memory Categories the User has items in, the newest Conversation Summaries, this Conversation's earlier Understandings, the recent Conversation, and the time and weekday in the User's time zone.
- It returns a fixed-shape form: `need`, `nuance`, `mood`, `intensity` (low/medium/high), `cause_known`, `memory_categories`, plus `bring_up`, `left_alone`, `look_up_past`, `knowledge` and `threads_touched` (empty until later slices use them).
- The reply call gets the picked Need's "how to reply", the nuance and mood, and the chosen Memory Items ("always include" ones always). When the mood stands out and `cause_known` is false, the reply instructions ask the Companion to gently ask why, not while the User is venting and not twice in a row.
- Each Understanding is saved with its Message, the Need stored by name. Removed with the Message (Message Retention, Delete My Data, Account Deletion).
- Unknown Need or unreadable form → the fallback Need. Failed call → the reply still goes with the fallback Need, newest Summaries and "always include" Memory Items; the failure shows in the Model Call Log if issue 03 has landed.
- Understanding model (start `deepseek-chat`) and prompt are Admin settings on the Prompts and Models page.

## Acceptance criteria

- [ ] Every Message gets an Understanding before the reply; the memory-retrieval call is gone
- [ ] The reply call's instructions include the picked Need's "how to reply" and only the chosen Memory Items plus "always include" ones
- [ ] The next Understanding in the Conversation sees the earlier ones
- [ ] The probe rule reaches the reply only for a standout mood with an unknown cause, and not after a probe in the previous reply
- [ ] Fallback on unknown Need, unreadable form and failed call, each tested
- [ ] Understanding prompt and model editable on the Prompts and Models page
- [ ] Saved Understandings are removed with their Message by retention and both deletions
- [ ] Tests at the webhook seam with the scripted chat model; existing tests updated only where they scripted memory retrieval
- [ ] `pytest`, `ruff`, `ruff format --check`, `mypy`, `pnpm` checks pass
- [ ] `/run`: a vent and a request for advice in the worktree get replies shaped by different Needs (seen in the Admin's own trace)

## Blocked by

- `.scratch/understanding/issues/02-reply-service-in-core-remove-langgraph.md`
- `.scratch/messages/issues/archive/01-answer-texts-in-a-row-as-one-message.md` (completed 14 Nov 2026)
