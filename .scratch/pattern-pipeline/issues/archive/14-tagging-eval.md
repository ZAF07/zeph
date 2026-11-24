# 14 — A Tagging Eval with its first cases, and the Pattern Evals guide

Status: completed
Track: B
Blocked by: 11

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 87, 89). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Everything downstream trusts the tagging step, so it gets its own Eval kind in the existing Eval runner. A case is a made-up Conversation (with any Life Threads it needs) plus the Observations expected: Pattern Type, for or against, unclear or not, situational or not. The real tagging step and code checks run on it. About 40 starting cases in a seed file, including ambiguous ones (must come back unclear), ones with nothing to tag (must come back empty) and ones anyone would do.

Also write `docs/pattern-evals/README.md`: the three layers of testing, what each can and can't show (a model playing a User and a model tagging them tend to agree), and what must be done later (a second rater, 200 labelled Observations, turning the score into a probability from Prediction outcomes, a psychologist's review). Evals cost money: remind the owner and show the estimate before any run.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [x] Tagging is an Eval kind Admins can run from the Dashboard and the terminal, with cases they can add and edit
- [x] A case passes only when the Observations kept match what was expected, and its result shows what was tagged and what was dropped
- [x] About 40 starting cases are seeded, covering clear, ambiguous, nothing-to-tag, against and anyone-would-do-it situations for the Pattern Types that exist
- [x] A Variant can override the tagging prompt, model and thinking switch
- [x] The run shows its cost estimate first
- [x] `docs/pattern-evals/README.md` exists and covers the layers, their limits and what must be done later
- [x] ~~The owner has corrected the drafted cases~~ moved to issue 20: the owner corrects them after the whole PRD is built (owner's decision, 24 Nov 2026); guide in `docs/pattern-evals/adding-tagging-cases.md`
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `11-tagging-step-keeps-observations.md`

## Comments

Plan (24 Nov 2026, branch `pattern-14-tagging-eval`, worktree `ai-chat-companion-pattern-14`):

- **New Eval kind `tagging`** in the existing runner, no Judge (code checks only). A case: `now`, the Life Threads the Conversation touched (title, story, people), the messages (`who`, `text`, a minute apart) and the Observations expected (Pattern Type ID, for or against, unclear, situational). The case form is drawn from its shape like every other Eval (ADR-0014).
- **Runs the real tagging step alone.** The made-up User gets Pattern noticing on and has pressed "Got it"; the Threads and the ended Conversation are saved; then `PatternTagger.tag_from` runs on them with the Eval database's Platform Settings, so a Variant can override `pattern_tagging_prompt`, `_model` and `_thinking`. The Eval database now loads the Pattern Catalog from its files for each case. No other Conversation-end step runs.
- **Pass rule.** Each expected Observation must be matched by a kept one with the same Pattern Type (when unclear, either of its two), direction, unclear and situational; and every kept one must match an expected one. An empty list means nothing may be kept. Several kept quotes for one expected Observation are fine.
- **What was dropped.** `plan_observations` also gives each dropped entry with why (unknown Pattern Type, unknown sign, quote not word for word, tag off its list, missing details, repeat). `tag_from` returns what it planned. The result's facts keep kept and dropped; the Case Result API gains a `tagging` part like `day_summary`, and the Dashboard shows it (new reference `AdminEvalTaggingCase.html`, built from the Day Summary case's parts).
- **Estimate first.** The Dashboard already shows it before starting; the terminal (`make eval`) now prints it before queueing. A rough per-case figure for Tagging is added.
- **Seed:** `seed/evals/cases/tagging.yaml`, about 40 cases over the three Pattern Types: clear for, against, unclear (two look-alikes), nothing to tag, and anyone-would (situational; only CONF.AVOID.BELONG has `anyone_would_when`).
- **Docs:** `docs/pattern-evals/README.md` (three layers, limits, later work, cost reminder), `evals/README.md` section, pattern-pipeline README built note.
- The owner correcting the drafted cases is theirs to do; it stays open until they comment.

Decisions made while building (24 Nov 2026):

- **Unclear matching:** an unclear expectation passes when its Pattern Type is either of the two kept; the other one isn't checked (logged in issue 20 in case the owner wants the pair checked).
- **"Anyone would" follows code:** code marks an Observation situational from its tags whatever its direction, so a CONF.AVOID.BELONG case about someone above the User expects situational, for or against (two seed cases fixed in review).
- **A step that never ran is an Error**, not a Fail: no tagging call at all (e.g. an empty catalog) raises a setup error; an unreadable answer is a Fail with an "answer read" check.
- **`TaggingMessage` kept apart from `EarlierLine`**: same fields, but `EarlierLine` means a line already in an open Conversation.
- **`make eval` prints the estimate first but doesn't stop to confirm** (it runs with no input); the Dashboard shows it before Start run.
- **Seed cases already in a database are never changed**, so the two review fixes reach new databases (and production) only.
- Left from review (judgement calls): the conversation-saving loop is now in three Evals, `last_call_facts` lives in `move_outcome_eval.py`, the design-sample page branches per Eval, and `evalDaySummaryFixtures` also serves the Tagging shape.

Evidence (24 Nov 2026, worktree stack on 3020/8020, real `deepseek-flash`, owner approved about S$0.20 of runs; build `d888e65`):

