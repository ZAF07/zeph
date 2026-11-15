# 17 — Tune the Understanding with the Understanding Eval

Status: ready-for-agent

## What

The first Understanding Eval run (issue 14, 2026-11-14) failed 4 of 13 Messages, all from the model's choices (its inputs were right):

- "should I take the job offer… what would you do?" → picked Think it through, expected Advice.
- "skipped my runs again this week. third week in a row" (Goal: run three times a week) → picked Be heard, expected Accountability.
- "my sister's wedding is next week", with the open 9-month-old Falling-out with Mei Thread shown → picked Just chatting and didn't bring the Thread up.
- "I'm in the BEST mood today, buzzing" → didn't set high intensity / unknown cause, so the reply wasn't told to ask why (the reply still probed gently on its own).

The PRD says being reminded is the heart of the feature and to tune the closeness bars and prompt with the Eval first. Admins can change the Understanding prompt and the Needs without a redeploy. A change to the seeded wording needs a migration to reach existing installs.

## Decisions (grilling, 2026-11-15)

- **Pass bar:** a case passes only if it passes in 3 Understanding eval runs in a row. A case that still fails after tuning is written up with its pass rate.
- **Only wording changes:** the Understanding prompt and the Needs' "when it fits". No code changes, and the eval's expectations stay as they are. If a case won't pass after about 3 tries, stop and ask.
- **Seed files only, no migration.** The platform isn't live; in production Admins own this wording (Dashboard, later the Eval dashboard), so a migration that overwrites it would be the wrong habit. At the end, reset the local main database's `understanding_prompt` and Needs to the new seed wording with a one-off command, shown to the User before it runs.
- **Run evals with the stack down**, so they use the seed files (the eval copies platform settings from the app's database when it is running; Needs always come from the seed).
- **Baseline first:** before changing anything, run `make eval` once and the Understanding eval 3 times. Issue 18's failures don't count against this issue.
- **Wording to try:**
  - *Advice* (`when_it_fits`): they ask what to do, what you would do, or for your view, ideas or a plan, even while they are still weighing it up. *Think it through*: add "and haven't asked for your view".
  - *Accountability*: they mention one of their Goals, even in passing and without naming it: progress, a slip, an excuse or a plan; a slip they sound fed up about is still Accountability. *Be heard*: add "and it isn't mainly about one of their Goals" (a slip mentioned beside real pain, e.g. mum in hospital, is still Be heard).
  - *bring_up* in the prompt: flip the default. When an open Thread connects to the message and they aren't struggling or caught up in something else, bring it up; a long gap is a reason to ask how things are now. "weave" for a light message, "lead" when the Thread is what they're talking about. Keep the "don't bring it up" and left-alone rules. The Need isn't checked for this Message.
  - *intensity*: "high" when the feeling is strong in their own words (capitals, "the best", "can't sit still", "I'm a wreck") or stands out from how they usually seem. *cause_known*: false when they share a strong feeling without saying what brought it on and nothing known explains it; don't guess a cause. Good moods count too.
- **Order:** baseline → all four fixes at once → 3 Understanding runs → tune any failing case alone (rerun just it 3 times) → 3 more Understanding runs, `make eval` once, `make check-python` → reset local main database.

## Acceptance criteria

- [ ] Every Understanding eval case passes in 3 runs in a row (`uv run pytest -n 0 evals -m eval -k understanding`), or each remaining failure is written up with its pass rate
- [ ] The other Evals don't get worse than the baseline run (a new failure is rerun 3 times to tell a regression from a fluke)
- [ ] `make check-python` passes
- [ ] The local main database has the new Understanding prompt and Needs

## Blocked by

- `.scratch/understanding/issues/14-understanding-eval.md`
- `.scratch/understanding/issues/archive/21-reasoning-calls-default-to-reasoner.md` (completed 2026-11-15) (tune on the reasoner, not on chat)

## Comments

- 2026-11-14 (issue 16 done): the Knowledge eval's reply sometimes skips a passage it was given. That is the reply prompt, not the Understanding: filed as `20-reply-skips-knowledge-passage-it-was-given.md`.
