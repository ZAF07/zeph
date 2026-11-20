# 14 — Patterns come to mind in replies

Status: completed
Lane: B
Blocked by: 07, 12

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

Patterns reach the Reply Plan through Recall: through their linked Threads when one comes to mind, and directly when what the User is saying is close to the Pattern in meaning, even about something new with no Thread yet. Like Threads, they stay in mind for the Conversation. The Reply Plan may build its Read on one and offer it aloud by 07's rules, as Zeph's view ("here's what I notice…"), never as fact. A suspected or confirmed Pattern can be offered; a closed one never is. One the User pushed back on waits an Admin-set time before it may be offered again. The Reply Plan records which Pattern it offered, so the keeping step (08) can confirm or close it from the User's reaction. Model Call Log shape: whether a Pattern was used or offered.

User stories covered: 24, 60.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- The push-back wait is an ordinary field row with a hint, as in the "Field rows" sample in `AdminPersona`. No new parts.
- **Model call trace** (reference `AdminModelCallTrace`): the Reply Plan step has a "Pattern" fact. The drawn values are "None" and "Used, not offered"; the value for an offered Pattern isn't drawn, so ask Zaf for it before building.
- **Shared reference.** `AdminModelCallTrace` also draws 05, 07, 09 and 11. Build your part. The full PASS is due on whichever of those issues lands last; until then, record under Comments which parts still differ and which issue owns them.

## Acceptance criteria

- [x] A Pattern linked to a reminded Thread reaches the Reply Plan's input
- [x] A Pattern close in meaning to a new message with no Thread reaches it too
- [x] A closed Pattern never reaches it; a pushed-back one doesn't until the wait has passed
- [x] A Pattern the Reply Plan offers reaches the Reply and is recorded as offered, and the next Conversation end's keeping call sees it was offered
- [x] The push-back wait is Admin-editable with a hint
- [x] The Model Call Log shows whether a Pattern was used or offered
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] The new field row matches the field-row sample in `AdminPersona`; the Pattern fact matches `AdminModelCallTrace` (full PASS if this is the last issue on it, otherwise the remaining differences are recorded under Comments) — **`AdminModelCallTrace` fails on height only (0.02%): the app doesn't draw the annotation section. Zaf chose (20 Nov 2026) to merge and draw annotation sections in redesign issue 19** (see Evidence)
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 07 — Zeph forms a Read from the Outlook (`.scratch/message-pipeline/issues/07-read-from-the-outlook.md`)
- 12 — Wide recall (`.scratch/message-pipeline/issues/12-wide-recall.md`)

## Comments

### Plan (20 Nov 2026, branch `message-pipeline-14-patterns-in-replies`)

- **Recall** (`PatternReminder` in `core/patterns.py`, plain code, after `ThreadReminder`): Patterns linked to the Threads in mind, plus Patterns close in meaning to what the Understanding says the User means and their latest texts (same text window and closeness bar as Threads). Found ones are kept in a new `patterns_in_mind` table (migration 0073) and stay in mind for the Conversation. Closed ones never come in; a pushed-back one waits `pattern_pushed_back_wait_days` (new field row with hint, Memory section).
- **Reply Plan:** sees the Patterns in mind, numbered, with their state, evidence and last reaction. Its form gets `patterns_used` (numbers) and `offer_pattern` (number or null). An offer counts only when the Read is said (07's rules) and always counts as used too. Saved in the form, so keeping can read it. Migration 0073 also reloads `reply_plan_prompt` from the seed.
- **Reply:** an offered Pattern goes in at level 3 with the Read, as what Zeph notices, never as fact. A used-but-not-offered one doesn't reach the Reply.
- **Keeping:** the Pattern keeping call's input marks a Pattern "offered to them in this Conversation" when one of that Conversation's Reply Plans offered it.
- **Model Call Log:** the Reply Plan shape gets `pattern_used` and `pattern_offered`; the trace's "Pattern" fact reads None / Used, not offered / Offered (Zaf chose "Offered" for the value that isn't drawn).

### Evidence (20 Nov 2026)

Live runs used the real app (`create_app` through the Evals `InProcessCompanion`) inside the worktree's backend container, with real DeepSeek, the real embedder and Postgres at migration 0073. Swapped: a recording chat channel, a manual timer, and a scheduler whose tick was called by hand to run Conversation ends. A test User was seeded with SQL through the repositories:
- Threads: Side project app, Mum's visit, Pressure at Acme.
- Patterns: "When something grabs them, everything else goes quiet…" (suspected), "Says yes to what others ask even when already stretched thin" (pushed back 5 days earlier) and "Avoids conflict by going silent…" (closed).

