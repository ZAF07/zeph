# 07 — Zeph forms a Read from the Outlook

Status: completed
Lane: A
Blocked by: 05

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

The heart of the review: Zeph stops only mirroring.

- **Outlook:** the Persona becomes two Admin-editable texts: its voice (today's Persona text) and its Outlook (new, plain prose, seeded with a starting text the owner can rewrite). The Outlook goes only into the Reply Plan's instructions; the voice stays in front of the Reply and Check-ins sent on their own. Both show on the settings page with hints.
- **Read:** the Reply Plan always forms a Read (Zeph's honest view of what is really going on, from the Outlook, the Understanding and memory) and decides whether to say it now: only when there is room (not mid-vent, in crisis or light chat; a vent is heard first, the Read comes once it is spent), it is worth saying (it adds something the User hasn't said) and it isn't a repeat (never the same Read twice in a Conversation). When the User asks for Zeph's view, it gives its deepest Read at once, not advice already given. The Read is offered as Zeph's view, never as fact.
- **Where we are:** the Reply Plan writes one line on where the Conversation is now ("venting, nearly spent", "asking for a view"); each Reply Plan sees the earlier ones.
- The Reply gets the Read at priority level 3 when it is to be said. Admins' own traces show the Read in full; the Model Call Log shape records only whether one was formed and said.

User stories covered: 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 22, 51, 52, 53, 63.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- **Persona** (`/admin/persona`): two tabs, Voice (reference `AdminPersona`) and Outlook (reference `AdminPersonaOutlook`, `?tab=outlook`), each with its own editor and save bar. Tabs work like the Memories tabs: clicking swaps the editor and sets `?tab=outlook`. Unsaved text in one tab is kept when switching to the other.
- **Model call trace** (reference `AdminModelCallTrace`): the Reply Plan step records "Read formed" and "Read said"; an Admin's own trace shows the Read and the where-we-are line in Content. Another User's trace shows only the two facts.
- **Shared references.** `AdminPersona` also draws 06's hints; `AdminModelCallTrace` also draws 05, 09, 11 and 14. Build your part. The full PASS is due on whichever of those issues lands last; until then, record under Comments which parts still differ and which issue owns them. `AdminPersonaOutlook` is yours alone.

## Acceptance criteria

- [x] The Outlook is an Admin-editable setting with a hint, seeded, and a change applies from the next reply
- [x] The Outlook reaches the Reply Plan's instructions and no other call; the voice still reaches the Reply
- [x] Every Reply Plan carries a Read and whether to say it; a Read to be said reaches the Reply at level 3, one not to be said doesn't reach it
- [x] The Reply Plan prompt states the three conditions and the when-asked rule
- [x] Each Reply Plan writes a where-we-are line and earlier Reply Plans in the Conversation are in its input
- [x] The Model Call Log records whether a Read was formed and said; an Admin's own trace shows its text
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] Switching Persona tabs keeps unsaved text in the other tab (component test)
- [x] `node design/compare.cjs AdminPersonaOutlook` prints PASS
- [x] The tabs and the Read facts match `AdminPersona` and `AdminModelCallTrace`; full PASS if this is the last issue on them, otherwise the remaining differences are recorded under Comments
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 05 — The Reply Plan takes over deciding; the Understanding only reads (`.scratch/message-pipeline/issues/05-reply-plan-takes-over-deciding.md`)

## Comments

### Plan (20 Nov 2026, branch `message-pipeline-07-read`)

