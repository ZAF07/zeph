# 17 — Tune the Understanding with the Understanding Eval

Status: needs-triage

## What

The first Understanding Eval run (issue 14, 2026-11-14) failed 4 of 13 Messages, all from the model's choices (its inputs were right):

- "should I take the job offer… what would you do?" → picked Think it through, expected Advice.
- "skipped my runs again this week. third week in a row" (Goal: run three times a week) → picked Be heard, expected Accountability.
- "my sister's wedding is next week", with the open 9-month-old Falling-out with Mei Thread shown → picked Just chatting and didn't bring the Thread up.
- "I'm in the BEST mood today, buzzing" → didn't set high intensity / unknown cause, so the reply wasn't told to ask why (the reply still probed gently on its own).

The PRD says being reminded is the heart of the feature and to tune the closeness bars and prompt with the Eval first. Admins can change the Understanding prompt and the Needs without a redeploy. A change to the seeded wording needs a migration to reach existing installs.

## Acceptance criteria

- [ ] `uv run pytest -n 0 evals -m eval -k understanding` passes (apart from failures caused by bug 16), or each remaining failure is explained
- [ ] The other Evals don't get worse
- [ ] `make check-python` passes

## Blocked by

- `.scratch/understanding/issues/14-understanding-eval.md`