- **Dashboard and terminal, add and edit.** Signed-in Admin: Cases → Tagging lists the 44 seed cases; New run lists "Tagging · 44 cases". Run `4352910b` was started from the Dashboard (44 cases, finished). `make eval CASES=nothing-logistics` from the terminal: "Estimate: 1 case, about S$0.0007 at the live prices", then PASS, report "Tagging: 1 of 1 right". A case `run-check-typos-sister` was added through the New Tagging case form (date, two messages, From choices, one Observation) and saved as typed; Edit turned "Anyone would" on and "Saved. The next run uses it" showed, stored `situational: true`. Tests: `test_an_admin_adds_edits_duplicates_and_archives_a_case_of_every_eval[tagging]`, `test_the_terminal_runs_single_cases_and_prints_each_one`.
- **Pass rule and what was tagged and dropped.** Run `4352910b`: 33 passed, 11 failed (findings in issue 20); `conf-mum-holiday-plans` on the run page shows Expected "CONF.AVOID.BELONG · for · Not kept" and three kept quotes "Not expected" with Pattern Type and sign, who, Life Thread and context, at 1280 and 390, no sideways scroll, no page errors. The real model dropped nothing in any case, so drops were shown with the real Eval runner, Eval database, API and Dashboard and a scripted tagging answer (run `734363e0`, worked in the backend container): one kept, three "Dropped" with "quote not word for word in the User's own texts" (×2, one a Zeph quote) and "sign not among that Pattern Type's signs for or against". Tests: the six `tagging` tests in `test_eval_runner.py`, `test_each_dropped_entry_comes_back_with_why_it_was_dropped` (9 cases), `TaggingResultPanel.test.tsx`, `CaseResultCard.test.tsx`.
- **Seeded cases.** 44 in `eval_cases` after start-up: 6 CONF for, 3 against, 4 situational; 6 ACH for, 3 against, 1 anyone-would (nothing to tag); 6 CTRL for, 3 against, 2 real-crisis; 4 unclear; 1 with two Pattern Types; 5 nothing to tag. Test: `test_the_tagging_seed_covers_each_kind_of_case_for_every_pattern_type`.
- **Variant overrides.** Run `406b58b4`, 3 cases × Variants A and B, B overriding Pattern tagging prompt (a line added), thinking (off) and model (`deepseek-flash`, the only model available): `eval_model_calls` show A's 3 tagging calls with thinking on and the live prompt, B's 3 with thinking off and the changed prompt. Test: `test_tagging_overrides_reach_only_their_variant`.
- **Estimate first.** New run with Tagging ticked: "About 308,000 in / 39,600 out tokens · S$0.1780" above "Start run · 44 cases" (actual: 79,120 in / 76,318 out, S$0.1476; the rough figure is logged in issue 20). The Variant run showed per-Variant estimates from each case's last run. Terminal: the estimate line comes before "Queued Eval Run".
- **Guide.** `docs/pattern-evals/README.md`: the three layers, what each can and can't show (incl. a model playing a User and a model tagging tend to agree), later work (second rater, 200 labelled Observations, score to probability from Prediction outcomes, a psychologist's review) and the cost reminder. `evals/README.md` gains the Tagging Eval.
- **Design.** New `web/design/reference/AdminEvalTaggingCase.html` (built from the Day Summary case's parts), its baseline (`shoot.cjs` changed no other baseline) and lines in `routes.json` and `manifest.json`, as issues 10 and 13 did. Pixel test (git-ignored copy of `compare.cjs` blocking Clerk's protect probes): `PASS AdminEvalTaggingCase 0.00% differs, height 3797 vs 3797`, `PASS AdminEvalDaySummaryCase 0.00%`.
- **Checks.** `make check` on `c343765`: ruff clean, ruff format clean, mypy clean (239 files), pytest 1927 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 137 files, 948 tests passed. After review fixes (`d888e65`): ruff, format, mypy clean; the 184 eval and tagging tests passed; web typecheck, lint and the result tests passed.
- **Review.** Standards and spec reviews run. Fixed: one component per file, a step that never ran is an Error, one helper for named Pattern Types, two seed cases, import order. Left: see decisions above.
- **After rebase on main** (OpenRouter model names): the override test now uses `deepseek/deepseek-v4.1-flash`. `make check`: ruff, format, mypy clean (241 files), pytest 1945 passed; web 137 files, 952 tests passed. Rebuilt stack: `make eval CASES=nothing-weather-vent` PASS (S$0.0011).
- **Open:** the owner corrects the 44 drafted cases (owner's choice: merge now, keep this issue open until they comment).

Merged (24 Nov 2026): c4a6815 (merge "Merge pattern-14-tagging-eval: a Tagging Eval checks the real tagging step against expected Observations"; work in b225895 "Tagging Eval: the real tagging step checked against expected Observations", d4f5c95 "Tagging Eval: review fixes", 3857dd9 "Issue 14: evidence, findings for the owner; open for the owner's case review", c053cfd "CONTEXT: the Tagging Eval", d69944e "Tagging Eval: override test uses OpenRouter model names after rebase"). Not archived: open until the owner corrects the drafted cases in `src/companion/seed/evals/cases/tagging.yaml` (or on Admin → Evals → Cases → Tagging) and comments here; then tick the last box, set `completed`, archive.

Owner's decision (24 Nov 2026): the drafted cases are the defaults until the whole PRD is built; correcting them moves to issue 20, with a guide for doing it (`docs/pattern-evals/adding-tagging-cases.md`). Issue archived.

## Completion

- Completed: 2026-11-24
- Commit: c4a6815 (merge "Merge pattern-14-tagging-eval: a Tagging Eval checks the real tagging step against expected Observations"; work in b225895, d4f5c95, 3857dd9, c053cfd, d69944e) and 1f4caa8 (merge "Merge pattern-14-case-guide: how to correct and add Tagging cases; issue 14 archived"; work in 5cfba29 "Pattern Evals: guide for correcting and adding Tagging cases; owner step moves to issue 20, issue 14 archived")
