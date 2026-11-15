# 05 — Runs lane: Setting Overrides, Variants side by side, Repeats and Make Live

Status: in-progress

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

- [ ] An override changes only its Variant's run; live settings are unchanged after the run (test)
- [ ] A run with 3 Variants and Repeats 3 runs every case 3 times per Variant, case by case across Variants
- [ ] Variants never share made-up data; all use the same Judge
- [ ] The grid shows per-Variant outcomes and totals, and opens each try's reasons and trace
- [ ] Estimate and token limit include all Variants and Repeats
- [ ] Make Live works only on Finished runs, once per Variant, through the normal settings checks
- [ ] A live setting changed since the run is shown for confirm or leave out; the run records who, when and what
- [ ] Tests at the API, at "work the next Queued run", and Dashboard component tests
- [ ] Verified at `/run`, including a real comparison of Understanding thinking on vs off (remind the User first: evals cost money)
- [ ] `make check-python` and `make check-web` pass

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

