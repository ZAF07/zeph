# 17 — Tune the Understanding with the Understanding Eval

Status: completed

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

- [x] Every Understanding eval case passes in 3 runs in a row (`uv run pytest -n 0 evals -m eval -k understanding`), or each remaining failure is written up with its pass rate: final 3 runs 12/12, 12/12, 12/12. `reminded-of-sister`'s reply rule then failed in the full eval and 1 of 3 reruns (8 of 10 since the last rewording, the Understanding's own checks passed every run): written up below and in issue 25
- [x] The other Evals don't get worse than the baseline run (a new failure is rerun 3 times to tell a regression from a fluke): final `make eval` 68/70; `reminded-of-sister` (above) and Persona `asks-for-tips` `no_lists` (2 of 4, a reply-side flake already seen failing 2 of 3 in issue 18, not caused by the Understanding) were rerun 3 times; baseline's `delete-account` failure passed
- [x] `make check-python` passes: ruff, ruff format, mypy clean; 957 passed
- [x] The local main database has the new Understanding prompt and Needs: one-off reset run on 2026-11-15 (see Comments); also brought it from migration 0038 to 0040, so it now has issue 18's prompt fields and the "Get it done" Need

## Blocked by

- `.scratch/understanding/issues/14-understanding-eval.md`
- `.scratch/understanding/issues/archive/21-reasoning-calls-default-to-reasoner.md` (completed 2026-11-15) (tune on the reasoner, not on chat)

## Comments

- 2026-11-15 (implemented; evidence). All runs on the deepseek-reasoner defaults, stack down so evals used the seed files:
  - **Baseline** (before any change): `make eval` 69/70 (only `delete-account`, issue 18/24's case). Understanding 3 runs: 12/12, 12/12, 11/12. On the reasoner 3 of the 4 cases in "What" already passed 3/3 (Advice, Accountability, Mei raised); only `strong-mood-unknown-cause` failed (1 of 3, `asked_why`).
  - **All four fixes** (seed files only: `needs.yaml` Advice, Think it through, Accountability, Be heard; `platform_settings.yaml` intensity, cause_known, bring_up), 3 Understanding runs: 12/12, 10/12, 10/12. Every Understanding check passed; the Judge failed `reminded-of-sister` `raises_sister_naturally` twice (the Understanding picked `weave` for Mei, because "weave after a light message" fit "my sister's wedding is next week", and the reply skipped Mei) and `no-knowledge-for-a-vent` `no_teaching` twice (a silver lining in the reply).
  - **Tuned bring_up alone:** "lead when the message is about the Thread or someone in it, weave when it is only a side link". Both cases rerun 3 times: 2/2 each time (the vent failures were noise).
  - **Final:** Understanding 12/12, 12/12, 12/12 (3 in a row). `make eval` 68/70: `reminded-of-sister` (Understanding picked `lead`, reply asked "how are you feeling about it?" without Mei) and Persona `asks-for-tips` `no_lists`. Each rerun 3 times: `reminded-of-sister` 2/3, `asks-for-tips` 2/3. Both are the reply, not the Understanding; filed as `25-reply-skips-thread-it-was-told-to-lead.md`. `strong-mood-unknown-cause` passed every run after the fix (8/8).
  - **Running app:** the Understanding eval drives the real backend through the Telegram webhook with real DeepSeek and fastembed, so these runs are the app check for a seed-wording change; no separate /run.
  - **Local main DB reset** (shown, then run): started only the main Postgres container, ran the project's `migrate()` (it was at 0038, so issue 18's 0039 and 0040 hadn't run), deleted `understanding_prompt` and re-ran `seed_platform_settings` from the new seed, set each Need's `when_it_fits` from `needs.yaml` by name (7 of 7 updated), checked the prompt has both the issue 18 fields and the new bring_up wording, stopped the container.
  - **Review:** Spec found nothing blocking (lead/weave rewording within the decision). Standards found no hard issues; kept as tested: one short line in bring_up, the "and" clauses in Be heard / Think it through, and "Good moods count too" placement in cause_known. Rewording now would ship text the evals didn't test.

- 2026-11-14 (issue 16 done): the Knowledge eval's reply sometimes skips a passage it was given. That is the reply prompt, not the Understanding: filed as `20-reply-skips-knowledge-passage-it-was-given.md`.

## Completion

- Completed: 2026-11-15
- Commits: `6a9378b` (Understanding prompt and Needs wording), `3284e0d` (follow-up issue 25)