- **Outlook setting:** new `persona_outlook` Platform Setting (label "Outlook", hint as drawn), seeded with the drawn starting text. The `persona` setting becomes the voice (label "Voice"). The Reply Plan's instructions are the Outlook, then `reply_plan_prompt`. No other call gets the Outlook; the Reply and Check-ins keep the voice.
- **Read and where we are:** `ReplyPlanForm` gains `where_we_are`, `read` and `say_read` (stored in the existing `form` JSON, so no new column; old rows read as no Read). `say_read` counts only when there is a Read. A Read to be said goes into the Reply's level 3 (plan) section as Zeph's view, never as fact; one not to be said doesn't reach the Reply. Earlier Reply Plans in the Conversation are written for the next one with their where-we-are line, Read and whether it was said, so it doesn't repeat a Read.
- **Prompt:** `reply_plan_prompt` asks for the where-we-are line and the Read first, states the three conditions (room, worth saying, not a repeat) and the when-asked rule. Migration 0070 (renumbered from 0068 after issues 08 and 10 took 0068 and 0069) deletes the stored `reply_plan_prompt` so the new seed loads (platform not live; 0067 did the same for the Understanding).
- **Model Call Log:** `ReplyPlanShape` gains `read_formed` and `read_said` (JSON, old rows read as false). The Read's text shows only in an Admin's own Content, as today.
- **Web:** Persona page gets Voice and Outlook tabs (`?tab=outlook`), each with its own editor and save bar, drafts kept per tab. Trace facts gain "Read formed" and "Read said". Fixtures as drawn.

### Evidence (20 Nov 2026, after rebasing on `origin/main` c490dba)

- **Outlook is an Admin setting with a hint, seeded, used from the next reply:** `persona_outlook` in `core/platform_settings.py` (label "Outlook", hint) and the seed. Tests: `test_the_outlook_is_an_admin_setting_with_a_hint`, `test_a_changed_outlook_is_used_from_the_next_reply`, `test_a_plain_user_cannot_change_the_outlook`. In the running app, a marker line written into the Outlook between messages showed up in the very next Reply Plan's instructions (no restart). In the browser as an Admin, the Outlook saved from its tab and was still there after a reload of `?tab=outlook`.
- **Outlook reaches the Reply Plan only; the voice still reaches the Reply:** `test_only_the_reply_plan_gets_the_outlook_and_the_reply_keeps_the_voice` (the Reply Plan's instructions are the Outlook, two newlines, then the prompt; the Reply, Understanding and Safeguard don't get it). The Check-in tests now also check that the Check-in on its own and the woven-in Check-in don't get it. Live run: "Outlook marker in instructions" was True for every Reply Plan and False for every Safeguard, Understanding and Reply call.
- **Every Reply Plan carries a Read and whether to say it; only a Read to be said reaches the Reply at level 3:** `test_a_read_to_be_said_reaches_the_reply_at_level_three_as_zephs_view`, `test_a_read_not_to_be_said_never_reaches_the_reply`, `test_saying_no_read_or_an_odd_say_read_says_nothing`. A fallback Reply Plan (failed call) forms no Read: `test_a_failed_reply_plan_forms_no_read`. Live run (real DeepSeek), three texts from an Admin:
  - "my manager dumped another project on me at 6pm and I said yes AGAIN": where we are "venting, just started", a Read formed, not said. The Reply's instructions had no Read line.
  - "I just never say no. like ever…": "venting, deepening — they've moved from the project to naming the pattern", a new Read, still not said.
  - "honestly what do you think is going on with me?": "venting has spent itself; they've turned and asked directly for my read on them", Read said. The Reply's level 3 read "Your Read of what is really going on, to give in this reply as your view, never as fact: The 'never say no' isn't a discipline problem…". Zeph answered "I think the "never say no" isn't a discipline problem. In the moment, no doesn't feel like a real option — the yes buys you something…".
