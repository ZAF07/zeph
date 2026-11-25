# 27 — Four reply-path faults a User can meet today

Status: ready-for-agent
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

- [ ] A reply holding tool-call markup is retried once and the markup never reaches the User; a test was red before and is green after
- [ ] `more-direct` and `gentler` pass 3 of 3 in the Settings Eval, or a code guard stops "it's done" being sent when no tool was called; Comments say which and show the runs
- [ ] The Reply Plan is shown the User's dropped topics, and in the running app a follow-up question does not go back to a dropped topic
- [ ] A Curiosity the reply did not ask stays waiting and can be offered again; one that was asked is marked raised
- [ ] A Prediction follow-up that was picked but not asked is still waiting afterwards
- [ ] An unasked Curiosity does not count as a brush-off toward backing off
- [ ] The owner was shown the estimate before each Eval run
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and `pytest`, `ruff`, `ruff format` and `mypy` pass

## Where to start

- Curiosities: `src/companion/core/curiosities.py` (`settle_curiosities` is in `core/reply_plan.py`), pace in `core/curiosity_pace.py`.
- The Woven-in Check-in check to copy from: see "Woven-in Check-in" in `docs/message-pipeline/README.md`.
- Settings tools: `reply_settings_instructions` in `src/companion/seed/platform_settings.yaml`; Settings Eval cases `more-direct` and `gentler`.
- Chat model adapters: `src/companion/adapters/` (the OpenRouter chat model).

## Out of scope

- The two never-Need findings (20 → 01): let go by the owner unless seen in real chats.
- Curiosity Check-ins and backing off: issue 30.

## Comments
