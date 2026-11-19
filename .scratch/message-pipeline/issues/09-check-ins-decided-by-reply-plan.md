# 09 — Woven-in Check-ins decided by the Reply Plan

Status: ready-for-agent
Lane: A
Blocked by: 07

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

The separate Woven-in Check-in model call is retired. When a Check-in is due mid-Conversation, the Reply Plan is given the due Check-in Kinds without fixed behaviour and weighs one against everything else the reply could do: it chooses whether a Woven-in Check-in fits now, which Kind, and a note, or none. It is never woven in while the User is struggling, nor while paused unless an Admin asked with Check in Now (keep these as code rules).

Everything else about Woven-in Check-ins works as today: saved, logged as sent with its Kind and marked woven in (and the Admin for Check in Now), moving the Due Time, taken back when the reply fails or (from 01 and 03) leaves it out or is dropped, going out on its own if no reply weaves it in before the Conversation ends. The `woven_check_in_prompt` setting is removed by migration. Check-ins sent on their own keep their own decision and prompt.

User stories covered: 19, 20, 64.

## Acceptance criteria

- [ ] No separate woven-in Check-in model call is made; the Reply Plan's input holds the due Kinds when one is due and nothing when none is
- [ ] A Reply Plan choosing a Kind makes a Woven-in Check-in that reaches the Reply as an optional extra and is logged as today
- [ ] Struggling, paused and Check in Now rules still hold
- [ ] The woven-in Check-in prompt is gone from the settings page and the database
- [ ] A Woven-in Check-in the Reply brings up is always logged as sent, and one it leaves out never is, shown live with the real Reply model (see the 19 Nov 2026 note from 01 under Comments)
- [ ] Existing Woven-in Check-in tests pass, rewritten for the Reply Plan where they scripted the old model
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 07 — Zeph forms a Read from the Outlook (`.scratch/message-pipeline/issues/07-read-from-the-outlook.md`)

## Comments

### 19 Nov 2026: handed over from 01, the Reply's "did I use the Check-in?" signal isn't reliable

The user decided to move this from 01 to here.

**What 01 built.** A due Woven-in Check-in reaches the Reply as an optional extra (level 6 of the priority order), together with a `bring_up_check_in` tool (`WovenCheckInOffer` in `core/woven_check_ins.py`). The Check-in is saved before the reply, as before. If the Reply doesn't call the tool, `ReplyService` takes it back, the same way as for a failed reply, so it isn't logged and stays due. If it calls the tool, it is logged as today. Tests script the tool call (`tests/test_woven_in_check_ins.py`).

**What happened live** (worktree stack, real DeepSeek Reply model, Check-in model forced to say "weave in" so the Reply was offered one every time):

- First try, with the note shown and the instruction "...and call mention_check_in" at the end: in light chat the Reply wove in "A present-moment pause" ("the mug warm in your hands, the sofa giving under you") **without calling the tool**. So it was not logged and stayed due, and it could be offered again or go out on its own afterwards. The User would get it twice.
- With the note hidden behind the tool (the tool returned what to bring up): over 8 offers the Reply never called it and never brought one up. It can't judge fit from the Kind name alone.
- With the note shown and "call bring_up_check_in first, before writing" (what shipped): over about 10 offers it never called the tool. Mostly it left the Check-in out, which is correct: for a direct question it gave a full answer and no pause, and with a "Get curious" lead Move it asked its own question. **But** once, when Maya asked "was there something you were going to ask me about?", it wrote "I was going to ask about your sister's interview", which is the offered follow-up, **without calling the tool**. So a Check-in that was used was not logged and stayed due.
- Context: across 85 real reply calls on the main stack, the Reply model only ever called tools the User asked for (web search, settings). It never once called an optional tool such as `send_sticker`. The Reply runs without thinking (`response_thinking` off).

**What this means for 09.** "Did the reply bring it up?" can't depend on the Reply calling an optional tool. Ideas raised with the user, none chosen yet:

1. A small checker model call after the reply: given the reply and the Check-in note, answer yes or no. It's reliable, but it costs one extra call per offer.
2. Have the Reply Plan's choice count as the decision, with the Reply told to follow it, accepting that it is then an order again. Check this against decision 10 in the README.
3. A hidden text marker the Reply adds and code strips. Untested: the model may forget it, or it may leak to the User.

Until this is fixed, most due Check-ins go out on their own after the Conversation, and a rare used-but-unlogged one can repeat.

