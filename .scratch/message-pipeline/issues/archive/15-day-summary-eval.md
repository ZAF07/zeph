# 15 — Day Summary Eval

Status: completed
Lane: B
Blocked by: 02

## Parent

`.scratch/message-pipeline/PRD.md`. Design: `docs/message-pipeline/README.md`. Terms: `CONTEXT.md`.

## What to build

A new Eval (Evals run in their own service, ADR-0013; each case shape checks, saves and draws its form, ADR-0014). A Day Summary case gives a made-up day of messages and a set of questions with expected answers about the facts, the feelings and what Zeph offered and how it landed. The Eval writes the Day Summary with the real memory processing prompt, then the Judge answers each question from the Summary alone and checks it against the expected answer, giving a reason. A case passes only if every answer matches. Seed a few starting cases (e.g. a guilt-and-job-worry day like the 19 Nov review). Admins add and edit cases on the Dashboard like other Evals.

Evals cost money: build and test with the fake model; don't run a real Eval Run without the owner.

User stories covered: 66, 69.

## Design

Read `web/design/README.md` in full first, including "Message-pipeline additions (20 Nov 2026)".

- **Case form** (`/admin/evals/cases/day_summary/new`, reference `AdminEvalDaySummaryCase`): Key, The day (messages with From, Time, Text; Remove and "Add a message"), Questions (Question and Expected answer; Remove and "Add a question"), then "Add case". Editing a saved case drops the Key panel and the button reads "Save case".
- **A result on a run:** the Summary written, then each question with Expected, the Judge's answer, Match or Miss, and the Judge's reason, as in "How a result reads, on a run".
- **Fixtures:** the new case form opens filled in as drawn.

## Acceptance criteria

- [x] Day Summary cases can be created, edited, duplicated and archived on the Dashboard
- [x] A run writes the Summary with the live (or overridden) memory processing prompt and the Judge answers from the Summary only
- [x] A case fails when any answer misses, with the Judge's reason shown
- [x] Starting cases are seeded
- [x] Eval runner, case and Dashboard tests pass with the fake model
- [x] `node design/compare.cjs AdminEvalDaySummaryCase` prints PASS, and a run's result page reads as the drawn sample
- [x] Any new migration sits after the latest one on `main` when rebasing (the other lane adds migrations too): one migration head only
- [x] `CONTEXT.md` and `docs/message-pipeline/README.md` still describe what was built (update the "Today" notes that this changes)
- [x] Checks pass: `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy src`
- [x] Web checks pass: `pnpm lint`, `pnpm format:check`, `pnpm typecheck`, `pnpm test`
- [x] Verified in the running app with `/run`, evidence recorded under `## Comments`

## Blocked by

- 02 — One Day Summary per day, carrying feeling as well as facts (`.scratch/message-pipeline/issues/02-day-summaries.md`)

## Comments

Evidence (20 Nov 2026, branch `message-pipeline-15-day-summary-eval`, worktree stack on 3020/8020):

