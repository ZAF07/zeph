# 01 — Reply follows a strict priority order

Status: completed
Lane: A
Blocked by: None - can start immediately

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

The Reply's instructions stop being a flat stack. They are put together in a fixed priority order, with a line telling the model that when two clash the higher one wins:

1. Safety, privacy and the User's own boundaries (e.g. a Thread they asked Zeph to drop).
2. What they just asked or need right now.
3. The Need, the Moves and the rest of today's guidance from the Understanding.
4. What was picked from memory, used accurately; nothing suspected stated as fact.
5. The Persona's voice (it stays in front of the instructions, as today; the order line says where it ranks).
6. Optional extras: a Woven-in Check-in, a Curiosity to raise, Knowledge passages, a sticker, a Shared Photo. Each is to be left out if it doesn't fit what the User needs right now.

The Woven-in Check-in is no longer phrased as an order ("Weave it into this reply"): it becomes an optional extra the reply may leave out. If the reply leaves it out, it is not logged as sent and stays due (it is taken back like a failed reply's). Everything else about the reply path stays as it is; the Reply Plan comes in 05.

This alone stops the review's worst moment: a "present-moment pause" Check-in overriding "give one short, real read".

User stories covered: 19, 20, 21.

## Acceptance criteria

- [x] The Reply's instructions list their sections in the priority order above, with the clash rule stated once
- [x] A due Woven-in Check-in reaches the Reply as an optional extra, never as an order
- [x] A Woven-in Check-in the Reply leaves out is not logged as sent and stays due; one the Reply uses is logged as today
- [x] A direct question in the Message is answered before any optional extra (tested through the instructions the scripted model receives)
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

None - can start immediately

## Comments

### 19–20 Nov 2026: implementation and evidence

**What was built**

- `write_instructions` in `core/response_composition.py` puts the Reply's instructions together as:
  - the Persona (voice) and `response_prompt`;
  - then `PRIORITY_ORDER`, which lists levels 1–6 (5 = "Your voice, as described at the top") and gives the clash rule once ("When two things clash, the higher one wins");
  - then one section per level that has something in it:
    - 1: data deletion note and Threads to leave alone;
    - 2: "If their message asks you something directly, answer it first, before anything else", plus the tools' instructions and Features not available;
    - 3: the Understanding's guidance;
    - 4: memory;
    - 6: Woven-in Check-in, Curiosities and Knowledge.
- The Understanding's guidance is now a `ReplyGuidance` (boundaries / plan / curiosities, in `core/reply_tools.py`). The Threads to leave alone are split out by `format_threads_left_alone`.
- The Woven-in Check-in is an optional extra ("Bring it up only if it fits what they need right now; if it doesn't, leave it out and it will wait") with a `bring_up_check_in` tool (`WovenCheckInOffer`). `ReplyService` takes it back if the Reply didn't call the tool, the same way as for a failed reply, and only once.

**Per criterion**

1. Priority order and clash rule once: `test_the_sections_come_in_priority_order_with_the_clash_rule_once` and `test_the_composer_puts_each_input_at_its_level` (`tests/test_reply_priority_order.py`). Live: every reply's sections came in order `2, 3, 6`, and level 1 was empty in those chats.
2. Optional extra, never an order: `test_a_due_check_in_reaches_the_reply_as_an_optional_extra_not_an_order`. Live: "Weave it into this reply" was in the instructions 0 times; the Check-in sat under "## 6. Optional extras: use one only if it fits what they need right now".
3. Left out → not logged and stays due; used → logged as today. Tests: `test_a_check_in_the_reply_leaves_out_is_not_logged_and_stays_due` (left out, then logged on the next reply that uses it), and the existing logging tests now script `bring_up_check_in`. Live, left out: after a direct question with "A present-moment pause" offered, `check-ins logged: []` and the Due Time didn't change. **Live, used: not shown.** The real Reply never called the tool, and twice it brought up the follow-up without calling it, so that one wasn't logged and stayed due. **The user chose to leave that bug to issue 09.** The findings are written up under 09's Comments, with a new criterion there.
4. Direct question before any optional extra: `test_a_direct_question_is_answered_before_any_optional_extra` checks that the scripted model's instructions have `ANSWER_THE_QUESTION` before the level 6 heading, and the heading before the Check-in note. Live: "honestly what do you think I should do?" with a pause offered got a full view and a next step ("Take it, but not as offered… ask what the hours actually look like…"), and no pause.
5. Docs: in `docs/message-pipeline/README.md`, step 6's "Today" note was updated, step 7's became a "Built (19 Nov 2026)" note, and the Reply rows in both prompt tables were updated. The `CONTEXT.md` Woven-in Check-in entry now says the reply gets it as an optional extra and that one left out isn't logged and stays due.
6. Checks after rebasing on main (9b5ba28): `uv run pytest` gave 1349 passed; `ruff check` passed; `ruff format --check` reported 530 files already formatted; `mypy src` found no issues in 190 source files.
7. `/run`: the worktree stack (`ai-chat-companion-mp-01`), with the real app (`create_app` with the real builders) inside the backend container, real repositories, and the real DeepSeek Reply and Understanding. Swapped out: the chat channel (records sends), the scheduler and timer (manual), and the Check-in model's answer, forced to "weave in" so that every reply was offered a Check-in. The User is an Admin, so full content was kept. Runs 19–20 Nov 2026:
   - a light opener;
   - the job question with "A present-moment pause" offered: answered, pause left out, not logged, still due;
   - "ask me something" with a fitting follow-up offered: the Reply asked its own question ("Get curious" lead Move, level 3 over 6), not logged;
   - "was there something you were going to ask me?": "Oh yeah — your sister. How did the interview go?" with no tool call, so not logged. This is the gap handed to 09.
   - A sanity check showed the Reply does call tools the User asks for (`pause_check_ins`).

**Caveats**

- Curiosities are now optional extras, but `CuriosityRaiser.mark_raised` still marks the chosen ones raised even if the Reply skipped them. Left for 05, where the Reply Plan picks what the reply uses.
- The fixed texts (the order line, headings, "answer it first") are in code, not Admin settings.

## Completion

- Completed: 2026-11-20
- Commit: 9588059 "Merge message pipeline issue 01: the Reply's instructions follow a strict priority order (safety and boundaries, what they just asked, today's guidance, memory, voice, optional extras) with one clash rule and an 'answer a direct question first' line; a due Woven-in Check-in is an optional extra with a bring_up_check_in tool and is taken back when the Reply leaves it out; the unreliable tool signal is handed to issue 09"
- Branch commits: 8cf4a30 (priority order and optional Check-in), 02d0195 (review fixes), 9f88dee (hand-off to 09), then the archive commit

