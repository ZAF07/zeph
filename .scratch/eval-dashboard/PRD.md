# PRD: Eval dashboard — Admins run, tune and compare Evals from the Dashboard

Status: ready-for-agent

## Problem Statement

Admins can't see how the Companion behaves with the real LLM without a developer.

- Evals only run from the terminal (`make eval`), as pytest tests on a developer's machine. Admins can't start one, watch it, or look back at past results.
- Nothing is kept. A run prints a report and is gone, so nobody can tell whether a prompt or model change made things better or worse over time.
- Eval Cases live in YAML files. Adding or fixing a case needs a code change and a developer.
- An Admin can only find out what a new prompt, Need, model or thinking switch does by saving it live, so real Users get it before anyone has checked it.
- Comparing two choices (for example the Understanding call with thinking on vs off, or `deepseek-flash` vs `deepseek-v4-pro`) means running Evals twice by hand and reading two terminal reports side by side.
- Nobody knows what a run will cost before it starts, and nothing stops a run that costs far more than expected.
- The Judge's model and prompts are hardcoded, against ADR-0004.

## Solution

An Eval area in the Dashboard's admin section.

- An Admin picks whole Evals or single Eval Cases, sees an estimate of tokens and SGD, and starts an Eval Run. Case Results appear as they finish: Pass, Fail or Error, the Judge's reason for each rule, tokens and time. Any Case Result opens its full trace.
- A run can have up to three Variants: the live Platform Settings, or the live ones changed by Setting Overrides. Every Variant runs the same cases, shown side by side. Repeats (1–5) show how steady a result is.
- When a Variant is better, Make Live applies its Setting Overrides to the live Platform Settings in one click, with a check for settings someone else changed since the run started.
- Admins add, edit, duplicate and archive Eval Cases in forms that explain every field. The Judge's model, thinking and prompts are Admin-managed too.
- Runs are kept with a snapshot of everything they used, so Admins can compare them over time and see each case's history.
- A token limit per run, a Cancel button and Model Prices in SGD keep cost in check.
- Runs work in a separate `eval-runner` service against a separate Eval database (ADR-0013), so made-up Users never mix with real ones and Eval load never slows real replies. `make eval` queues a run the same way, so the terminal and the Dashboard run the same thing.

## User Stories

**Starting a run**

1. As an Admin, I want to start an Eval Run from the Dashboard, so that I can check the Companion without a developer.
2. As an Admin, I want to pick whole Evals for a run, so that I can check one area (such as the Safeguard) at a time.
3. As an Admin, I want to pick single Eval Cases inside an Eval, so that I can re-check one case I care about without paying for the rest.
4. As an Admin, I want to see an estimate of a run's tokens and SGD before it starts, so that I don't spend more than I meant to.
5. As an Admin, I want the estimate to be based on the last run of the same cases, so that it is close to what the run will really cost.
6. As an Admin, I want cases that have never run to use a rough figure for their Eval, so that a new case still gets an estimate.
7. As an Admin, I want the estimate to count every Variant and Repeat, so that a comparison doesn't surprise me with its cost.
8. As an Admin, I want the estimate labelled as an estimate at DeepSeek's highest price, so that I know real costs will be the same or lower.
9. As an Admin, I want to set how many times each case runs (Repeats, 1–5), so that I can tell a steady result from luck.
10. As an Admin, I want a run I start while another is running to wait as Queued, so that runs don't compete and costs stay predictable.
11. As an Admin, I want any Admin to be able to start a run, so that the whole Admin team can check changes.

**Watching a run**