- **A Pattern linked to a reminded Thread reaches the Reply Plan:** `test_a_pattern_linked_to_a_reminded_thread_reaches_the_reply_plan`. Live: "mum lands on friday and I've barely looked up from the app all week" brought Mum's visit and Side project app to mind, and the Reply Plan's input listed "[1] (suspected) When something grabs them…" with both pieces of evidence.
- **A Pattern close in meaning with no Thread reaches it:** `test_a_pattern_close_in_meaning_to_a_message_with_no_thread_reaches_it_too`; `test_a_message_far_from_every_pattern_and_thread_brings_no_pattern`; `test_a_pattern_in_mind_stays_in_mind_for_the_conversation`. Live: in a new Conversation, "started learning guitar last week and I keep playing till 2am, forgot to eat dinner twice" had "Life Threads in mind: None." and the Pattern in mind. The search (the Understanding's meaning plus the text) scored 0.626 against the 0.62 bar; the text alone scored 0.531. The next message ("any good podcast recommendations?") still had it in mind.
- **Closed never; pushed back waits:** `test_a_closed_pattern_never_reaches_the_reply_plan`, `test_a_pushed_back_pattern_waits_the_admin_set_days_before_it_comes_back`. Live: "Priya just asked me to take another project at Acme and I said yes again…" brought Pressure at Acme to mind, but "Patterns in mind: None.". Both linked Patterns were left out: the closed one, and the one pushed back 5 days earlier. With `last_offered_at` moved back 31 days, the same text brought the pushed-back Pattern in. The closed one stayed out.
- **An offered Pattern reaches the Reply, is recorded, and keeping sees it:** `test_an_offered_pattern_reaches_the_reply_as_zephs_view`, `test_a_pattern_used_but_not_offered_never_reaches_the_reply`, `test_a_pattern_is_offered_only_when_the_read_is_said`, `test_the_next_conversation_ends_keeping_call_sees_the_pattern_was_offered`. Live:
  - A1, mid-vent: the plan used the Pattern but didn't offer it (`patterns_used` set, `pattern_offered` null), and the Reply wasn't told it.
  - A2, "honestly, what do you think is going on with me?": the plan offered it (`pattern_offered` saved in the form), and the Reply's instructions had "It comes from something you've noticed keeps showing up in their life: … Offer it as what you notice ("here's what I notice…"), never as fact". The reply opened "Here's what I notice. When something grabs you, everything else goes quiet…" and ended "That's just what I see, though. Does it land?".
  - A3, "huh. yeah... that's actually exactly me": at Conversation end, the keeping input showed "[1] (suspected; offered to them in this Conversation…)". The keeping call answered `reaction: agreed, state: confirmed`, and the row became confirmed.
  - Re-run after the review fixes: the marker reads "offered to them in this Conversation: judge how they took it from the Conversation", and the Pattern was confirmed again.
- **Push-back wait Admin-editable with a hint:** `test_the_push_back_wait_is_admin_editable_with_a_hint`, `test_every_editable_setting_comes_with_a_short_hint`, and the `PlatformSettingsForm` test. In the browser as an Admin, the Memory section of `/admin/settings` showed "Wait after a pushed-back Pattern", 30 days, with its hint. Saving 45 survived a reload, then it was set back to 30. At 1280 and 390 it matches the rows around it, with no page errors. The updated hints for "Texts searched for Life Threads" ("…Life Threads and Patterns on…") and "Life Thread closeness bar" ("…a Thread's story, or a Pattern…") show there too.
- **Model Call Log:** `test_the_model_call_log_shows_whether_a_pattern_was_used_or_offered`, `model-calls.test.ts` (`describePatternUse`) and `ModelCallTraceView.test.tsx`. In the browser, three live traces showed "Pattern" between "Read said" and "Check-in Kinds offered": Offered (A2), Used, not offered (A1) and None (podcast message).
- **One migration head:** `0073_patterns_in_replies` (revises 0072) is the only new migration. No two migrations share a `down_revision`. After rebasing on `origin/main` (1c84ccc, issue 13 merged, no migration), the stack's `alembic_version` reads 0073. `test_the_migration_reloads_the_reply_plan_prompt_so_it_sees_patterns`.
- **Docs:**
  - `docs/message-pipeline/README.md`: a "Built for Patterns" note under 5. Recall, a "Built" note under 6. Reply Plan, and "Not yet: Patterns (14)" removed in both places. The c. Patterns note now says replies use Patterns. The Today table rows for the Reply Plan, the Reply and Pattern keeping are updated.
  - `CONTEXT.md` Pattern: Patterns stay in mind, closed ones never come to mind, pushed-back ones wait, and the Reply Plan records which one it offered.
- **Design:**
  - `AdminModelCallTrace`: 0.13% before this issue, 0.07% with the Pattern fact, 0.02% after the header fixes Zaf asked for. Those fixes:
    - The app's font now falls back to system-ui as the design does (`adjustFontFallback: false`), so the back link's arrow draws as drawn.
    - The trace says "Started 19 Nov 2026, 9:14 PM." with the year.
    - Fixture mode labels the drawn trace "Sample data"; real traces don't.

    The diff image has no red left above the dashed line. It fails only on height (1357 vs 2274): the drawn annotation section ("Content, opened" and "For a User who is not an Admin") isn't rendered. No page renders its annotation section yet. Zaf chose to merge and track it as `.scratch/redesign/issues/19-draw-annotation-sections-in-fixture-mode.md`.
  - The full pixel run (every route but the three Clerk pages) had the same 24 PASS before and after the font change. Nothing got worse, and seven pages got closer, e.g. Landing 0.03% → 0.00% and Onboarding 0.12% → 0.11%.
  - `AdminPersona`: 0.71%, unchanged (the same annotation-section height gap).
- **Checks** (final code, rebased on `origin/main`): `uv run pytest` 1470 passed; `ruff check` "All checks passed!"; `ruff format --check` "555 files already formatted"; `mypy src` "Success: no issues found in 204 source files". `pnpm lint` and `pnpm typecheck` clean; `pnpm format:check` "All matched files use Prettier code style!"; `pnpm test` 893 passed in 131 files.
- **`/code-review`:**
  - Standards: no hard breaches. Fixed: a garbled docstring, now with a one-item `read_pattern_picked`; a docstring on the test helper `shape_after`.
  - Spec: the closeness bar and text window hints now say they also apply to Patterns. The keeping marker now says to judge how the User took it.
  - Left as is: the Pattern search embeds the same text as the Thread search (one more local embed per reply, skipped for Users with no Pattern that may come to mind). The cap of 10 stays a code constant, since the issue asks for one new setting only. The `cosine_distance` query shape repeats the Thread search, like the surrounding code.

### Decisions and things to know

- **"Offered" is the trace value for an offered Pattern** (Zaf, 20 Nov 2026). An offered Pattern always counts as used too.
- **Direct recall reuses the Life Thread bar (62) and text window (8).** With the real embedder, an abstract Pattern scores lower than a Thread story against concrete texts: the guitar text alone scored 0.531, and only with the Understanding's meaning added did it pass (0.626). Patterns coming to mind in brand-new situations may be rare at this bar. A separate Pattern bar is the obvious knob if live use shows this.
- **Only an offered Pattern reaches the Reply.** A used one shapes the Read, which reaches the Reply already. A suspected Pattern's text never goes to the Reply unless it is offered.
- **An offer counts only when the Read is said** (07's rules). An `offer_pattern` with `say_read` false is dropped.
- **Keeping (08) is unchanged in code and prompt.** It still judges the reaction from the transcript, and the marker tells it which Pattern was offered.
- **Migration 0073 drops the stored `reply_plan_prompt`** so it reloads from the seed, even where an Admin edited it, as 0071 did: the old prompt never sees Patterns.
- **Font fallback changed for every page:** the app's stack is now "Outfit, system-ui, sans-serif", as in the design. This only affects glyphs Outfit's Latin subset lacks (e.g. arrows) and the moment before the font loads.
- No Eval was run (Evals cost money).

## Completion

- Completed: 2026-11-20
- Commit: 0db0f64 "Merge message pipeline issue 14: Patterns come to mind in replies" (merged into `main` locally and pushed), with:
  - 72ff690 "Message pipeline issue 14: Patterns come to mind in replies"
  - d314463 "Message pipeline issue 14: review fixes"
  - 268c3c5 "Message pipeline issue 14: trace header matches the design"
  - d39b129 "Message pipeline issue 14 done: archive issue with test, run, pixel and review evidence; redesign issue 19 filed"
