# 01 — Eval dashboard: Admins run and tune Evals from the Dashboard

Status: completed

## Idea (from the User, during the Understanding grilling, 14 Nov 2026)

Admins should have a quick, easy way to run Evals on demand from the Dashboard and see the results visually, as they come in. They should also be able to adjust the test cases, prompts and anything else the real platform has, so humans can steer and check the Companion without a redeploy.

## Decisions (grilling, 15 Nov 2026)

Terms are in `CONTEXT.md` (Eval Run, Eval Case, Variant, Setting Override, Make Live, Case Result, Model Price). The runner and database choice is ADR-0013.

**Scope and order.** One PRD, built as slices in this order: (a) run Evals and watch results come in, (b) a case's full trace, (c) edit Eval Cases, (d) Setting Overrides and Make Live, (e) Variants side by side. (a)+(b) are useful alone.

**Where it runs (ADR-0013).**
- A separate `eval-runner` service in Docker Compose, same image as the backend. The backend saves a run as Queued; the runner takes one at a time.
- Made-up data goes into a separate Eval database on the same Postgres server, wiped and re-seeded for each Variant. Must stay clearly apart from live data.
- Results and each case's full-content model calls go into Eval-only tables in the app database, tied to the run, never to a User. `model_calls` rows need a real User, so Eval traces are **not** in the Model Call Log; the Eval pages show them with the same trace view (`ModelCallTraceView`).
- The runner is always wired with the fake chat channel and fake web search (not a setting). No Check-in scheduler on the Eval database. Real LLM and embedder.
- Runner stops mid-run → run ends **Interrupted**, never retried by itself.

