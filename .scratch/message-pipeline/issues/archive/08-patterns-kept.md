# 08 — Patterns kept at Conversation end

Status: completed
Lane: B
Blocked by: 06

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

New User Memory (ADR-0020). Nothing User-facing yet (10 shows them; 14 uses them in replies).

- **Storage:** per User: the pattern (a sentence or two); linked Life Threads; evidence entries (day, Thread, one self-contained line); state (suspected, confirmed, closed); when last offered and how the User took it (agreed, pushed back, brushed off); an embedding. No "how sure" score.
- **Keeping step** (new core service, own prompt, model and thinking switch, with hints), run after Life Threads at Conversation end: given the Threads the Conversation touched plus the User's other Threads closest in meaning (open or settled, however old, up to an Admin-set number), existing Patterns, and the days behind the evidence in play (up to an Admin-set number): messages while Message Retention keeps them, Day Summaries after. It may add evidence, start a suspected Pattern when the same way of thinking, feeling, acting or choosing shows up across two or more Threads (inferred values and goals included), and confirm or close one from how the User took a view Zeph offered in this Conversation (it judges from the transcript).
- No Curiosity is made to check a Pattern. While User Memory is off, nothing is started or changed.
- Delete My Data and Account Deletion remove all Patterns; Message Retention doesn't; deleting a linked Thread removes its link (and the Pattern if no evidence is left).
- **Admins** see only how many confirmed Patterns a User has. **Model Call Log:** a Pattern keeping step, no content for Users.

User stories covered: 23, 25, 26, 27, 30, 32, 55, 59, 65.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- **Users** (`/admin/users`, reference `AdminUsers`): the user panel lists "Confirmed Patterns" (a count only).
- **Prompts & models** (reference `AdminPrompts`): Pattern keeping is a core service, last in the list, with two limit rows, each with a hint.
- Fixture mode: Prompts & models lists four services in this order: Understanding, Reply Plan, Reply, Pattern keeping.
- **Shared references.** `AdminPrompts` also draws 05, 06 and 09. Build your part. The full PASS is due on whichever of those issues lands last; until then, record under Comments which parts still differ and which issue owns them. `AdminUsers` is yours alone.

## Acceptance criteria

- [x] A Conversation touching two Threads that show the same way of acting leaves a suspected Pattern with evidence from both, when the scripted keeping answer says so
- [x] The keeping call is given the touched and closest Threads (an old settled Thread close in meaning included) and the existing Patterns
- [x] Days within retention reach the call as messages; older days as their Day Summaries
- [x] A Pattern can be confirmed or closed by the keeping answer; a closed one is never changed back
- [x] Nothing is kept while User Memory is off
- [x] Delete My Data and Account Deletion remove all Patterns
- [x] Prompt, model, thinking and the two limits are Admin-editable with hints; the Admin user view shows the confirmed count
- [x] The Model Call Log shows the Pattern keeping step
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] `node design/compare.cjs AdminUsers` prints PASS — **FAIL as drawn, as Zaf chose in redesign issue 10** (the panel stays closed until Manage, no "Sample data" pill); with Manage pressed on Alex: 0.06% (see Evidence)
- [x] The Pattern keeping card matches `AdminPrompts`; full PASS if this is the last issue on it, otherwise the remaining differences are recorded under Comments
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 06 — Every Admin field explains itself (`.scratch/message-pipeline/issues/06-admin-field-hints.md`)

## Comments

### Plan (20 Nov 2026, branch `message-pipeline-08-patterns-kept`)

- **Storage** (migration 0067): `patterns` (pattern text, state, started/updated, last offered at + reaction, embedding) and `pattern_evidence` (day, Thread, line). Evidence cascades with its Pattern and its Thread; a Pattern's linked Threads are the Threads in its evidence, so deleting a Thread drops its evidence, and a Pattern left with none is deleted in the same transaction.
- **Keeping** (`core/patterns.py`, `PatternKeeper`): runs after Life Threads, only when that step touched a Thread (`LifeThreadKeeper.keep_from` now returns the Threads it started or changed). Given: touched Threads, other Threads closest in meaning (no bar, up to `pattern_keeping_threads`), all the User's Patterns, and the days behind the evidence of Patterns linked to those Threads (newest first, up to `pattern_keeping_days`): that day's messages if any are still kept, else its Day Summary.
- **Code rules over the answer:** a new Pattern needs evidence from 2+ different shown Threads; evidence must name a shown Thread; confirm/close only with a reaction (agreed, pushed back, brushed off) judged from this Conversation; closed Patterns are never changed.
- **Admin:** five settings with hints (prompt, model, thinking, two limits); core services get `limit_keys`, drawn as limit rows on the card; Users panel shows Confirmed Patterns; Model Call Log step `patterns` ("Pattern keeping").
- Delete My Data / Account Deletion delete Patterns.

Changed while building (see Evidence): keeping runs at every Conversation end, not only when a Thread changed; a new Pattern can start confirmed or closed; evidence is dated to the Conversation's day; the migration is 0067.

### 2026-11-20 — evidence

