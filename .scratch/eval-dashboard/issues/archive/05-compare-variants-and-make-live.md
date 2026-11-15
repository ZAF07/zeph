# 05 — Runs lane: Setting Overrides, Variants side by side, Repeats and Make Live

Status: completed

## Parent

`.scratch/eval-dashboard/PRD.md`

## What to build

Lane A, after 03. An Admin tries changes before real Users get them, compares them side by side, and makes the winner live.

- **Setting Overrides:** on New run, any Platform Setting (prompt, Need, model, thinking on/off, limit) can be changed for one Variant only, in the same kind of fields as the settings pages. Written into the Eval database's settings for that Variant; live settings never touched. The Run page shows them as a difference from live at the time.
- **Variants:** 1–3 per run. A is live settings by default; B and C add their own overrides. Each Variant gets fresh made-up data. The runner goes case by case across Variants (case 1 on A, on B, then case 2…). The Judge is the same for every Variant.
- **Repeats:** 1–5 (default 1). Each case runs that many times per Variant; a cell shows e.g. "2 of 3 passed" and each try can be opened.
- **Grid:** a row per case, a column per Variant (outcome, tokens, time), totals per Variant (passes, tokens, time, SGD). A cell opens that Variant's reasons and trace.
- **Estimate and token limit** count all Variants and Repeats. Re-run failed keeps the same Variants and Repeats.
- **Make Live:** on a Variant of a Finished run, once per Variant. Applies its overrides through the normal Platform Settings save (same checks). If a setting's live value changed since the run started, show the value then, now and the override, and let the Admin confirm or leave out each one; unchanged ones apply straight away. The run shows who made it live, when, and what was applied or left out.

## Acceptance criteria

