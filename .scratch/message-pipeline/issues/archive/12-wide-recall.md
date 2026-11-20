# 12 — Wide recall

Status: completed
Lane: B
Blocked by: 05, 08

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

Recall stops starving the Reply Plan:

- It searches by meaning on what the Understanding says the User means plus a wider window of their recent texts (Admin-set; today it is 3).
- Whatever Threads pass the closeness bar come in, up to a high Admin-set cap (today it is 3).
- Threads that came to mind earlier in the Conversation stay in mind until it ends, so the start of a long Conversation still counts.
- The Reply Plan sees all of them and picks what the reply uses, so a wide memory never crowds the reply.

Hold-back rules (raised once per Conversation, brushed-off wait, asked to drop) apply as today.

User stories covered: 37, 38, 57.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- The text window and the Thread cap are ordinary field rows with hints, as in the "Field rows" sample in `AdminPersona`. No new parts.
- The trace's Reply Plan step already draws "Life Threads reminded", "Threads brought up", "Threads left alone" and "Threads held back" (`AdminModelCallTrace`, set up in 05). Nothing new to draw here.

## Acceptance criteria

- [x] A Thread reminded by message 2 is still in the Reply Plan's input at message 20 of the same Conversation
- [x] Recall's search uses the Understanding's meaning and the wider text window
- [x] More than 3 Threads past the bar reach the Reply Plan, up to the cap
- [x] Only Threads the Reply Plan picks reach the Reply
- [x] The window and cap are Admin-editable with hints
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] The new field rows match the field-row sample in `AdminPersona`
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Web checks pass, if web code changed: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 05 — The Reply Plan takes over deciding; the Understanding only reads (`.scratch/message-pipeline/issues/05-reply-plan-takes-over-deciding.md`)
- 08 — Patterns kept at Conversation end (`.scratch/message-pipeline/issues/08-patterns-kept.md`)

## Comments

### Plan (20 Nov 2026, branch `message-pipeline-12-wide-recall`)

- `ThreadReminder.remind` (`core/life_threads.py`) takes the Understanding's `means` and searches on it plus the User's latest texts (new setting `life_threads_texts_to_search`, 8). Names (people or things in a Thread) are matched in the texts only.
- New table `life_threads_in_mind` (migration 0072): each Thread found is kept for the Conversation and comes back for every later message, after the ones that message found.
- The cap `life_threads_per_reply` (10, allowed up to 30) limits how many Threads are in mind at once (story 57).
- The Reply gets only the Threads the Reply Plan picked. A failed Reply Plan gives it none.
- The new setting is a field row on Platform settings, in the Memory section, using the existing `FieldRow`/`FieldNumber` (no new parts).

### Evidence (20 Nov 2026)

Live runs used real DeepSeek, the real embedder and Postgres inside the worktree's backend container. Only the Telegram channel was swapped for a recording one, and the timer runs work at once (fake chat IDs can't reach Telegram). The User was a seeded Admin (Asia/Singapore) with 5 open Threads: Mum's visit, Pressure at Acme, Side project app, Marathon training, Falling-out with Mei. Messages 3–19 were put straight into the database ("random thought N: the weather here is so grey and humid today", with replies) instead of being sent one by one.

- **A Thread reminded by message 2 is still in the Reply Plan's input at message 20:** `test_a_thread_reminded_by_message_2_is_still_in_mind_at_message_20` (20 real messages in one Conversation). Live:
  - Message 2 ("my mum lands on friday and I haven't even started cleaning") brought Mum's visit to mind, and it was saved in `life_threads_in_mind`.
  - Message 20 ("anyway, what should I even do with my saturday") still had it.
  - Message 21 ("random q, any good podcasts about space and black holes?") had `[1] Mum's visit` and `[2] Side project app`, both "Don't bring it up: you already brought it up in this Conversation".
  - The same search run on its own for message 21 (its meaning plus its 8 latest texts) found no Threads. So both came only from being kept in mind.
  - A new Conversation started with only the Thread its first message found.
