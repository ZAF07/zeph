# 05 — The Reply Plan takes over deciding; the Understanding only reads

Status: in-progress
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

- [ ] Each Message makes an Understanding call whose instructions and input contain no Needs, Moves or Threads to pick, then a Reply Plan call that gets them
- [ ] The Understanding's answer keeps said / read / unclear apart for feelings and wants, and these reach the Reply Plan
- [ ] The Need and Moves picked by the Reply Plan reach the Reply, with today's rules still enforced (question-asking Moves, ask-why, raise limits, hold-backs)
- [ ] A failing Reply Plan call falls back to the fallback Need and the reply still goes out
- [ ] Reply Plan prompt, model and thinking are Admin-editable on the settings page, with a short hint
- [ ] The Model Call Log shows the Understanding and the Reply Plan as separate steps with the shapes above
- [ ] Move Outcomes and the unmade next Move still work from the Reply Plan's Moves
- [ ] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [ ] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [ ] The Reply Plan card and the trace's two steps match `AdminPrompts` and `AdminModelCallTrace` (`node design/compare.cjs AdminPrompts AdminModelCallTrace`); full PASS if this is the last issue on them, otherwise the remaining differences are recorded under Comments
- [ ] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [ ] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [ ] Verified in the running app with `/run`, evidence recorded under `## Comments`

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
