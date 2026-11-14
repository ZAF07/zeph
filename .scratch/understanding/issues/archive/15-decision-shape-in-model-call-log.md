# 15 — Decision shape in the Model Call Log

Status: completed

## Parent

`.scratch/understanding/PRD.md`

## What to build

The Model Call Log's Understanding entry shows the shape of the decision, never the words: the Need picked, the mood intensity and whether the cause was known, how many Life Threads were reminded, how many were brought up (and lead or weave), how many were left alone, how many held back, and how many `look_up_past` phrases were asked for. This is for every User, as ADR-0010 and PRD story 68 promise ("Need picked, how many Threads found, whether one was raised, which tools were called").

Today the decision shape is only the tools called. Issue 03 left the rest "to the Understanding slices", but issues 04 (Needs) and 08 (Life Threads) did not add it.

## Acceptance criteria

- [x] The Understanding entry in a trace shows the Need, intensity, cause known, and the counts above, for a plain User and for an Admin
- [x] No titles, stories, nuance or mood words appear in a plain User's entry
- [x] Admin Model Call Log page shows them; Vitest + RTL tests
- [x] Tests at the webhook and Admin API seams; checks pass
- [x] `/run-dashboard`: open a trace and see the decision shape

## Blocked by

- `.scratch/understanding/issues/08-life-threads-and-being-reminded.md` (completed)

## Comments

- Decision: the shape is saved on the trace's Understanding call (`model_calls.understanding_shape`, migration 0036) after the form is read, by `ModelCallLog.record_understanding_shape`. A failed or unreadable Understanding still gets a shape: the fallback the reply followed (fallback Need, low, cause known), next to the call's error.
- "Need picked" is the Need the reply followed, after falling back from an unknown name.
- "Left alone" counts the Threads the reply was told to leave alone; a held-back Thread counts there only when the model named it. "Held back" counts every held-back reminded Thread.

## Completion

- Completed: 2026-11-14
- Evidence:
  - Shape for a plain User and an Admin: `tests/test_model_call_log.py` `test_a_plain_users_understanding_shows_its_shape_and_never_its_words`, `test_an_admins_own_understanding_shows_its_shape_with_its_content`, `test_a_held_back_thread_shows_as_held_back_and_left_alone_when_chosen`, `test_a_failed_understanding_shows_the_fallback_need_it_used` (webhook + Admin API, real Postgres).
  - No words for a plain User: the plain-User test checks the mood, nuance, Thread title and story never reach the API response or any stored `model_calls` column.
  - Admin page: `ModelCallCard` shows the shape; `ModelCallTraceView.test.tsx` "shows the shape of the Understanding's decision" and `model-calls.test.ts` (Vitest + RTL).
  - Checks: `make check` — ruff, ruff format, mypy clean; pytest 908 passed; ESLint, Prettier, tsc clean; Vitest 374 passed.
  - `/run-dashboard`: in the worktree stack, the real app (real model, recording chat channel, run in the backend container) answered a plain User with a seeded "Falling-out with Mei" Thread and the Admin. The trace pages showed: plain User — Be heard, High, cause known Yes, 1 reminded, 0 brought up, 1 left alone, 0 held back, 1 past look-up, "No content kept"; Admin — Think it through, Low, cause known No, all counts 0, with Content. The plain User's 3 stored calls held none of their words. Checked again after the review fixes. Run Users and Clerk test users removed.
  - `/code-review`: no breaks of the written standards. Fixed: an explicit field-by-field read of the stored shape, no default on `ModelCall.understanding_shape`, docstrings on what "left alone" and a fallback shape mean, and a test for a held-back Thread the model never named.
- Commits: to be filled in after merge