1. **Cases on the Dashboard** (`/run`, Playwright as an Admin on the real stack): the three seed cases are listed on `/admin/evals/cases/day_summary`. A new case `run-check-day` was added through the form; a Time of "teatime" was refused beside the field ("Write a time like 9:10 AM or 21:10.", with "The case has problems; see each field."), then saved with 6:40 PM and went back to the list. Edited (Save case → "Saved. The next run uses it; past runs keep the case as it was.", no Key panel on edit), duplicated as `run-check-day-copy`, archived ("Archived · Edited", View instead of Edit). No page errors. API tests: `test_an_admin_adds_edits_duplicates_and_archives_a_case_of_every_eval[day_summary]`, and the two Day Summary own-checks (unreadable time, times out of order).
2. **Run writes the Summary, Judge reads only it** (fake model; no paid run): `test_a_day_summary_case_writes_the_whole_day_s_summary_and_the_judge_reads_only_it`: a morning and an evening Conversation are both shown to the one memory processing call; the Judge's answering call holds the Summary (as later steps see it, "19 Nov 2026: … They seemed … Asked what came before…") and the questions, and not the messages or the expected answers; the marking call holds each Expected and the answer. The trace shows only the `conversation_end` step. `test_a_memory_processing_override_reaches_only_its_variant`: a Variant's `memory_processing_prompt` reaches only its Variant; live settings unchanged.
3. **Fails on any miss, with the reason**: `test_a_day_summary_case_fails_when_any_answer_misses_with_the_judge_s_reason`; also no Summary written → every question misses unjudged, and an unreadable Judge answer misses every question.
4. **Seed**: `seed/evals/cases/day_summary.yaml` (guilt-and-job-worry, first-10k-and-sore-knee, breathing-brushed-off), all fit the shape (`test_every_seed_case_fits_its_eval_s_case_shape`), seen on the running Dashboard.
5. **Pixel test**: `node design/compare.cjs AdminEvalDaySummaryCase` → `PASS 0.01% differs, height 2716 vs 2716`; rerun after the review fixes and rebase: "All pages match the design." Phone width (390) checked by eye: everything wraps, no sideways scroll. **Run result page**: a finished Day Summary result inserted into the worktree database (shaped as the runner saves it) opens at `/admin/evals/runs/<id>/results/<id>` with "Day Summary written", the Summary, then each question with Expected, "Judge’s answer, from the Summary alone", Match/Miss and "Judge’s reason.", as drawn.
6. **Migration**: none added; the two new Judge prompts (`day_summary_answer_instructions`, `day_summary_marking_instructions`) are seeded by the Judge settings' add-missing step, seen on `/admin/evals/judge` in the running app ("Day Summary answers prompt", "Day Summary marking prompt"). Head stays 0072 after rebasing.
7. **Docs**: `CONTEXT.md` (Eval and Judge entries), `docs/message-pipeline/README.md` (Built note under a. Day Summary), `evals/README.md` (eighth Eval, seed file).
8. **Checks**: `uv run pytest` 1465 passed; `ruff check`, `ruff format --check`, `mypy src` clean. Web: `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 892 passed, `pnpm build` OK.

Decisions:
- The owner chose to restyle **every** Eval case form to the drawn look, with a field's hint shown only when the backend gives one: back link instead of the Eval tabs, a section that is one list draws its entries straight in the panel, short fields (choice, number, date, time) side by side, panel-coloured inputs inside entries, "Add a message". Fields inside a list entry may have no hint (test relaxed for those only). New `time_of_day` field kind, checked by the shape.
- The Judge makes two calls per case so it never sees the expected answers while answering.
- The Day Summary step (`DayMemoryWriter`) was split out of the Conversation-end processor so the Eval runs it alone; the processor builds and calls it, with no wiring change.
- The day is saved split into Conversations at the quiet gap, on a fixed made-up day in UTC (the made-up User has no time zone).

Review (`/code-review`): fixed one hard violation (a second component in `ShapeFormSections.tsx`, now `SectionFields.tsx`), the duplicated Judge-call shape (one `ask_about_questions` helper), names (`calendar_time`, `MADE_UP_DAY`, `inputClassName`) and a time-zone trap (the case now reads the made-up User's newest Day Summary). Kept: the per-Eval registries (existing pattern), the fixture-only sample on the new-case page (the design README asks for it in fixture mode), and separate input class strings (Tailwind classes of equal weight can't override each other).

## Completion

- Completed: 2026-11-20
- Commit: `424b003` — Merge message pipeline issue 15: Day Summary Eval. A case is a made-up day of messages (From, Time, Text) and questions with expected answers. The day is saved split into Conversations at the quiet gap and the real Day Summary step alone (DayMemoryWriter, split out of the Conversation-end processor) writes its Summary with the live or overridden memory processing prompt, model and thinking. The Judge answers every question from the Summary alone, never shown the messages or the expected answers, then marks each Match or Miss with a reason; a case passes only if every answer matches. Two new Judge prompts, seeded without a migration. Three starting cases. A run's result shows the Summary and each question. Every Eval case form takes the drawn look (back link, one-list sections drawn in the panel, short fields side by side, hints only when given, a time-of-day field kind); ADR-0014 amended. No migration

