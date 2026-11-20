# 09 — Woven-in Check-ins decided by the Reply Plan

Status: completed
Lane: A
Blocked by: 07

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

The separate Woven-in Check-in model call is retired. When a Check-in is due mid-Conversation, the Reply Plan is given the due Check-in Kinds without fixed behaviour and weighs one against everything else the reply could do: it chooses whether a Woven-in Check-in fits now, which Kind, and a note, or none. It is never woven in while the User is struggling, nor while paused unless an Admin asked with Check in Now (keep these as code rules).

Everything else about Woven-in Check-ins works as today: saved, logged as sent with its Kind and marked woven in (and the Admin for Check in Now), moving the Due Time, taken back when the reply fails or (from 01 and 03) leaves it out or is dropped, going out on its own if no reply weaves it in before the Conversation ends. The `woven_check_in_prompt` setting is removed by migration. Check-ins sent on their own keep their own decision and prompt.

User stories covered: 19, 20, 64.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- **Prompts & models** (reference `AdminPrompts`): the woven-in Check-in prompt is gone; nothing replaces it.
- **Model call trace** (reference `AdminModelCallTrace`): there is no Woven-in Check-in step. The Reply Plan step shows "Check-in Kinds offered" and "Check-in Kind chosen".
- **Shared references.** `AdminPrompts` also draws 05, 06 and 08; `AdminModelCallTrace` also draws 05, 07, 11 and 14. Build your part. The full PASS is due on whichever of those issues lands last; until then, record under Comments which parts still differ and which issue owns them.

## Acceptance criteria

- [x] No separate woven-in Check-in model call is made; the Reply Plan's input holds the due Kinds when one is due and nothing when none is
- [x] A Reply Plan choosing a Kind makes a Woven-in Check-in that reaches the Reply as an optional extra and is logged as today
- [x] Struggling, paused and Check in Now rules still hold
- [x] The woven-in Check-in prompt is gone from the settings page and the database
- [x] A Woven-in Check-in the Reply brings up is always logged as sent, and one it leaves out never is, shown live with the real Reply model (see the 19 Nov 2026 note from 01 under Comments)
- [x] Existing Woven-in Check-in tests pass, rewritten for the Reply Plan where they scripted the old model
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] Prompts & models and the trace match `AdminPrompts` and `AdminModelCallTrace`; full PASS if this is the last issue on them, otherwise the remaining differences are recorded under Comments
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

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


### Decision (20 Nov 2026): how "did the Reply bring it up?" is told

Asked the user, who chose option 1 from the note above: a small checker model call after the reply. It uses the Check-in model without thinking and a fixed yes/no prompt in code (`BROUGHT_UP_CHECK_PROMPT` in `core/woven_check_ins.py`), so there's no new Admin prompt and nothing new on Prompts & models. It runs only when the Reply Plan chose a Check-in and it was saved. A "no", a failed call or an unreadable answer takes the Check-in back (it stays due), so a Check-in is logged only when it is known to be sent. The `bring_up_check_in` tool is gone.

### Evidence (20 Nov 2026, branch `mp-09-check-ins-by-reply-plan`)

