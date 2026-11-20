# 05 — The Reply Plan takes over deciding; the Understanding only reads

Status: completed
Lane: A
Blocked by: 03

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

Split today's Understanding call in two (ADR-0021). No Read yet: replies should behave as before, just decided in a separate step.

- **Understanding** (narrowed): its prompt is rewritten to read only. Given the Message, the Conversation, earlier Understandings and the Portrait. Output: what the User said and means; how they feel and how strongly, and what they want, each split into said / read / unclear; whether the cause is known; struggling; asked for a photo; look-up phrases for the past. It no longer picks Needs, Moves, Threads, Curiosities, Knowledge or memory categories. Fallback Understanding when it fails, as today.
- **Reply Plan** (new core service with its own prompt, model and thinking switch, thinking on by default, shown on the settings page like the other core services): given the Understanding, the reminded Threads, due Curiosities, Move Outcomes, memory, the Needs and Moves (filtered by Features and limits as today), Ready Knowledge documents and earlier Reply Plans in the Conversation. Output: the Need; lead, supporting and next Moves with why; Threads to bring up or leave alone with reasons; Curiosities to raise; Knowledge documents and a search phrase or none; memory categories; whether a Shared Photo may be sent; whether to ask why. A fallback Reply Plan uses the fallback Need when it fails.
- All existing code rules move with the decisions: Moves that ask a question, ask-why, Curiosity raise limits, Thread hold-backs, next Move carry-over (and the unmade next Move reaching Curiosities), Move Outcomes reading the Moves made.
- Knowledge passages are fetched after the Reply Plan, from what it picked. The Reply gets the Reply Plan's guidance where it got the Understanding's (keeping 01's priority order).
- The Woven-in Check-in model still runs for now (moved into the Reply Plan in 09); give it the Understanding and the Reply Plan.
- **Model Call Log:** a Reply Plan step; its shape takes over the Need, Moves and Thread counts from the Understanding's; the Understanding's keeps intensity, cause known, struggling and look-ups. Never any User's words.
- **Glossary:** terms already in `CONTEXT.md` (Understanding, Reply Plan). Existing Understanding Eval cases may fail until 13; mark them, don't rewrite them here.

User stories covered: 4, 5, 6, 7, 54, 62.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- **Prompts & models** (`/admin/prompts`, reference `AdminPrompts`): Reply Plan is a core service with its own card, after Understanding and before Reply, with Model, Thinking, Prompt and Fallback wording. Keep today's card look; only add what the reference adds.
- **Model call trace** (`/admin/model-calls/[traceId]`, reference `AdminModelCallTrace`, fixture at `/admin/model-calls/design-trace`): Understanding and Reply Plan are separate steps. Understanding keeps Mood intensity, Cause known, Struggling, Past look-ups. Reply Plan takes Need picked, the Moves and the Thread counts (`web/src/lib/model-calls.ts`).
- Fixture mode must show exactly what is drawn (README "Fixtures").
- **Shared references.** `AdminPrompts` also draws 06, 08 and 09; `AdminModelCallTrace` also draws 07, 09, 11 and 14. Build your part. The full PASS is due on whichever of those issues lands last; until then, record under Comments which parts still differ and which issue owns them.

## Acceptance criteria

- [x] Each Message makes an Understanding call whose instructions and input contain no Needs, Moves or Threads to pick, then a Reply Plan call that gets them
- [x] The Understanding's answer keeps said / read / unclear apart for feelings and wants, and these reach the Reply Plan
- [x] The Need and Moves picked by the Reply Plan reach the Reply, with today's rules still enforced (question-asking Moves, ask-why, raise limits, hold-backs)
- [x] A failing Reply Plan call falls back to the fallback Need and the reply still goes out
- [x] Reply Plan prompt, model and thinking are Admin-editable on the settings page, with a short hint
- [x] The Model Call Log shows the Understanding and the Reply Plan as separate steps with the shapes above
- [x] Move Outcomes and the unmade next Move still work from the Reply Plan's Moves
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] The Reply Plan card and the trace's two steps match `AdminPrompts` and `AdminModelCallTrace` (`node design/compare.cjs AdminPrompts AdminModelCallTrace`); full PASS if this is the last issue on them, otherwise the remaining differences are recorded under Comments
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 03 — A Message waits for the User to finish, and starts over (`.scratch/message-pipeline/issues/03-message-wait-and-start-over.md`)

## Comments

### Plan (20 Nov 2026, branch `message-pipeline-05-reply-plan`)

