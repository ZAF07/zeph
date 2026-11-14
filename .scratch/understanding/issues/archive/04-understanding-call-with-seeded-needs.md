# 04 — Understanding call with seeded Needs

Status: completed

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

- [x] Every Message gets an Understanding before the reply; the memory-retrieval call is gone
- [x] The reply call's instructions include the picked Need's "how to reply" and only the chosen Memory Items plus "always include" ones
- [x] The next Understanding in the Conversation sees the earlier ones
- [x] The probe rule reaches the reply only for a standout mood with an unknown cause, and not after a probe in the previous reply
- [x] Fallback on unknown Need, unreadable form and failed call, each tested
- [x] Understanding prompt and model editable on the Prompts and Models page
- [x] Saved Understandings are removed with their Message by retention and both deletions
- [x] Tests at the webhook seam with the scripted chat model; existing tests updated only where they scripted memory retrieval
- [x] `pytest`, `ruff`, `ruff format --check`, `mypy`, `pnpm` checks pass
- [x] `/run`: a vent and a request for advice in the worktree get replies shaped by different Needs (seen in the Admin's own trace)

## Blocked by

- `.scratch/understanding/issues/02-reply-service-in-core-remove-langgraph.md`
- `.scratch/messages/issues/archive/01-answer-texts-in-a-row-as-one-message.md` (completed 14 Nov 2026)

## Comments

- Branch `understanding-04-understanding-call`, worktree `ai-chat-companion-understanding-04` (ports 3200/8200/5632).
- Plan:
  - `needs` table (platform data, seeded once from `seed/needs.yaml`, like Check-in Kinds) and `understandings` table (Message, Conversation, User, the form, the Need by name, whether the reply was asked to gently ask why, when made). Its message and Conversation links cascade, so Message Retention, Delete My Data and Account Deletion remove it with the Message. Migration 0028; it also drops old `memory_picking` Model Call Log rows (platform not live).
  - New core `UnderstandingService`: one cheap call (`understanding_model`, `understanding_prompt`) given the Needs, Goals, Memory Category names with items (plus "Shared Photos" as before), newest Summaries, this Conversation's earlier Understandings, the Conversation and the local time and weekday. Reads the JSON form; unknown Need → fallback Need; unreadable or failed → fallback form. Saved before the reply call.
  - `MemoryRetrieval` no longer calls a model: it fetches the Memory Items of the categories the Understanding chose, plus "always include", the newest Summaries and Shared Photos when picked. The memory-retrieval prompt and model settings go.
  - The reply gets a Need section: the Need's name and "how to reply", the nuance and mood. The Admin-editable "ask why" note is added only when intensity is high, `cause_known` is false and the previous Understanding in the Conversation didn't already ask.
  - Prompts and Models: "Memory retrieval" card becomes "Understanding". Model Call Log step `memory_picking` becomes `understanding`.
- Decisions: a "standout mood" means intensity `high`. "Not while venting" lives in the wording: the Understanding prompt says a vent means the cause is known, and the Admin-editable "Gently ask why" note (`reply_ask_why_note`, on the Response composition card) says to just listen when they vent. A code rule on the Need's name was not used, since Admins can rename Needs. `asked_why` on a saved Understanding means the note reached the reply.
- The Understanding is linked to the Message's newest text; its texts arrive seconds apart, so Message Retention removes them together.
- The Understanding is saved before the reply call, so a failed reply still leaves it for the next one.
- Migration 0028 also deletes old `memory_picking` Model Call Log rows, as that step no longer exists and its value can't be read any more (platform not live).
- Follow-up, not in this issue: CONTEXT.md says the Model Call Log keeps each decision's shape for every User (e.g. the Need picked). Today the picked Need shows only in full content (Admins and Evals). A content-free "decision" field would need a column, the API and the trace page.

## Evidence

- **Understanding before every reply, memory-retrieval call gone:** `tests/test_understanding.py::test_every_message_gets_an_understanding_before_the_reply` (call order `safeguard, understanding, reply`; it sees every Need's "when it fits" and "Wednesday 11 Nov 2026, 17:00" in Asia/Singapore). `MemoryRetrieval` no longer calls a model (`src/companion/core/memory_retrieval.py`); the `memory_retrieval_*` settings and the `memory_picking` step are gone.
- **Reply gets the Need's "how to reply" and only chosen + "always include" items:** `test_the_reply_follows_the_picked_needs_how_to_reply`; `tests/test_memory_retrieval.py::test_reply_gets_picked_and_always_include_memories_and_recent_summaries`. Goals reach the Understanding: `test_the_understanding_sees_the_users_goals`.
- **Next Understanding sees earlier ones:** `test_the_next_understanding_in_the_conversation_sees_the_earlier_ones`.
- **Probe rule:** `test_a_standout_mood_with_an_unknown_cause_asks_the_reply_to_gently_ask_why`, `test_no_gentle_ask_when_the_cause_is_known_or_the_mood_is_mild`, `test_the_gentle_ask_is_not_made_twice_in_a_row` (asks, doesn't, asks).
- **Fallbacks:** `test_an_unknown_need_falls_back_to_the_fallback_need`, `test_an_unreadable_form_falls_back_to_the_fallback_need`, `test_a_failed_understanding_still_replies_with_the_fallback_and_shows_in_the_log` (reply sent with the fallback Need, newest Summaries and "always include" items; the trace shows `understanding` with `TimeoutError`).
- **Settings:** `test_a_changed_understanding_prompt_and_model_are_used_for_the_next_message`; `tests/test_admin_settings.py` lists the "Understanding" card (prompt, model, Shared Photos description) and the "Understanding" note group on Response composition. The Dashboard's Prompts and Models page is built from that list.
- **Removed with the Message:** `test_message_retention_removes_understandings_with_their_messages`. `tests/test_data_deletion.py` checks every table with a `user_id` column (now `understandings` too) has rows before and none after, for Delete My Data and Account Deletion. Saved with its Message and the Need by name: `test_each_understanding_is_saved_with_its_message_and_the_need_by_name`.
- **Existing tests:** changed only where they scripted memory retrieval (`script_retrieval` → `script_understanding`), plus where the new `understanding` step now shows in call orders, Model Call Log steps and row counts, and per-User table checks that every reply adds to (`tests/test_settings_via_chat.py`). One exact-instructions check in `tests/test_knowledge.py` now asserts no Knowledge intro instead.
- **Checks (after rebase on main, with Messages issues 02 and 03):** `make check`: `ruff check` all passed; `ruff format --check` 305 files already formatted; `mypy` no issues in 111 files; `pytest` 791 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean; `pnpm test` 50 files, 343 tests passed.
- **/run in the worktree** (ports 3200/8200): a Telegram send from a fake chat fails in a worktree, so the real app ran inside the backend container with the real database (Needs seeded by the real startup) and DeepSeek, and only the chat channel swapped for a recorder. An Admin sent a vent, "ugh my manager took credit for my work AGAIN…" → Understanding `Be heard`, mood "fed up, frustrated" (medium). The reply listened: "God. Again. That's infuriating…" / "How did you handle it in the moment?". In a new Conversation they asked "should I raise it with her directly or go to her boss? what would you do?" → `Advice`, and the reply gave a view: "Directly first. Going over her head…". Each Admin trace was `safeguard, understanding, reply` with full content, and each reply's instructions held "What they need from you right now: Be heard." / "…: Advice." with that Need's "how to reply".
- **/code-review:** Standards found no hard violations in `src/`. Fixed: the test's inline `type: ignore` (uses the `engine` fixture now), and `compose(understanding=…)` renamed to `reply_guidance`. Kept as they are: the form's later fields (the issue asks for them), the Need stored by name (the PRD asks for that), and the seed loader's likeness to the other seed loaders. Spec: fixed venting (see the decisions above). The deletions were already covered (above). Old `memory_picking` rows are deleted on purpose (above).

## Completion

- Completed: 2026-11-14
- Commits: `4e3bd7b` (Understanding call with seeded Needs), `55fd231` (review fixes: `reply_guidance` name, a vent counts as a known cause, test uses the `engine` fixture), `298c78e` (issue archived, CONTEXT.md)
- Merged into main: `6b10654` (branch `understanding-04-understanding-call`, pushed to origin)
