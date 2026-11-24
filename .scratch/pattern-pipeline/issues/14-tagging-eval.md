# 14 — A Tagging Eval with its first cases, and the Pattern Evals guide

Status: in-progress
Track: B
Blocked by: 11

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 87, 89). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Everything downstream trusts the tagging step, so it gets its own Eval kind in the existing Eval runner. A case is a made-up Conversation (with any Life Threads it needs) plus the Observations expected: Pattern Type, for or against, unclear or not, situational or not. The real tagging step and code checks run on it. About 40 starting cases in a seed file, including ambiguous ones (must come back unclear), ones with nothing to tag (must come back empty) and ones anyone would do.

Also write `docs/pattern-evals/README.md`: the three layers of testing, what each can and can't show (a model playing a User and a model tagging them tend to agree), and what must be done later (a second rater, 200 labelled Observations, turning the score into a probability from Prediction outcomes, a psychologist's review). Evals cost money: remind the owner and show the estimate before any run.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [ ] Tagging is an Eval kind Admins can run from the Dashboard and the terminal, with cases they can add and edit
- [ ] A case passes only when the Observations kept match what was expected, and its result shows what was tagged and what was dropped
- [ ] About 40 starting cases are seeded, covering clear, ambiguous, nothing-to-tag, against and anyone-would-do-it situations for the Pattern Types that exist
- [ ] A Variant can override the tagging prompt, model and thinking switch
- [ ] The run shows its cost estimate first
- [ ] `docs/pattern-evals/README.md` exists and covers the layers, their limits and what must be done later
- [ ] The owner has corrected the drafted cases (comment on this issue when done)
- [ ] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

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