- **Recall searches on the Understanding's meaning and the wider window:** `test_recall_searches_on_what_the_understanding_says_they_mean` (the text "ugh, not again" finds the knee Thread through the meaning alone), and `test_recall_searches_the_admin_set_number_of_their_recent_texts` (window 4: texts 3–6 are searched, text 2 isn't). Live: "my leg's been playing up on the long ones again so I've barely trained" brought Marathon training to mind. The Understanding read it as "a recurring leg problem that has disrupted their training". Closeness to the Thread was 0.632 on the words alone (just over the 0.62 bar) and 0.689 with the meaning added.
- **More than 3 Threads past the bar reach the Reply Plan, up to the cap:** `test_more_than_3_threads_past_the_bar_reach_the_reply_plan` (5 of 5), `test_the_admin_set_cap_limits_the_threads_one_search_brings_to_mind` (cap 4 → 4), and `test_the_cap_limits_the_threads_in_mind_at_once_keeping_this_messages_first` (cap 2: this message's Thread first, then the earliest one in mind; the other is left out). Live: "honestly everything is piling up. mum arrives friday, Priya dumped another project on me at Acme, the app launch slipped again and my sister still isn't talking to me" brought all 5 Threads to the Reply Plan. Its shape in the Model Call Log was `threads_reminded: 5, threads_left_alone: 2`.
- **Only Threads the Reply Plan picks reach the Reply:** `test_only_threads_the_reply_plan_picks_reach_the_reply` and `test_a_failed_reply_plan_gives_the_reply_no_threads`. Live, on the 5-Thread message:
  - The plan touched all 5 and left Mei and Mum's visit alone.
  - The Reply's "Ongoing stories" section held only the other 3 stories (app, Acme, Marathon). Mei and Mum's visit showed only as "Leave alone" lines, with no story.
  - On message 21 the plan picked no Thread, and the Reply got none.
- **The window and cap are Admin-editable with hints:** the `PlatformSettingsForm` test and `test_admin_settings.py` (a hint is required and at most two sentences). In the browser as an Admin, the Memory section of `/admin/settings` showed:
  - "Most Life Threads in mind" (10 threads), with the hint "How many Life Threads the Reply Plan can have in mind at once: …".
  - "Texts searched for Life Threads" (8 texts), with the hint "How many of the User's latest texts Recall searches Life Threads on, together with what the Understanding says they mean."
  - A change to 12 saved and was still there after a reload. It was then set back to 8. The page had no errors. Screenshots at 1280 and 390 match the rows around them.
- **One migration head:** 0072 (revises 0071) is the only new migration. No two migrations share a `down_revision`. `origin/main` was still at 550cbb9 when merging, so there was nothing to rebase. The stack's `alembic_version` reads 0072. `test_life_threads_in_mind_migration.py` checks that a stored cap still at the old 3 reloads from the seed (now 10) and that an Admin's own value is kept.
- **Docs:**
  - `docs/message-pipeline/README.md`: under 5. Recall, the "Today: searches on the User's last 3 texts, and caps Threads at 3" note is replaced by a "Built for Life Threads" note. The Reply Plan row of the Today table now says "the Threads in mind".
  - `CONTEXT.md` Life Thread: Threads are found by what the User means, a failed Reply Plan gives the reply none, and Admins set the number of texts searched and how many Threads can be in mind at once.
- **Design:** the new row uses the same `FieldRow`/`FieldNumber` as its neighbours. `node design/compare.cjs AdminPersona`: `FAIL 0.71%`, the same parts recorded in 06, 07 and 11 (this issue doesn't change that page). `AdminPersonaOutlook`: PASS 0.04%.
- **Checks** (final code): `uv run pytest` 1452 passed; `ruff check` "All checks passed!"; `ruff format --check` "553 files already formatted"; `mypy src` "Success: no issues found in 203 source files". `pnpm lint` and `pnpm typecheck` clean; `pnpm format:check` "All matched files use Prettier code style!"; `pnpm test` 887 passed in 131 files.
- **`/code-review`:**
  - Standards: no hard breaches. Fixed: the merge of found and in-mind Threads, which relied on dict order, is now a small pure helper `threads_in_mind`; the vague name `store` is now `life_thread_repository`; the docstring now covers a count of 0.
  - Spec: story 57 says "how many Threads … can be in mind at once". The first version capped only one message's search, so the cap now limits the whole set (test added) and CONTEXT.md is back to "in mind at once".

### Decisions and things to know

- **The order when over the cap:** the Threads this message found come first (open ones first, then named, then closest), then the earlier ones in the order they first came to mind. The earlier Threads that came to mind last are the ones left out. The cap is high (10), so this should rarely happen. A Thread left out for one message stays in the table and can come back later.
- **Setting key kept:** the cap is still stored as `life_threads_per_reply` (no rename migration), but its label is now "Most Life Threads in mind". Its allowed maximum went from 10 to 30.
- **Migration 0072 also deletes a stored `life_threads_per_reply` still at 3,** so it reloads from the new seed (10). A value an Admin changed stays.
- **A failed Reply Plan now gives the Reply no Threads.** Before, every reminded Thread that wasn't held back went in. With a wide memory that could be 10 stories, so the old test was replaced by `test_a_failed_reply_plan_gives_the_reply_no_threads`.
- **Names are matched in the User's texts only, not in the Understanding's meaning,** so words the Understanding uses can't pull in a Thread by name.
- **The fake Understanding's default meaning ("They're just saying hi.") now goes into the Thread search in tests.** Three tests in `test_life_threads.py` got a realistic meaning or a new Conversation between steps. Two tests that list the exact embedding searches (`test_knowledge_when_it_helps.py`, `test_older_summaries.py`) now expect the Thread search too.
- **The Reply Plan's heading** for the list is now "Life Threads in mind: those this message reminds you of, open ones first, then those from earlier in this Conversation". This is code, so no prompt migration was needed. `reply_plan_prompt` still says "the Life Threads this message reminds Zeph of", which is near enough; it can be updated with a prompt migration if wanted.
- **Not changed here:**
  - Patterns coming to mind is issue 14.
  - Move Outcomes still search the latest 3 texts.
  - The Conversation-end steps still find Threads from the whole Conversation, not from `life_threads_in_mind`.
- No Eval was run (Evals cost money).

## Completion

- Completed: 2026-11-20
- Commit: 0e27a5b "Merge message pipeline issue 12: wide recall" (merged into `main` locally and pushed), with:
  - bbae9b8 "Message pipeline issue 12: wide recall"
  - ef99387 "Message pipeline issue 12: review fixes"
  - 76f33df "Message pipeline issue 12 done: archive issue with test, run, pixel and review evidence"