- [x] An override changes only its Variant's run; live settings are unchanged after the run (test) (`test_an_override_changes_only_its_variant_and_every_variant_has_the_same_judge`, `test_a_need_override_reaches_only_its_variant_and_live_needs_stay`; `/run`: Platform Settings and Needs fingerprints identical before and after the real run)
- [x] A run with 3 Variants and Repeats 3 runs every case 3 times per Variant, case by case across Variants (`test_three_variants_with_three_repeats_run_case_by_case_across_variants`: 18 results in case → try → Variant order; `/run`: case 1 on A then B as the grid filled)
- [x] Variants never share made-up data; all use the same Judge (`test_every_variant_and_try_starts_from_fresh_made_up_data`; same Judge model, thinking and prompt in `test_an_override_changes_only_its_variant…`; `/run`: 24 results, 24 different made-up Users)
- [x] The grid shows per-Variant outcomes and totals, and opens each try's reasons and trace (`EvalRunView.test.tsx` "comparing Variants"; `/run` screenshot: 12 rows × A/B, totals A 12/0 99.6 s S$0.0392, B 11/1 63.1 s S$0.0293, picked cell shows its card with Full trace)
- [x] Estimate and token limit include all Variants and Repeats (`test_the_estimate_counts_every_variant_and_repeat`, `test_the_token_limit_counts_every_variant_and_repeat`; `/run`: Repeats 3 estimate 864,000 in = 3 × Repeats 1's 288,000, per Variant shown)
- [x] Make Live works only on Finished runs, once per Variant, through the normal settings checks (`test_make_live_applies_the_overrides_once…`, `test_make_live_needs_a_finished_run_and_a_variant_with_overrides`, `test_a_variant_is_marked_made_live_only_once`, `test_a_refused_make_live_changes_nothing_and_can_be_tried_again`; overrides go through `PlatformSettingsService.checked_value` and `NeedService.checked`)
- [x] A live setting changed since the run is shown for confirm or leave out; the run records who, when and what (`test_a_setting_changed_live_since_the_run_is_applied_only_if_confirmed`; `/run`: daily limit changed live to 150, confirm showed 200 / 150 / 80, left out; thinking applied; Variant B shows "Made live by Run check, 15 Nov, 20:21. Applied: Understanding thinking. Left out…: Daily message limit.")
- [x] Tests at the API, at "work the next Queued run", and Dashboard component tests (`tests/test_eval_runs.py`, `tests/test_eval_runner.py`; `NewEvalRunForm.test.tsx`, `EvalRunView.test.tsx`, `setting-overrides.test.ts`, `eval-run-grid.test.ts`)
- [x] Verified at `/run`, including a real comparison of Understanding thinking on vs off (remind the User first: evals cost money) (User approved up to S$0.50; estimate S$0.16, real S$0.0685. A thinking on: 12/12, 62,980 in / 9,941 out, 99.6 s, Understanding calls avg 4.1 s. B thinking off: 11/12, 62,547 in / 3,590 out, 63.1 s, avg 1.4 s; `reminded-of-sister` failed: didn't bring up the falling-out with Mei. Re-run failed queued just that case with the same Variants and Repeats (runner stopped, then cancelled, so no cost). 390 px: no page-wide scroll, grid scrolls in its box)
- [x] `make check-python` and `make check-web` pass (1087 Python tests, ruff, ruff format, mypy; 424 web tests, eslint, prettier, tsc)

## Blocked by

- `03-cost-traces-re-runs-and-history.md`
- `.scratch/understanding/issues/22-use-deepseek-flash-with-thinking-toggle.md` (thinking on/off as an override)

## Comments

- 2026-11-15 (implementing, branch `eval-dashboard-05-variants`): plan.
  - Start run takes `variants` (1–3 lists of Setting Overrides, lettered A, B, C) and `repeats` (1–5). Each override is checked with the same checks as the settings save, so a run can't try a value the settings page would refuse. Model Prices and the token limit can't be overridden (they don't change results).
  - Need overrides: key `need:<id>`, value `{name, when_it_fits, how_to_reply}`; a Variant edits existing Needs only (no adding or removing). For this the run snapshot keeps the live Needs, and the Eval database gets the live Needs instead of the seed's, so Evals use what Users get.
  - Runner order: for each case, for each try, for each Variant (case 1 try 1 on A, B, C; case 1 try 2 on A, B, C; …), so a cancelled run still compares fairly. Every case still gets fresh made-up data.
  - Estimate: each case's figure × Repeats, per Variant, plus the total. The token limit already counts every result.
  - Re-run failed copies the Variants and Repeats; a case is re-run if any try on any Variant failed or errored.
  - Run detail adds totals per Variant (passes, tokens, time, SGD).
  - Make Live: one check call lists overridden settings whose live value changed since the run (then, now, override); one apply call takes the changed ones the Admin confirms, applies them with every unchanged one through the normal settings and Need saves, and records who, when, applied and left out. Only Finished runs, only Variants with overrides, once per Variant. On the Dashboard it is one click when nothing changed.
  - Migration 0045: `eval_runs.needs_snapshot`; `eval_variants` gets `made_live_by`, `made_live_at`, `applied_keys`, `left_out_keys`.
  - Dashboard: New run gets Repeats and Variants with an override editor (pick a setting or Need, edit it in a field of its kind, starting from the live value). The Run page gets a Variants panel (overrides as a diff from live then, Make Live and its confirm step) and a grid (row per case, column per Variant, "2 of 3 passed", each try linking to its reasons and trace, totals per Variant).
- 2026-11-15 (done):
  - Built as planned. Review fixes: Make Live marks the Variant made live in one conditional update before saving and takes the mark off if the save is refused, so two Admins can't both apply it; a Variant changing a Need deleted before its run started ends its cases as Errors; Re-run failed checks the copied overrides again; the override choices are listed by the core (`SettingOverrideService`).
  - Known limits, left as they are: the estimate for a case that ran before uses its newest result's tokens whatever Variant made them, so a model or thinking override isn't reflected (only never-run cases use the Variant's reply model); an override equal to the live value is accepted and shown; a setting changed live between the check and Make Live is left out (and recorded as left out); Make Live is one click when nothing changed since the run; if a database error stops Make Live after some Needs are saved, those stay saved (checks run first, so a refused value never gets that far).

## Completion

- Completed: 2026-11-15
- Commits (branch `eval-dashboard-05-variants`):
  - `f634777` Eval dashboard issue 05: Variants, Repeats, Setting Overrides and Make Live in the backend
  - `f9a73e9` Eval dashboard issue 05: Dashboard Variants, Repeats, run grid and Make Live
  - `0fe0daa` Eval dashboard issue 05: review fixes (Make Live marks once in one step, deleted Need is an Error, re-run re-checks overrides, choices in core, less duplication)
  - `cd0de9f` Eval dashboard issue 05: CONTEXT.md and evals README on Variants, Repeats, Need overrides and Make Live
  - `9e693a5` Eval dashboard issue 05: test that the token limit counts every Variant and Repeat
- Archive commit: `65b1a07` Eval dashboard issue 05 done: archive issue with run, eval, review and check evidence
- Merge commit: `abb4d5c` Merge eval dashboard issue 05: Variants side by side, Repeats, Setting Overrides and Make Live