- **The prompt states the three conditions and the when-asked rule:** `test_the_seeded_reply_plan_prompt_asks_for_a_read_and_says_when_to_give_it` (room, worth saying, not a repeat, "ask for your view", "deepest Read", "never as fact"). Migration 0070 reloads it on existing installs: `test_an_existing_install_gets_the_reply_plan_prompt_that_asks_for_a_read`; the worktree database was at the newest migration with the new prompt.
- **Where-we-are line, and earlier Reply Plans in its input:** `test_the_next_reply_plan_sees_where_we_were_and_the_reads_already_formed`. Live run: the third Reply Plan's input listed both earlier plans as "- Where we were: … Read (not said): … Need: Be heard; …".
- **Model Call Log records Read formed / said; an Admin's own trace shows the text:** `test_the_log_records_whether_a_read_was_formed_and_said_never_its_words` (a plain User: the facts, no content, no words), `test_an_admins_own_trace_shows_the_read_in_full`, the updated shape test in `test_model_call_log.py`, `model-calls.test.ts` and `ModelCallTraceView.test.tsx`. In the browser, the Admin's trace showed "Read formed Yes / Read said Yes", and its Content showed the Outlook, the prompt and the answer with `"where_we_are"` and `"read"`. A plain User's trace showed the two facts and "No content kept for this User".
- **One migration head:** issue 08 merged `0068_patterns.py` while this was in review, and issue 10 merged `0069_pattern_confirmed_at.py` just before this merged, so this migration became `0070_reply_plan_read.py` (revises 0069). A fresh worktree database migrated to the newest head with every lane's tables and settings.
- **Docs:** `CONTEXT.md` (the Model Call Log entry names the two Read facts; Read, Outlook and Reply Plan already described this) and `docs/message-pipeline/README.md` (Built notes for step 6, step 7's level 3 and the Outlook; the Today table's Persona column and Reply Plan input; the target row). It also puts back "migration 0066" for the Message wait, which `main` had as 0068.
- **Tabs keep unsaved text (component test):** `PersonaEditor.test.tsx` "keeps unsaved text in one tab while the other is shown", plus Outlook-from-`?tab=outlook` and saves-only-the-Outlook tests, and `persona.test.ts`. In the browser: typed in Voice, went to Outlook (URL `?tab=outlook`), back to Voice (URL clean), and the Voice draft was still there with "Unsaved changes".
- **Pixel test** (`compare.cjs`, fixture mode, Admin storage state, after the rebase):
  - `PASS  AdminPersonaOutlook  0.04% differs, height 800 vs 800`
  - `FAIL  AdminPersona  0.71%`. The header lead, tabs, Voice label and hint, editor box and save bar line up. Still different: the drawn "Unsaved changes" and Saved state of the Voice sample, the drawn character count, and the "Sample data" pill. No issue owns these (the same parts were recorded in 06).
  - `FAIL  AdminModelCallTrace  0.64%` (0.66% before this issue). "Read formed Yes / Read said No" line up exactly in the Reply Plan card. Still different: "Pattern" (14), "Check-in Kinds offered" and "Check-in Kind chosen" (09), which move the Reply card down; owned by no issue: the "Sample data" pill and the year in "Started 19 Nov 2026".
  - The Persona tabs needed `box-content`. The design draws them as links (44px plus a 2px underline), where the Memories tabs are buttons (44px all told).
- **Checks** (after the rebase): `uv run pytest` 1428 passed; `ruff check` "All checks passed!"; `ruff format --check` "546 files already formatted"; `mypy src` "Success: no issues found in 199 source files". `pnpm lint`, `pnpm format:check` ("All matched files use Prettier code style!") and `pnpm typecheck` clean; `pnpm test` 886 passed in 131 files.
- **`/code-review`:**
  - Standards found no hard breaches. Fixed: `persona.ts` got its own test; the tabs are a `Record` with a typed setting key (no fallback that can't happen); one place owns "say only when there is a Read"; a docstring and a seed comment rewrapped.
  - Left as judgement calls: the Persona tab helpers mirror the Memories ones (sharing them would touch Memories); the voice keeps the stored key `persona`.
  - Spec: added the Check-in "no Outlook" checks; the migration renumbered on rebase.
- **Judgement calls:**
  - The real Outlook hint is two sentences ("How Zeph sees people and what helps them grow, in plain prose. Zeph forms its Read of each User from this before every reply."), because 06's test caps hints at two sentences. The design fixture keeps the drawn three-sentence wording, so the live page's hint differs slightly from the drawing.
  - The voice hint likewise says "both Check-in prompts" (the woven-in Check-in model still gets the voice until 09) instead of the drawn "a Check-in sent on its own".
  - "Never the same Read twice" is held by the prompt plus the earlier Reads (said / not said) given to each Reply Plan, not by code.
- **Final re-check on the merged-ready code (0070):** a fresh worktree database migrated to 0070; the pixel figures were the same; one live "what do you think is going on with me?" from an Admin formed and said a Read at level 3 with the Outlook only in the Reply Plan; the Persona tabs check passed in the browser.
- **Caveat:** no Eval was run (Evals cost money). The live runs above used real DeepSeek calls.