**`make eval`.**
- Eval checks move out of pytest into one core Eval runner. `make eval` queues a run on the local stack, prints each case as it finishes, then the report. Needs `make up` (or the worktree's own stack). Options like `EVALS=understanding`, `CASES=reminded-of-sister`.
- Each run records where it was started (Dashboard or terminal). The run list **hides terminal runs by default**, with a "Show terminal runs" toggle (terminal runs are mostly development and agents).

**Starting a run.**
- Any Admin. Pick whole Evals, or single cases inside one. **Re-run failed** on a finished run (includes Errors).
- **Repeats**: 1–5, default 1. A cell shows e.g. "2 of 3 passed"; each try can be opened.
- **Estimate** before starting: tokens and SGD, from the last run of those cases; first-time cases use a rough per-Eval figure. Counts all Variants and Repeats.
- **Eval run token limit**: a Platform Setting (default about 1M tokens). Crossing it ends the run **Stopped over limit**. Limit is in tokens so a missing price never breaks it.
- **Cancel** keeps finished cases. One run at a time; others wait Queued.
- Run states: Queued → Running → Finished / Cancelled / Interrupted / Stopped over limit.

**Live results.** The run page polls every 2 s while Queued or Running (TanStack Query, ADR-0012), stops when it ends. No websockets or SSE. Each case row appears when done: Pass / Fail / Error, the Judge's reason per rule, tokens, time.

**Case Results.** Pass, Fail (behaved wrongly) or Error (couldn't be checked; the error is shown). Errors don't count as fails, are shown apart, and the run carries on.

**Setting Overrides and Make Live.**
- On a run, an Admin can override any Platform Setting (prompt, Need, model, thinking on/off from issue 22, limit) for that run only. Written into the Eval database's settings; live settings never touched.
- The run keeps its overrides and shows them as a diff against live at the time.
- **Make Live** applies a Variant's overrides through the normal settings save (same checks), so nothing is retyped. Only on a **Finished** run, once per Variant.
- If a live value changed since the run started: show *live then*, *live now*, *override*; Admin confirms or leaves out each such setting. Unchanged ones apply straight away.
- The run shows "Made live by <Admin> at <time>" and what was applied or left out.

**Variants (side by side).**
- 1–3 Variants per run. Each is live settings, or live + its own overrides. A plain run has one.
- Every Variant runs the same cases; the runner goes case by case across Variants (case 1 on A, case 1 on B, …) so a cancelled run still compares fairly.
- Run page: a row per case, a column per Variant (pass/fail, tokens, time), plus totals (passes, tokens, SGD). Click a cell for the Judge's reasons and the full trace.

**Judge.**
- Judge model, thinking and prompts (hardcoded in `evals/judge.py` today) become Admin-managed (ADR-0004), seeded from a file, edited in the Eval area.
- Variants never change the Judge. The run snapshot keeps the Judge settings used.

**Eval Cases.**
- Admin-managed data (ADR-0004), one list per Eval: add, edit, duplicate, archive (archived kept so old runs still show them). Photo cases upload their images.
- **One form style for every Eval** — no YAML editor. Every field has a plain description of what it means and what changing it affects. Big cases (Understanding, Persona, Knowledge) are split into sections (made-up User Memory, earlier messages, Messages and what to expect).
- Each case has a stable key (e.g. `reminded-of-sister`). The seed (`evals/cases/*.yaml` today) adds cases whose key isn't in the database yet; it never overwrites an edited case or brings back an archived one. Dashboard edits don't go back to files.

**History.**
- Runs kept until an Admin deletes one. Each run saves a snapshot: full settings (live + overrides), Judge settings, each case's content at the time.
- Run list: when, who, Dashboard/terminal, Evals, Variants, pass counts, tokens, SGD.
- Case page: pass/fail in recent runs, marked where the case or settings changed between them.

**Model Prices.**
- A Platform Setting: SGD per 1M tokens in and out, per model. Admins enter SGD directly; no exchange-rate setting.
- Uses DeepSeek's **peak, cache-miss** price, so the estimate is an upper bound and labelled "estimate".
- Seed with DeepSeek's current names only (1 USD ≈ 1.28 SGD, 10 Nov 2026; [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing), checked 15 Nov 2026):
  - `deepseek-flash`: in 0.38, out 1.54 (USD 0.30 / 1.20)
  - `deepseek-v4-pro`: in 1.69, out 5.07 (USD 1.32 / 3.96)
- Old names (`deepseek-chat`, `deepseek-reasoner`) show "no price set"; issue 22 (`.scratch/understanding/issues/22-use-deepseek-flash-with-thinking-toggle.md`) moves the settings to `deepseek-flash`.

**Design.** No Eval pages in `docs/design/zeph-admin.html`, and no new design file: build from the existing admin pages' look and parts (Model Call Log, Knowledge, Prompts and Models). The first slice's `/run` sends screenshots for the User to approve before later slices copy the pattern. The whole platform gets redesigned once backend work is done.

## Depends on

- Model Call Log and its trace view, from the Understanding PRD (`.scratch/understanding/`).
- Issue 22 (deepseek-flash and the Thinking switch) should land first, so Model Prices and overrides use the current names.

## Next

`/to-prd`, then `/to-issues`. Evals cost money: the User is reminded before any eval run is planned or made.

## Comments

- 2026-11-15: PRD written at `.scratch/eval-dashboard/archive/PRD.md` (test seams agreed: backend HTTP API, "work the next Queued run", Dashboard components). Next: `/to-issues`.
- 2026-11-15: archived. Grilling done; decisions carried into `.scratch/eval-dashboard/archive/PRD.md` and issues 02-05.

## Completion

- Completed: 2026-11-15 (grilling issue; its decisions live in the PRD and issues 02-05, which hold the code)
- Commits:
  - `599cd9d` Eval dashboard issue 01 grilling: decisions, CONTEXT.md terms, ADR-0013
  - `bf47648` Eval dashboard issue 01: archive the grilling issue; links updated
- Merge commits:
  - `c73949d` Merge eval dashboard issue 01 grilling
  - `dee4951` Merge eval dashboard issue 01 archive