12. As an Admin, I want Case Results to appear as each case finishes, so that I don't wait six minutes to see the first result.
13. As an Admin, I want to see a run's state (Queued, Running, Finished, Cancelled, Interrupted, Stopped over limit), so that I know whether it is still going and how it ended.
14. As an Admin, I want each Case Result to show Pass, Fail or Error, so that I can tell wrong behaviour from a case that couldn't be checked.
15. As an Admin, I want to see the Judge's reason for each rule of a case, so that I understand why it passed or failed.
16. As an Admin, I want each Case Result to show its tokens and time, so that I can spot slow or costly cases.
17. As an Admin, I want an Error to show what went wrong (for example the model didn't answer), so that I can tell it apart from a real failure.
18. As an Admin, I want an Error not to count as a Fail in the totals, so that a network hiccup doesn't make the Companion look worse.
19. As an Admin, I want a run to carry on after one case errors, so that one bad case doesn't waste the rest of the run.
20. As an Admin, I want running totals (passes, tokens, SGD) per Variant, so that I can see how it is going at a glance.
21. As an Admin, I want to cancel a run and keep the cases already done, so that I can stop a run I don't need without losing what it found.
22. As an Admin, I want a run to stop by itself when it crosses the Eval run token limit, so that a mistake can never cost a lot.
23. As an Admin, I want to set the Eval run token limit, so that I can raise it for a big comparison or lower it to be careful.
24. As an Admin, I want a run that stopped unexpectedly (for example the runner restarted) to show as Interrupted and never restart by itself, so that I decide whether to spend money on it again.

**Traces**

25. As an Admin, I want to open any Case Result's full trace (what each model was given, what it answered, its tool calls and its reasoning), so that I can see exactly why the Companion did what it did.
26. As an Admin, I want the trace to look like the Model Call Log's trace view, so that I don't have to learn a second view.
27. As an Admin, I want to see each Understanding call's time and tokens in a trace, so that I can judge whether a slower model is worth it.

**Re-running**

28. As an Admin, I want a Re-run failed button on a finished run, so that I can check a fix on just the cases that went wrong.
29. As an Admin, I want Re-run failed to include Errors, so that cases that couldn't be checked get another go.
30. As an Admin, I want a re-run to use the same Variants and Repeats as the original, so that its results compare fairly.

**Setting Overrides**

31. As an Admin, I want to change any Platform Setting for one run only (a prompt, a Need, a model, thinking on or off, a limit), so that I can try a change before real Users get it.
32. As an Admin, I want Setting Overrides never to touch the live Platform Settings, so that trying something is always safe.
33. As an Admin, I want a run to show its Setting Overrides as a difference from the live settings at the time, so that I can see exactly what was tried.
34. As an Admin, I want overrides edited in the same kind of fields as the normal settings pages, so that I don't need to learn anything new.

**Variants**

35. As an Admin, I want to add up to three Variants to a run, so that I can compare choices side by side in one go.
36. As an Admin, I want each Variant to be the live settings or the live settings plus its own overrides, so that I can always compare a change against what Users get today.
37. As an Admin, I want every Variant to run the same cases the same number of times, so that the comparison is fair.
38. As an Admin, I want cases to run across Variants one case at a time (case 1 on A, then on B, then case 2…), so that a cancelled run still gives a fair comparison of the cases done.
39. As an Admin, I want each Variant to start from fresh made-up data, so that one Variant can't affect another.
40. As an Admin, I want a grid with a row per case and a column per Variant, so that I can see at once where they differ.
41. As an Admin, I want totals per Variant (passes, tokens, time, SGD), so that I can weigh quality against cost.
42. As an Admin, I want every Variant in a run marked by the same Judge, so that a difference comes from the Companion and not from the Judge.
43. As an Admin, I want to click a grid cell to see that Variant's reasons and trace for that case, so that I can see why they differ.
44. As an Admin, I want a cell to show for example "2 of 3 passed" when Repeats is more than 1, and open each try, so that I can see which tries failed.

**Make Live**

45. As an Admin, I want a Make Live button on a Variant of a finished run, so that I can apply what worked without retyping it.
46. As an Admin, I want Make Live to go through the same checks as saving the settings page, so that it can't save something the settings page would refuse.
47. As an Admin, I want Make Live only on Finished runs, so that I don't make live something that wasn't fully checked.
48. As an Admin, I want Make Live to warn me when a live setting changed since the run started, showing the value then, the value now and the override, so that I don't overwrite another Admin's change by accident.
49. As an Admin, I want to confirm or leave out each changed setting one by one, so that I keep the other Admin's change where it matters.
50. As an Admin, I want settings that didn't change since the run to be applied straight away, so that Make Live is quick in the usual case.
51. As an Admin, I want the run to show who made it live, when, and which settings were applied or left out, so that the team knows where a live setting came from.
52. As an Admin, I want Make Live to be possible only once per Variant, so that the same change isn't applied twice by mistake.
53. As an Admin, I want a change made live to apply from the next reply or Check-in, like any saved Platform Setting, so that a reply under way isn't changed halfway.

**Eval Cases**

54. As an Admin, I want a list of each Eval's cases, so that I can see what is being checked.
55. As an Admin, I want to add an Eval Case, so that I can check a situation I saw go wrong.
56. As an Admin, I want to edit an Eval Case, so that I can fix a case that expects the wrong thing.
57. As an Admin, I want to duplicate an Eval Case, so that I can make a similar case quickly.
58. As an Admin, I want to archive an Eval Case instead of deleting it, so that past runs still show it.
59. As an Admin, I want every Eval's cases edited in the same style of form, so that I never need to read or write YAML.
60. As an Admin, I want every field to explain what it means and what changing it affects, so that I can edit a case without knowing the code.
61. As an Admin, I want big cases (Understanding, Persona, Knowledge) split into sections (made-up User Memory, earlier messages, Messages and what to expect), so that they are easy to follow.
62. As an Admin, I want a case form to tell me clearly what is wrong when I save something invalid, so that I can fix it.
63. As an Admin, I want to upload the images for photo cases, so that I can add photo cases myself.
64. As an Admin, I want each case to have a stable key (such as `reminded-of-sister`), so that it can be found and picked in runs and in the terminal.

**Seeding cases**

65. As a developer, I want new cases I add to the seed files to appear on the Dashboard, so that cases written with code still reach Admins.
66. As an Admin, I want the seed never to overwrite a case I edited, so that my changes are safe.
67. As an Admin, I want the seed never to bring back a case I archived, so that archiving sticks.

**Judge**

68. As an Admin, I want to set the Judge's model, thinking and prompts, so that I can improve how cases are marked without a developer.
69. As an Admin, I want Judge settings explained in the same kind of form as cases, so that I know what I'm changing.
70. As an Admin, I want each run to keep the Judge settings it used, so that I know which Judge marked old results.

**History**

71. As an Admin, I want a list of past runs with when, who, where it started, Evals, Variants, pass counts, tokens and SGD, so that I can find and compare runs.
72. As an Admin, I want runs started from the terminal hidden by default, with a toggle to show them, so that development and agent runs don't clutter my list.
73. As an Admin, I want each run to keep what it used (the Platform Settings, overrides, Judge settings and each case as it was), so that later changes never change its results.
74. As an Admin, I want to open a case and see whether it passed or failed in recent runs, so that I can see whether it is getting better or worse.
75. As an Admin, I want a case's history to mark where the case or the settings changed between runs, so that I can tell what caused a change in results.
76. As an Admin, I want to delete a run, so that I can remove runs I no longer need.
77. As an Admin, I want runs kept until an Admin deletes them, so that I can look back as far as I need.

**Model Prices**

78. As an Admin, I want to set each model's price in SGD per million tokens in and out, so that estimates and totals show real money.
79. As an Admin, I want a model with no price to show tokens only, marked "no price set", so that a missing price is obvious but never blocks a run.
80. As an Admin, I want prices seeded for `deepseek-flash` and `deepseek-v4-pro`, so that costs show from the first run.

**Safety and separation**

81. As an Admin, I want made-up Users, messages and documents from Evals kept fully apart from real Users and their data, so that live data is never touched or cluttered.
82. As an Admin, I want an Eval never to message a real chat, so that no real User ever gets an Eval's reply.
83. As an Admin, I want an Eval never to use real web search, so that it doesn't spend search credits.
84. As an Admin, I want no Check-ins sent to made-up Users, so that the Eval database never sends anything.
85. As an Admin, I want Eval traces not to show in the Model Call Log, so that the log only shows real use.
86. As a User, I want Eval runs not to slow down the Companion's replies to me, so that my chats aren't affected by Admins' testing.
87. As a User, I want my data never used in an Eval, so that my privacy is kept.

**Terminal**

88. As a developer, I want `make eval` to queue a run on the local stack and print each case as it finishes, then the same report as today, so that the terminal and the Dashboard give the same results.
89. As a developer, I want to pick Evals or cases from the terminal (`EVALS=understanding`, `CASES=reminded-of-sister`), so that I can check just what I changed.
90. As a developer or agent, I want `make eval` to work in my worktree against the worktree's own stack, so that parallel work doesn't share runs or databases.
91. As a developer, I want `make eval` to tell me clearly when the stack isn't running, so that I know to run `make up`.

## Implementation Decisions

**Process and storage (ADR-0013)**

- A new `eval-runner` service in Docker Compose, built from the backend image with a different command. It loops: take the oldest Queued Eval Run (one at a time, safe if two runners start), work it, repeat.
- At start-up, the runner marks any run still Running as Interrupted.
- A separate Eval database on the same Postgres server. For each Variant the runner wipes it, runs migrations, seeds it, then writes the Variant's Platform Settings (live snapshot + Setting Overrides) into it. Worktrees get their own Eval database alongside their own app database.
- The runner builds the app the way Evals do today: real chat model, real embedder and photo viewer, **fake chat channel and fake web search always**, no Check-in scheduler. This wiring is fixed in code, not a setting.
- Model calls during an Eval keep full content (the Model Call Log already supports content for everyone in an Eval run). After each case, the runner copies that case's model calls from the Eval database into the app database's Eval tables.
- The runner checks Cancel and the token limit between cases (and between Messages within an Understanding case), so a run stops within one case.

**Modules**

- **Eval runner (core, new, deep):** one public entry, "work the next Queued run". It owns the run's state changes, the case-by-case loop across Variants and Repeats, the token limit, Cancel and writing Case Results. It depends on ports only: a port to prepare the Eval database for a Variant and give back the app built on it, the app's repositories for runs, cases and results, the chat model (for the Judge) and the clock.
- **Eval checks (core, new):** the six Evals' checks, moved from the pytest files: Safeguard, Persona, Knowledge, Settings, Photo description and Understanding. Each takes a case and the app built on the Eval database and returns a Case Result (Pass/Fail/Error, reasons per rule, tokens, time). An unexpected exception becomes an Error with its message.
- **Judge (core, moved):** reads its model, thinking and prompts from Eval settings instead of constants.
- **Eval Runs service (core, new):** start a run (with Evals or case keys, Variants with Setting Overrides, Repeats), estimate, cancel, delete, list (with or without terminal runs), run detail with Case Results, Re-run failed.
- **Make Live (core, new):** applies a Variant's Setting Overrides through the Platform Settings save that the settings page uses. It compares each setting's live value now with the run's snapshot and returns the changed ones for the Admin to confirm or leave out; a second call with the Admin's choices applies them.
- **Eval Cases service (core, new):** list per Eval, add, edit, duplicate, archive. Each Eval has a typed case shape (one per Eval) used to check a save and to drive the form.
- **Eval case seed (new):** on start-up, adds cases from the seed files whose key isn't in the database; never updates an existing or archived case.
- **Model Prices and Eval run token limit:** new Platform Settings, seeded (`deepseek-flash` 0.38 / 1.54, `deepseek-v4-pro` 1.69 / 5.07 SGD per 1M tokens in / out; limit about 1,000,000 tokens).
- **HTTP adapter:** admin-only routes for runs, estimate, cancel, Make Live, cases, Judge settings and Model Prices. Core errors map to status codes once (ADR-0011).
- **`make eval`:** a small terminal client that calls the backend's admin API with a dev Admin, starts a run marked "terminal", polls and prints results, and exits non-zero if any case failed or errored.

**Schema (new Eval-only tables in the app database)**

- Eval Case: key (unique), Eval, content (JSON in the Eval's case shape), archived, edited, created/updated by and when.
- Eval Run: who, where started (Dashboard or terminal), state, Repeats, chosen case keys, live settings snapshot, Judge settings snapshot, token limit, started/finished, tokens used.
- Variant: run, letter, Setting Overrides, made live by/at, applied and left-out settings.
- Case Result: run, Variant, case key, try number, case content as it was, outcome, reasons per rule, error, tokens, time.
- Eval model call: Case Result, and the same fields as a Model Call Log row (including full content), with no User.
- Images uploaded for photo cases are kept with the case.

**API shape**

- Start run: Evals and/or case keys, Repeats, Variants (each a list of Setting Overrides), where started. Returns the run.
- Estimate: the same input as start, returns tokens and SGD per Variant and in total, and which models have no price.
- Run detail: state, totals per Variant, and Case Results so far. The Dashboard polls it every 2 seconds while Queued or Running (TanStack Query, ADR-0012) and stops when it ends.
- Make Live: first call returns the settings whose live value changed since the run; second call takes which to apply.

**Dashboard**

- Pages: Runs list, New run, Run page (grid and Make Live), Case result trace, Eval Cases list and form per Eval, case history, Judge settings, Model Prices.
- Built from the existing admin pages' look and parts (Model Call Log, Knowledge, Prompts and Models). The trace reuses the Model Call Log's trace view component. No new design file; the first slice's `/run` sends screenshots for the User to approve first.
- All calls go through the API client module; no business logic in the Dashboard.

**Order of slices**

(a) run Evals and watch results come in, terminal included; (b) a Case Result's full trace; (c) edit Eval Cases and Judge settings; (d) Setting Overrides and Make Live; (e) Variants and Repeats side by side. History and Model Prices land with the slice that first needs them.

## Testing Decisions

- A good test checks what an Admin (or the terminal) sees through the API, not how the runner works inside. Tests never call the real LLM.
- **Seam 1, the backend HTTP API** (existing, like the admin settings tests): start, cancel, list, delete and Re-run failed; the estimate; Eval Cases add/edit/duplicate/archive and their checks on save; Judge settings; Model Prices; Make Live including changed live settings and "only Finished, once per Variant"; terminal runs hidden by default; admin-only access. Uses the test client, the scripted chat model and a test Postgres.
- **Seam 2, "work the next Queued run"** (new, the one call the runner loops on): start a run via the API, call it once in-process with the scripted chat model and a test Eval database, then read the results via the API. Covers each Eval's Pass/Fail/Error, Errors not stopping the run, the token limit, Cancel between cases, Interrupted at start-up, Variants getting their own settings and fresh data, Repeats, the case-by-case order across Variants, live settings untouched by overrides, no messages to a real chat, and the case seed's never-overwrite rule.
- **Seam 3, Dashboard components** (existing, Vitest + React Testing Library with the API client mocked, like the admin usage and Check-in kinds tests): the new-run form and estimate, the run grid filling in while polling and stopping at the end, Make Live's confirm step, the case forms and their field descriptions, the terminal-runs toggle.
- **Real-LLM:** only `make eval` itself, never in `make check`, because it costs money. Each slice that changes behaviour does one `make eval` run after reminding the User of the cost, and its results must be no worse than the run before.
- Prior art: the admin settings and Model Call Log API tests, the eval helper tests, the existing Eval checks (which move rather than get rewritten), and the Dashboard admin component tests.

## Out of Scope

- A general background job queue for other work (replies, Check-ins); that stays with the scaling issue.
- Running more than one Eval Run at a time.
- Exchange rates or prices in any currency but SGD; off-peak and cache-hit prices.
- Writing Dashboard case edits back to the seed files.
- A YAML or raw editor for cases.
- Scheduled or automatic Eval Runs (for example after every settings change).
- Eval results in the Model Call Log.
- Using real Users' data in Evals.
- A new visual design; the whole platform is redesigned later.
- Moving models to `deepseek-flash` and the Thinking switch (issue 22 in `.scratch/understanding/`).

## Further Notes

- Issue 22 (`deepseek-flash` and the Thinking switch per call) should land first, so Setting Overrides include thinking and the seeded Model Prices match the model names in use. Until then old model names show "no price set".
- Prices from DeepSeek's pricing page (checked 15 Nov 2026), at peak, cache miss, at 1 USD ≈ 1.28 SGD (10 Nov 2026): `deepseek-flash` USD 0.30 / 1.20, `deepseek-v4-pro` USD 1.32 / 3.96 per 1M tokens in / out. DeepSeek may change them; Admins update the setting.
- Cases are already data files (`evals/cases/*.yaml`), so they become the seed without a rewrite.
- The platform isn't live yet, so no backfill of old terminal runs is needed.
- Grilling decisions: `.scratch/eval-dashboard/issues/archive/01-run-evals-from-the-dashboard.md`.