- **Models:** `UnderstandingForm` narrows to reading only: `said`, `means`, `feelings` and `wants` (each said / read / unclear), `mood`, `intensity`, `cause_known`, `struggling`, `asked_for_photo`, `look_up_past`. New `ReplyPlanForm` (the model's answer: Need, guidance, Moves with why, Threads touched / to bring up / to leave alone, Curiosities, Knowledge, memory categories, photo, ask why) and `ReplyPlan` (saved: the Need, Moves and asked-why the reply followed). `UnderstandingShape` keeps intensity, cause known, struggling, past look-ups; new `ReplyPlanShape` takes the Need, Moves and Thread counts. `ModelStep.REPLY_PLAN`.
- **Storage:** one migration adds `reply_plans` (same keys and cascades as `understandings`), drops the decision columns from `understandings`, adds `reply_plan_shape` to both Model Call Log tables, and resets `understanding_prompt` to the new seed (the old one asks the Understanding to pick Needs and Moves). Old Understanding rows read tolerantly; no backfill (platform not live).
- **Services:** `UnderstandingService.understand` gets only the Portrait, earlier Understandings and the Conversation. New `core/reply_plan.py` takes the deciding code from `understanding.py` (Moves that ask a question, ask-why, raise limits, hold-backs, fallback Need, Features) with its own prompt/model/thinking. The plan decides "ask why" and the photo; code keeps the old limits on both. `ReplyService`: gate → Understanding → reminders/due/outcomes → Reply Plan → memory + Knowledge + Woven-in Check-in → Reply. Move Outcomes, the unmade next Move and Woven-in Check-ins read the Reply Plan.
- **Settings:** `reply_plan_prompt`, `reply_plan_model`, `reply_plan_thinking` (on) with hints; the Reply Plan core service sits after Understanding and before Reply; the Shared Photos description moves to it.
- **Evals:** the Understanding Eval runs both steps and reads its checks from both; cases are marked as checking both until 13.
- **Web:** `reply_plan` step, `ReplyPlanShape`, `replyPlanShapeFacts`; Understanding facts narrowed; a design fixture for `/admin/model-calls/design-trace`.

### Evidence (20 Nov 2026)

- **Understanding gets nothing to pick, then a Reply Plan gets it:** `test_every_message_gets_an_understanding_then_a_reply_plan_before_the_reply` (call order safeguard → understanding → reply_plan → reply; the Understanding's input has no Needs, Moves, Life Threads, Knowledge or Goals; the Reply Plan's has every Need) and `test_the_seeded_understanding_prompt_asks_for_no_decisions`. `/run` in the worktree stack (real app, real repositories, real DeepSeek, run in the backend container with only the Telegram channel swapped for a recording one, per the worktree fake-chat limit): an Admin's message "my PM overruled me AGAIN in front of everyone…" made Understanding, Reply Plan and Reply calls. The Understanding's instructions held none of `"need"`, `lead_move`, `bring_up`, `Needs:`, `Moves`, and its input had only the time, Portrait, earlier Understandings and the Conversation.
- **Said / read / unclear kept apart and reach the Reply Plan:** `test_said_read_and_unclear_stay_apart_and_reach_the_reply_plan`. In the `/run` the Understanding answered feelings `said: "Frustrated and 'so done with this job'"`, `read: "Humiliated at being contradicted in front of others…"`, `unclear: "Whether this is pure venting or whether quitting is actually on their mind"`, and wants `read: "To vent and have someone take their side"` with the advice-or-vent question as unclear. The Reply Plan's input opened with "How you understood their latest message: … Feelings: said: …; read (a guess): …; unclear: …". It was saved in `understandings.form`.
- **Need and Moves reach the Reply, rules kept:** `test_the_reply_follows_the_reply_plans_need`, the ask-why tests (`test_a_standout_mood…`, `…not_made_twice_in_a_row`, `test_the_reply_plan_can_ask_why_when_the_mood_does_not_stand_out`, `…never_asks_why_when_the_cause_is_known`, `…can_rule_out_asking_why…`), `test_moves_that_ask_a_question.py` (13), the raise-limit tests in `test_curiosities.py` and the hold-back tests in `test_life_threads.py`. In the `/run` the first Reply Plan picked Be heard, lead Get curious, next Suggest. The Reply's level-3 guidance read "What they need from you right now: Be heard … How they seem: angry, fed up (high)". The second Message ("idk. what would you do?") got Advice, lead Suggest, support Plan steps (the next Move held earlier), and the reply gave a concrete plan.
- **A failing Reply Plan falls back and the reply goes out:** `test_a_failed_reply_plan_still_replies_with_the_fallback_and_shows_in_the_log`, `test_an_unreadable_reply_plan_falls_back_to_the_fallback_need`, `test_a_failed_reply_plan_never_asks_why_even_when_the_mood_stands_out`. In the `/run`, `reply_plan_model` was set to a model that doesn't exist. The log showed `reply_plan` with `OpenAIInvalidRequestError`, the shape and saved row were Ask more with no Moves (`is_fallback` true), and the reply "Sounds like one of those days. What kind of long…" was saved and sent.
- **Admin-editable on the settings page, with a hint:** the `/admin/prompts` screenshot in the running stack shows a Reply Plan card after Understanding and before the Reply ("Every Message · after the Understanding"), with Model, Thinking (on) and a Prompt editor, each with its hint. In the browser, turning Thinking off and pressing Save stored `reply_plan_thinking = false` in `platform_settings`; turning it back on stored `true`. Tests: `test_a_changed_reply_plan_prompt_and_thinking_are_used_for_the_next_message`, `test_core_services_list_their_prompt_and_model_settings`, `test_model_defaults.py` (thinking on).
- **Model Call Log shows two steps with their shapes:** `test_a_plain_users_understanding_and_reply_plan_show_shapes_and_never_words`, `test_a_failed_understanding_shows_the_fallback_it_used`, `test_a_failed_reply_plan_shows_the_fallback_need_it_used`, and `ModelCallTraceView.test.tsx` "shows the Understanding and the Reply Plan as separate steps". The running trace page for a plain User showed Understanding (Mood intensity Low, Cause known Yes, Struggling No, Past look-ups 0) and Reply Plan (Need picked Just chatting, Lead Move Get curious, Supporting and Next None, the Life Threads and Thread counts) as separate cards, each "No content kept for this User". None of that User's calls kept content.
- **Move Outcomes and the unmade next Move work from the Reply Plan:** `test_move_outcomes.py` (15), `test_unmade_next_move.py` (9), `test_next_move.py`. In the `/run` the Admin's Conversation was ended by shifting its times back 3 hours and ticking the scheduler. Move Outcome keeping was given "Moves Zeph made: [1] Get curious (lead) [2] Suggest (lead) [3] Plan steps (support)" with each message's Need, Moves and the mood from its Understanding, and kept "Get curious, lead, mixed". Curiosity keeping was given "A next Move Zeph had in mind but never made: Reframe, Once they say whether this is one PM or the whole job…".
- **One migration head:** `0067_reply_plans.py` revises `0066`, the newest on `main` at merge time; the worktree database is at 0067. `test_an_existing_install_moves_deciding_to_reply_plans_and_resets_the_prompt` checks it on an old-shaped Understanding.
- **Docs:** `CONTEXT.md` (Delete My Data, Model Call Log, Eval) and `docs/message-pipeline/README.md` (Built notes for steps 4, 6 and 7, the prompts table, the target table) describe what was built.
- **Pixel test** (`compare.cjs`, fixture mode, after this issue): AdminPrompts differs by 0.80%, the same figure recorded in 06. The Reply Plan card (Model, Thinking, Prompt, hints) lines up. AdminModelCallTrace differs by 0.66% (it errored with no fixture before). Its Safeguard, Understanding and Reply Plan facts, totals and spacing line up. What still differs, and who owns it:
  - Reply Plan facts "Read formed" and "Read said" (07), "Pattern" (14), "Check-in Kinds offered" and "Check-in Kind chosen" (09). These move the Reply card down.
  - On the Prompts page: Pattern keeping's limit rows (08), and a "Fallback wording" group on the Reply Plan card. The design draws that group empty, and no setting exists for it yet; this needs a decision.
  - Owned by no issue: the "Sample data" pill beside the trace heading; the year in "Started 19 Nov 2026, 9:14 PM" (the shared date format drops the current year); the reference's annotation samples ("Content, opened", "For a User who is not an Admin"), which the app doesn't draw on any template page (see 06); the drawn character counts and the model dropdown font on Prompts (see 06).
- **Checks:** `uv run pytest` 1388 passed; `ruff check`, `ruff format --check` and `mypy src` clean; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean; `pnpm test` 872 passed.
- **`/code-review`:** Standards found no hard breaches. Fixed: two hint strings left split mid-sentence, and `describe_understanding_for_check_in` renamed `describe_reading_and_plan_for_check_in`. Left as judgement calls: the two `_ask` methods have the same shape (each service owns its call, as elsewhere); `ReplyPlanService.plan` is long. Spec: fixed a failed Reply Plan still asking why (its fallback now never asks; test added). Kept on purpose: migration 0067 resets an edited Understanding prompt (the old one asks for decisions; 0054 did the same); the Understanding Eval's checks read the Reply Plan, and the cases are marked rather than rewritten, until 13; Moves in Conversations open during the migration aren't copied (platform not live). The "Tools called: None", the ▸ Content row, "Strong", the wide Tokens tile and the 24px gap follow the `AdminModelCallTrace` reference.
- **Caveat:** the Understanding Eval wasn't run (Evals cost money). Its cases may fail until 13.

## Completion

- Completed: 2026-11-20
- Commits on branch `message-pipeline-05-reply-plan`:
  - 999fd79 "Message pipeline issue 05: the Reply Plan takes over deciding; the Understanding only reads"
  - 0940229 "Message pipeline issue 05 review fixes: a failed Reply Plan never asks why, the Check-in helper is named for both forms it describes, two split hints joined"
  - d435c5c "Message pipeline issue 05 done: archive issue with test, run, pixel and review evidence"
- Merged into main in 6204605 "Merge message pipeline issue 05: the Reply Plan takes over deciding and the Understanding only reads (ADR-0021). …"