- **No separate Check-in model call; the Reply Plan gets the Kinds only when one may be offered.**
  - Code still decides (`WovenCheckIns.kinds_to_offer`, using the unchanged `may_weave_check_in`). Only then does `describe_message_for_reply_plan` add "A Check-in with them is due. Check-in Kinds you may weave in:" with the Kinds that have no fixed behaviour. Otherwise it adds nothing.
  - The Reply Plan answers `check_in: {"kind", "note"} | null`, read by `read_check_in_choice`: it must be an offered Kind (any case) with a note. A fallback Reply Plan chooses none.
  - Tests: `test_the_reply_plan_is_given_the_due_check_in_kinds_and_no_check_in_model_runs`, `assert_no_check_in_offered` in four rule tests, `test_a_check_in_due_mid_conversation_is_woven_into_the_reply_and_logged` (call order ends understanding → reply_plan → reply → brought_up_check), and the eval runner test (the first plan sees the due Check-in, the second, after it is sent, doesn't).
  - Live: every trace was safeguard → understanding → reply_plan → reply, plus "check_in" (the checker) only after a Reply Plan chose one. Not due: "Kinds offered in input: False", shape 0 / None.
- **A chosen Kind reaches the Reply as an optional extra and is logged as today.**
  - The Reply's level 6 gets "A Check-in with them is due. Bring it up only if it fits…" with the Kind and note, and no tool.
  - Saving, logging (sent, Kind, woven in, the Admin for Check in Now), moving the Due Time, taking back on a failed, dropped or partly sent reply, and going out on its own after the Conversation all use the same code as before. All existing tests for them pass.
  - Live (natural, no forcing): in light chat ("making pasta tonight…") the Reply Plan chose "A present-moment pause" with its own note. The Reply wrote "…that moment when the garlic hits the warm oil… worth a second of just standing there", the check said yes, it was logged as `('sent', True, 'A present-moment pause')` and the Due Time moved.
- **Struggling, paused and Check in Now rules hold.** Live, with every Reply Plan answer forced to choose "A follow-up":
  - "my manager screamed at me… crying in the toilets": struggling True, no Kinds offered, the forced choice was ignored, nothing logged.
  - Due but paused for a day: no Kinds offered.
  - Then an Admin's Check in Now while still paused: Kinds offered, brought up, logged with `requested_by` set.
  - Tests: the struggling, paused, before-due and Admin-off tests (each also scripts a choice, which is ignored), plus the four Check in Now tests.
- **The woven-in Check-in prompt is gone from the settings page and the database.**
  - Removed from `platform_settings.py`, the Check-ins card's extra prompts and the seed. Migration 0071 deletes the `woven_check_in_prompt` row and reloads `reply_plan_prompt`.
  - Tests: `test_the_woven_in_check_in_prompt_is_gone_from_the_settings` (not in core services or settings; saving it is refused) and `test_the_migration_removes_the_woven_in_prompt_and_reloads_the_reply_plan_prompt`.
  - Live: the worktree database is at 0071 with no `woven_check_in_prompt` row, and its `reply_plan_prompt` asks for `check_in`. In the browser, Prompts & models shows no woven-in prompt.
- **One the Reply brings up is always logged, and one it leaves out never is (real DeepSeek Reply model).** Forced "A follow-up" runs:
  - "can you recommend one good sci-fi book?": the Reply gave the book only. Check "no", nothing logged, Due Time unchanged.
  - "what's the difference between a latte and a flat white?": answer only. Check "no", nothing logged. This was repeated after the review fixes with the same result.
  - "ok what were you going to ask me?": "…how did your sister's interview go yesterday?" Check "yes", logged, Due Time moved. This happened in 4 separate runs, including the run after the review fixes.
  - Across all live runs the check agreed with my own reading of the reply every time (5 yes, 3 no).
- **Existing tests rewritten.** `tests/test_woven_in_check_ins.py` scripts the Reply Plan's `check_in` and the check's yes/no instead of the old model and tool (37 tests). Also updated: `test_reply_priority_order.py`, `test_eval_runner.py`, `test_model_call_log.py` and `test_moves_that_ask_a_question.py`. The three "told the reply already asks" tests became one test of the Reply Plan prompt, since the plan now sees its own question choices.
  - New tests: a failed check takes the Check-in back, and a shape saved by the old model shows as no shape.
- **One migration head:** `0071_check_ins_weighed_by_reply_plan.py` revises 0070, the newest on `main` (7f9fc64, unchanged on origin).
- **Docs.**
  - `docs/message-pipeline/README.md`: Built notes for step 6 (it weighs a due Check-in) and step 7 (optional extra plus the checker). The Today table's Reply Plan input, Reply row and checker row replace the woven-in row. The Target rows are marked built. The Persona note now says "the Reply and Check-ins sent on their own".
  - `CONTEXT.md`: Woven-in Check-in names the check; the Model Call Log names the new facts.
  - The voice hint now uses the drawn wording ("…and so does a Check-in sent on its own"), which 07 had held back until this issue.
- **Trace and Prompts & models.**
  - In the browser (Admin, live trace): the Reply Plan card shows "Check-in Kinds offered 4 / Check-in Kind chosen A follow-up", and a "Check-in" card shows "Check-in Kind A follow-up / Brought up Yes".
  - The Reply Plan card's description is the drawn "Decides what the reply should do: the Need, the Moves, which Threads to bring up, whether a Check-in fits, and Zeph's Read."
  - Pixel test (fixture mode):
    - `FAIL AdminModelCallTrace 0.13% differs, height 1357 vs 2274` (0.64% after 07). The two Check-in facts are in place, and the Reply card now lines up. Still different: the "Pattern" fact (14, so the two Check-in facts sit one slot early); and, owned by no issue, the "Sample data" pill, the year in "Started 19 Nov 2026", the back link and the annotation section below the dashed line (the height gap). 11 and 14 still draw this page.
    - `FAIL AdminPrompts 0.19% differs, height 3361 vs 3520`. Under the 0.5% pixel limit; it fails on height. This is the last issue on this page, but what still differs belongs to no issue (08 recorded the same list): the drawn "About this page" note the app doesn't draw (the height gap), the drawn unsaved Reply Plan save bar, character counts that don't match the drawn texts, the model dropdown font, the footer note wording and the "Sample data" pill. **The user decided (20 Nov 2026) to record these and merge without a full PASS.**
- **Checks** (final, on the reviewed code): `uv run pytest` 1430 passed; `ruff check` "All checks passed!"; `ruff format --check` "547 files already formatted"; `mypy src` "Success: no issues found in 200 source files". `pnpm lint` and `pnpm typecheck` clean; `pnpm format:check` "All matched files use Prettier code style!"; `pnpm test` 886 passed in 131 files.
- **How the live runs were made:** worktree stack `ai-chat-companion-mp-09` on a fresh database at 0071. The real app (`create_app` with the real builders) ran inside the backend container on real Postgres, with real DeepSeek for every call. Swapped: the chat channel (records sends), the scheduler (never ticks) and the timer (Message waits run at once). Test Users were made with SQL, and the Due Time was moved with SQL. The "forced" runs rewrote only the Reply Plan's `check_in` field, so every reply was offered a Check-in. No Eval was run.
- **`/code-review`:**
  - Standards: no hard breaches. Fixed: the offered Check-in and its saved row are one `SavedWovenCheckIn` (no bare tuple, no pass-through `_take_back`); one function writes the Check-in line for the Reply and the check; two test lines tidied.
  - Spec fixes: a Kind no longer offered can't crash the Reply Plan (it gives no Check-in); the stale seed comment about the woven-in prompt is removed.
- **Judgement calls, left as they are:**
  - The Reply Plan isn't given the User's recent Check-ins, which the old model saw. It judges repeats within the Conversation and from earlier Reply Plans.
  - The checker shows as a "Check-in" step inside a Message trace, which the design doesn't draw (it follows from the user's choice). The step filter "Check-in" now also finds those Message traces.
  - The understanding eval's `woven_in` now means "the Reply Plan chose a Check-in".
  - The check runs before the reply is sent, so a reply offered a Check-in waits for one small call (about 0.7 s live).

## Completion

- Completed: 2026-11-20
- Commits on branch `mp-09-check-ins-by-reply-plan`:
  - 018b728 "Message pipeline issue 09: the Reply Plan weighs a due Woven-in Check-in. Code still decides whether one may be offered (not struggling, not paused unless Check in Now); only then the Reply Plan gets the Check-in Kinds and may choose one with a note. The separate Check-in model call and woven_check_in_prompt are gone (migration 0071 removes it and reloads reply_plan_prompt). The Reply gets the chosen one as an optional extra with no tool; a small yes/no check on the Check-in model then says whether the reply brought it up, and one left out is taken back. The trace shows Check-in Kinds offered and chosen, and the check's Kind and Brought up"
  - 9895a1f "Message pipeline issue 09 review fixes: the offered Check-in and its saved row travel as one SavedWovenCheckIn, a Kind no longer offered can't crash the Reply Plan, one function writes the Check-in line, the stale seed comment is gone, two test lines tidied"
  - 59c656e "Message pipeline issue 09 done: archive issue with test, run, pixel and review evidence"
- Merged into main in c0c0353 "Merge message pipeline issue 09: Woven-in Check-ins are decided by the Reply Plan. …"