- **Suspected Pattern from two Threads:** `test_two_threads_showing_the_same_way_of_acting_start_a_suspected_pattern`. Running app, real models: a Conversation about a side project, mum's visit and climbing kept "When something grabs them, everything else goes quiet: food, people, patience." (suspected), with one self-contained line of evidence from each Thread. Later run: "Says yes to requests from others even when already overloaded…" with evidence from three Threads.
- **Touched and closest Threads, and the Patterns, reach the call:** `test_keeping_is_given_the_touched_and_closest_threads_however_old_and_the_patterns` (a settled Thread 300 days old comes in as closest; the limit holds). Running app: the call's input listed the touched Thread (pottery), the two older Threads closest in meaning, and the kept Pattern with its evidence.
- **Days as messages, then Day Summaries:** `test_days_within_retention_reach_keeping_as_messages_and_older_ones_as_summaries`. Running app: the 19 Nov day reached the call as its messages; a day whose messages weren't there came as its Day Summary.
- **Confirm or close; closed never changes back:** `test_a_pattern_is_confirmed_or_closed_by_how_the_user_took_it_and_stays_closed`, `test_a_brushed_off_view_never_closes_a_pattern`, `test_a_new_pattern_the_user_agreed_with_in_the_same_conversation_starts_confirmed`, `test_a_pattern_is_confirmed_even_when_no_thread_changed_in_the_conversation`. In code, only "agreed" confirms and only "pushed back" closes. Running app: a follow-up Conversation where the User agreed with the view ("yeah, that is exactly me") confirmed the Pattern (`last_reaction` agreed, `last_offered_at` set), both when a new Thread was started and when none changed.
- **Nothing kept with User Memory off:** `test_with_user_memory_off_no_pattern_is_started_or_changed`. Running app: with User Memory turned off through `PATCH /api/me`, the next Conversation end made no model calls and the Pattern was unchanged.
- **Deletes:** `test_delete_my_data_removes_every_kind_of_data_but_keeps_the_account` now has a Pattern among its data; Account Deletion is covered by the same file (every per-User table empty). `test_deleting_a_linked_thread_drops_its_evidence_and_the_pattern_once_none_is_left`. Running app: deleting the Spanish Thread removed only its evidence; Delete My Data left 0 Patterns, 0 evidence and 0 Threads; deleting the account through `DELETE /api/me` left no User, Patterns or evidence.
- **Admin settings and count:** `test_pattern_keeping_is_the_last_core_service_with_its_limits_and_hints`, `test_admins_see_only_how_many_confirmed_patterns_a_user_has_and_the_keeping_step`, `PromptsAndModels.test.tsx` (limit row with hint, saved with the service), `AdminUsers.test.tsx` (Confirmed Patterns). Running app as Admin: Prompts & models shows Pattern keeping last with "Closest Threads to include" 8 and "Days of evidence to include" 14, each with its hint; changing days to 10 saved and survived a reload (set back to 14). At 390 the card wraps with no sideways scroll. The Users panel showed "Confirmed Patterns 1". No page errors.
- **Model Call Log:** the step is `patterns`, labelled "Pattern keeping" (`model-calls.test.ts`); the trace test checks a plain User's call keeps no content. Running app: each Conversation end ran conversation_end → life_threads → patterns → curiosities → portrait, and the step filter lists "Pattern keeping".
- **No Curiosity checks a Pattern:** the Curiosity keeping prompt no longer asks for "a pattern you notice" and says never to check a Pattern; migration 0067 reloads it only where unedited (two tests). Running app: the four Curiosities written were plain follow-ups.
- **Migration head:** after rebasing on `3f5518c` (issue 03's `0066_longer_message_wait`), this is `0067_patterns` revising 0066; Alembic reports one head, `0067`.
- **Docs:** `docs/message-pipeline/README.md` has a "Built" note under "c. Patterns" and the Pattern keeping row in the "Today" prompts table; `CONTEXT.md`'s Pattern entry says how deleting a Thread, Delete My Data and Account Deletion affect Patterns, and that Admins see only the confirmed count.
- **Pixel tests** (design fixtures, worktree port 3020):
  - `AdminUsers`: FAIL as drawn, 2.80% (height 800 vs 933), for the reasons Zaf accepted in redesign issue 10. With Manage pressed on Alex: 0.06%, height 933 vs 933. The Confirmed Patterns row lines up exactly; what is left is the "Sample data" pill and the totals line.
  - `AdminPrompts`: 0.19% of pixels differ (under the 0.5% limit), height 3422 vs 3581. The whole Pattern keeping card, both limit rows included, lines up. Still different, and not this issue's:
    - the drawn "unsaved" Reply Plan save bar and its card (05)
    - the drawn character counts, which don't match the drawn texts
    - the model dropdown font (monospace in the drawing; was already different)
    - the footer note wording
    - the "Sample data" pill
    - the "About this page" note, which the app doesn't draw (the height gap)

    A full PASS is due on whichever of 05 or 09 lands last.
- **Checks** (after the rebase): `uv run pytest` 1389 passed; `uv run ruff check .`, `uv run ruff format --check .` and `uv run mypy src` clean; `pnpm lint`, `pnpm format:check` and `pnpm typecheck` clean; `pnpm test` 872 passed. The Docker web image's `pnpm build` succeeded.
- **Code review:** standards and spec reviews ran.
  - Fixed: keeping now runs at every Conversation end (it used to skip when no Thread changed, losing a confirm); Threads brought up count as touched; confirm and close rules are in code; evidence is saved in one insert, skipping Threads or Patterns deleted meanwhile; `last_reaction` is stored as its value; the keep_from Thread numbering is simpler; `FieldNumber` takes an optional unit; TSDoc rewrapped.
  - Left as is: the read-JSON-and-retry shape repeats as in the other keeping steps; the description takes many arguments, like the others; `read_text` is shared from `life_threads.py`; the step label stays "Pattern keeping", as the issue names it.
- **Found in the running app and fixed:** a new Pattern the User agreed with in the same Conversation stayed suspected (now it can start confirmed or closed); evidence was dated "today" rather than the day the Conversation started (the call now gets the Conversation's day, and evidence defaults to it).

## Completion

- Completed: 2026-11-20
- Commit: <merge commit, filled in after merging>
