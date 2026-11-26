# 27 — Four reply-path faults a User can meet today

Status: completed
Track: shared
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md`. Findings from `20-findings-for-the-owner.md` (sections 02, 03 and 09), triaged with the owner on 25 Nov 2026 as high risk: each one can reach a real User now, with Pattern sharing on or off. Read `docs/message-pipeline/README.md` before planning.

## Why

Production is live with one real User. Each fault below either shows them something broken, tells them something false, or breaks a boundary they set.

## What to fix

**A. A tool call is sent to the User as plain text** (20 → 03).
In Eval Run 2eb36fca, deepseek-flash wrote `<tool call>` and `<function=change_directness>…` into its reply instead of calling the tool. The User got the markup as messages and the setting didn't change.

- In the chat model adapter, catch a reply that holds tool-call markup. Retry the call once; if the markup is still there, strip it. That markup is never sent to a User.
- Pure function for "does this text hold tool-call markup", with tests.

**B. Zeph says a setting changed when it didn't** (20 → 03).
`more-direct` passed 1 of 3 and `gentler` 1 of 2 in the Settings Eval. In a live run "could you go easier on me…" got "you're on gentle now" with the setting still on direct.

- First try what issue 03 suggested: the Reply with thinking on, or a stronger reply model, for replies that offer settings tools. Compare on the two cases, 3 tries each (about S$0.05).
- If the model still can't be trusted, add a code guard: when a reply offered settings tools, called none, and says a setting was changed, don't send that claim (retry once with the tool call forced, or drop the claim). Pick the simplest that passes the cases and say which in Comments.

**C. A topic the User asked to drop can come back** (20 → 02).
A dropped Curiosity is never offered again, but the Reply Plan and its Get curious questions aren't told which topics were dropped.

- Show the Reply Plan the User's dropped topics as "don't ask about".
- This reloads `reply_plan_prompt`. Don't add a migration that overwrites Admin edits: issue 28 changes how prompts reload, so do this part after 28, or follow 28's rule by hand.

**D. A picked Curiosity is marked raised even when the reply never asked it** (20 → 02 and 09).
Seen 3 of 9 times in a live run. The Curiosity is used up, and a Prediction follow-up that was picked but not asked is not asked again in its window, so the Prediction is dropped.

- After the reply, check whether the picked Curiosity was really asked, the same way the Woven-in Check-in is taken back when the reply left it out. Mark it raised only when it was asked; otherwise leave it waiting.
- One small model call per reply that picks a Curiosity. Prediction follow-ups go through the same check.
- Confirm in the running app that an unasked Curiosity is no longer read as "brushed off" by the next Reply Plan (commit 55c03b8 told the model to answer null, never seen live).

## Acceptance criteria

- [x] A reply holding tool-call markup is retried once and the markup never reaches the User; a test was red before and is green after
- [x] `more-direct` and `gentler` pass 3 of 3 in the Settings Eval, or a code guard stops "it's done" being sent when no tool was called; Comments say which and show the runs
- [x] The Reply Plan is shown the User's dropped topics, and in the running app a follow-up question does not go back to a dropped topic
- [x] A Curiosity the reply did not ask stays waiting and can be offered again; one that was asked is marked raised
- [x] A Prediction follow-up that was picked but not asked is still waiting afterwards
- [x] An unasked Curiosity does not count as a brush-off toward backing off
- [x] The owner was shown the estimate before each Eval run
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and `pytest`, `ruff`, `ruff format` and `mypy` pass

## Where to start

- Curiosities: `src/companion/core/curiosities.py` (`settle_curiosities` is in `core/reply_plan.py`), pace in `core/curiosity_pace.py`.
- The Woven-in Check-in check to copy from: see "Woven-in Check-in" in `docs/message-pipeline/README.md`.
- Settings tools: `reply_settings_instructions` in `src/companion/seed/platform_settings.yaml`; Settings Eval cases `more-direct` and `gentler`.
- Chat model adapters: `src/companion/adapters/` (the OpenRouter chat model).

## Out of scope

- The two never-Need findings (20 → 01): let go by the owner unless seen in real chats.
- Curiosity Check-ins and backing off: issue 30.

## Comments

### 25 Nov 2026: what was built

**A. Tool-call markup.** Both chat model adapters (OpenRouter, which prod uses, and DeepSeek) catch a reply that holds tool-call markup when tools were offered. The model is asked again, once per answer. Markup still there is taken out. The pure functions are `holds_tool_call_markup` and `without_tool_call_markup` in `adapters/chat_tools.py`. A reply left empty fails like any empty reply, so the User gets the reply-failed message.

**B. "It's done" with nothing done: a code guard, not a model change.** Which was picked and why:

- Run 1 (Eval Run 2a7a1577, 2 cases, 3 tries, 3 Variants) showed what the Reply's first draft does:

  | Variant | First draft called the tool | Passed with the guard |
  | --- | --- | --- |
  | A: live (deepseek-flash, no thinking) | 5 of 6 | 5 of 6 |
  | B: Reply thinking on | 6 of 6 | 6 of 6 |
  | C: Reply on deepseek-v4-pro | 4 of 6 | 5 of 6 |

- Thinking on passed 3 of 3 on both cases. But settings tools are offered on every reply, so "thinking on for replies that offer settings tools" means thinking on for every reply. That is an Admin setting (`response_thinking`) with a cost and a wait on every reply, and 6 tries is a small sample. So it is left to the owner (see the findings file), and the guard was built. The stronger model was worse, not better.
- The guard: before a reply is sent, if it called no settings tool that changes something, one small yes/no call (`CLAIM_CHECK_PROMPT` in `core/chat_settings.py`, on the Check-in model, no thinking) reads it. If it says or promises a setting change, the reply is written once more, shown its draft and told to call the tool or not say it. If the second one still says so, nothing of it is sent and the User gets the reply-failed message.
- In run 1 the guard caught all 3 false claims, but the second draft fixed only 1 of 3; the other 2 ended as the reply-failed message (no false claim sent). The note to the model was then made firmer and now shows it its draft.
- Run 2 (Eval Run eb03b46e, live settings, after the firmer note): **`more-direct` 3 of 3, `gentler` 3 of 3.** In 2 of the 6 the first draft made the claim with no tool, the guard caught it and the second draft called `change_directness`.
- Cost of the guard: one small model call on every reply that calls no settings tool.

**C. Dropped topics.** On every reply, code reads every Curiosity the User asked to drop and shows them to the Reply Plan ("They asked you to drop these. Never ask about them or bring them up, not in a question of your own or a Move that asks one either, unless they bring one up themselves in their latest message"). The Reply is told them too, with its level 1 boundaries, since the Reply words the Get curious question. **No prompt was changed and there is no migration**: the rule is in the text code builds, so it holds whatever `reply_plan_prompt` an Admin saved (prod's is edited).

**D. The asked check.** Once the reply is sent, one small yes/no call per picked Curiosity (`ASKED_CHECK_PROMPT` in `core/curiosities.py`) reads the reply. Only one that was asked is marked raised. One left out stays waiting, doesn't count toward the limits or the pace, and is never shown to the next Reply Plan as awaiting a reaction, so it can't be read as brushed off. Prediction follow-ups go through the same check. A failed or unreadable check counts as asked, so a User is never asked the same thing twice because a check failed. The Reply Plan shape's "Curiosity asked" now says what the check found.

Also: two new steps in the Model Call Log ("Curiosity asked check", "Settings claim check"), with labels on the Dashboard (unit tests only, no browser check; no criterion is about the Dashboard). The load-test chat model answers both checks. `docs/message-pipeline/README.md` and the Curiosity term in `CONTEXT.md` are updated.

### Eval runs and what the owner was shown

The owner was asked before any run and picked "Run both". Shown: run 1 about S$0.09 (18 cases), run 2 about S$0.02 (6 cases), about S$0.11 in all. **Real cost: S$0.20 and S$0.05, S$0.25 in all**, more than twice the estimate. The estimate was rough because the two cases had never run and one Variant used a dearer model (logged in the findings file).

### Evidence (`/run`, worktree stack, 25 Nov 2026)

The chat checks ran the real app (the Eval `InProcessCompanion`) in the worktree's backend container, on the worktree's Eval database, with real model calls through OpenRouter. Swapped: the chat channel (it records texts), and one HTTP transport that can hand the Reply model's next answer a fixed text, to force the rare cases. Everything after that answer was real. Run twice: before the review fixes and again on the final code. The lines below are from the final run.

- **A.** The Reply's first answer was forced to `<tool call>…<function=change_directness>…</tool_call>`. The adapter asked again (log: "A model wrote a tool call as text; asking it again"), the real model called `change_directness`, the User got "Done — set to blunt…" with no markup, and directness was `direct`. Forced twice in a row, with words around the second ("okay, straight talk from here."): the markup was cut and nothing with `<` was sent. Red-then-green tests: `tests/adapters/test_chat_tools.py`, and the new tests in `test_openrouter_chat_model.py` and `test_deepseek_chat_model.py`.
- **B.** First draft forced to "of course. you're on gentle now, I'll go easy". Steps: `reply`, `settings_claim_check -> yes`, `reply tools=[change_directness]`. The User got "Done — I've set it to gentle…" and directness went `balanced` → `gentle`. Same result 5 times out of 5 with the firmer note. Ordinary chat ("long day at work, my feet hurt"): `settings_claim_check -> no`, reply sent as written. Plus the two Eval runs above.
- **C.** A User with one dropped Curiosity ("How did the talk with your dad about the loan go?", reaction `asked_to_drop`). All three Reply Plans were shown it under the "They asked you to drop these" rule. "family stuff has been on my mind a lot this week" got "what's been coming up?"; "money's been tight too" got a Get curious question about what tight looks like; "ask me anything, I'm bored" got a question about the new job. No reply named the dad or the loan.
- **D, left out.** The Reply Plan picked "How did the driving test go?" and the reply was forced to "sounds like a calm evening. enjoy it". `curiosity_asked_check -> no`; the Curiosity stayed `waiting` with no `raised_at`; the shape said Curiosity asked: false.
- **D, not a brush-off.** On the User's next text ("meh, nothing much going on") the Reply Plan was not shown "was meant to ask", was offered the Curiosity again, and `curiosity_taken` stayed null. No reaction was saved.
- **D, asked.** That next reply (real) asked "how did the driving test go, by the way?". `curiosity_asked_check -> yes`; the Curiosity is `raised`.
- **Prediction follow-up.** A User with a shared Pattern (CONF.AVOID.BELONG), an open Prediction 8 days old and its follow-up Curiosity. Picked and forced out of the reply: check `no`, still `waiting`. On the next message it was offered and picked again, and this time the **real** Reply left it out by itself; check `no`, still `waiting`, the Prediction still open.
- **Checks.** `uv run pytest`: 2526 passed. `ruff check`, `ruff format --check`, `mypy`: clean. Web: `pnpm lint`, `format:check`, `typecheck` clean, `pnpm test` 989 passed.

### Review

Standards and spec reviews were run. Fixed: a reply written twice now drops the sticker, photo or closing text its first draft picked; an asked-check answer that can't be read counts as asked; a reply that only listed memories is still checked for a false claim; a bare `<function>` tag goes with what is inside it; a docstring. Left as they are, and logged in the findings file where they are risks: the three yes/no checks share a shape but live in three files; a rewrite can run a non-settings tool (web search) twice.

## Completion

- Completed: 2026-11-25
- Commit: 1ce67a12 (merge of `pattern-27-replies-that-mislead` into main; work commits 322202b5, d4085399, c9783639, bd7ddd04)

