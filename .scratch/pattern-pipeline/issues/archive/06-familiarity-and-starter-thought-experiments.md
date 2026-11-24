# 06 — Familiarity: Zeph knows how well it knows a User, and starts new Users with starter Thought Experiments

Status: completed
Track: A
Blocked by: 05

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 16, 17, 18, 19, 80). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Familiarity is how well the Companion knows a User: new, getting to know, or knows well. Code works it out at each Conversation end from counts (Conversations, Life Threads, Observations from real stories, Pattern states) against Admin-set bars. The Reply Plan is told it in one line on every reply, and Admins see it for each User.

A new User is offered starter Thought Experiments in their first Conversations (start: 4 over the first 14 days, at most 1 per Conversation), under the usual Need rules. Their answers are weak evidence. Once the User is getting to know, the Agenda takes over and starter ones stop. Onboarding is unchanged.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [x] Familiarity is worked out by a pure function from counts and Admin-set bars, and recomputed at each Conversation end
- [x] The Reply Plan is given the User's Familiarity in one line, and the prompt says what each level means for how Zeph asks
- [x] A new User with Pattern exploring on is offered starter Thought Experiments within the Admin-set number, days and per-Conversation cap
- [x] Starter Thought Experiments stop once the User is getting to know
- [x] A starter answer alone never makes a Pattern suspected or ready
- [x] Admins see each User's Familiarity on the Users page
- [x] Onboarding has no new step
- [x] Each bar and limit is a Platform Setting with a hint
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `05-thought-experiments.md`

## Comments

### 25 Nov 2026: built

What was built:

- **Familiarity** (`core/familiarity.py`, `users.familiarity`, migration 0095): new, getting to know, knows well. One pure function, `familiarity_of`, from four counts (Conversations, Life Threads, Observations from real stories, Patterns in each state) against Admin-set bars. `FamiliarityKeeper` works it out at every Conversation end, after scoring and Pattern keeping, also while User Memory is off.
- **Reply Plan**: one line on every reply ("How well you know them (Familiarity): new"). `reply_plan_prompt` says what each level means for how Zeph asks; migration 0095 reloads it from the seed.
- **Starter Thought Experiments** (`core/starter_thought_experiments.py`): after the Agenda, while Pattern exploring and Curiosities work, code (`plan_starters`, pure) writes a new User's next starter as a waiting Curiosity (new aim `starter`, `curiosities.thought_experiment_id`). Asked like any Curiosity under the usual Need rules.
- **Six Platform Settings** with hints, in the Patterns section, overridable in Eval Variants: `familiarity_conversations` 5, `familiarity_life_threads` 3, `familiarity_real_stories` 0, `starter_thought_experiments` 4, `starter_thought_experiment_days` 14, `starter_thought_experiments_per_conversation` 1.
- **Users page**: a "Familiarity" row, first under "What Zeph holds" on the User's panel.

Decisions made while building (owner may want to look):

- **"What if" answers alone never make a situation.** A starter answer is a "what if" answer (40% of its sign's points). Two strong ones about two people gave 112 points and 2 situations, enough for suspected. So scoring now counts a situation only when something other than a "what if" answer counts for the Pattern there. This holds for every Thought Experiment answer, not only starters. Issue 07's ready gate uses the same situations count, so it is covered too.
- **A third bar, real stories, starting at 0.** The issue lists "Observations from real stories" among the counts but decision 29 gives no number. It is a setting that starts at 0 (none needed), so the start matches decision 29: 5 Conversations and 3 Life Threads, or a first suspected Pattern.
- **Getting to know also with a ready or contested Pattern; knows well with shared or confirmed**, with or without a Pattern Type (so a Pattern confirmed before the catalog counts).
- **Familiarity follows the counts**, so it can go back (a deleted Thread, a Pattern back to noticed). Delete My Data makes a User new again.
- **The per-Conversation cap** is kept by writing starters only at Conversation end and never more waiting than the cap. So the first starter comes in the second Conversation.
- **Days count from sign-up.** A waiting starter is not offered after the days pass, and is closed at the next Conversation end.
- **Starters stop when the User asks Zeph to drop one.** Not asked for; added as the kind default.
- **The Agenda never puts a Thought Experiment that was already a starter for that User**, and the other way round.
- **The keeping model can no longer write the code-only aims** (`exploration`, `starter`).
- **Design files.** As issues 05, 10, 13 and 14 did: one row added to `reference/AdminUsers.html` (existing row style), baseline rebuilt with `shoot.cjs` (no other baseline changed).

Limits:

- A User signed up before this reads "new" until their next Conversation ends.
- A User who drops back to new inside the days is offered starters again, up to the same number.
- The answer is weak evidence only when the tagging model marks it as answering the Thought Experiment it was shown.
- Starters are picked oldest first, not by area.
- Migration 0095 reloads `reply_plan_prompt` from the seed, so an Admin's edit to it is lost (as migration 0088 did).

Evidence (25 Nov 2026, worktree stack on 3010/8010, migration 0095 applied by the running backend; chat through the real webhook with the real model (`InProcessCompanion` in the backend container on the worktree database, recording chat channel), Conversation ends run by the running backend's scheduler, times moved back with SQL instead of waiting; signed-in Admin in a real browser (Playwright); made-up User only):

- **Pure function, recomputed at each Conversation end.** Running app: new after Conversations 1 to 3; after "Conversations to be getting to know" was set to 4 and "Life Threads" to 0 on the Dashboard, the fourth Conversation end made the User `getting_to_know`; with the bar raised to 50 the next end made them `new` again; with User Memory off and the bar back at 4, the next end made them `getting_to_know`. Tests: `test_familiarity_follows_the_counts_and_the_bars` (11 cases), `test_the_real_stories_bar_counts_once_an_admin_sets_it`, `test_the_admin_set_bars_decide_when_a_user_is_no_longer_new`, `test_familiarity_is_worked_out_even_while_user_memory_is_off`.
- **Reply Plan told in one line; prompt says what each level means.** Running app: the logged Reply Plan input held "How well you know them (Familiarity): new", later "getting to know"; its instructions held the three-level paragraph from the reloaded prompt. While new, Zeph also asked a made-up question of its own. Tests: `test_a_new_user_is_put_one_starter_a_conversation_and_answers_are_weak_evidence`, `test_starters_stop_and_the_agenda_takes_over_once_zeph_is_getting_to_know_them`.
- **Starters within the number, days and cap.** Running app: the first Conversation end wrote `belong-worth-team-plan` as a waiting `starter` Curiosity, low sensitivity. In the second Conversation Zeph put it: "Alright, a made-up one for you. Your team lead, someone you get on well with, shares a plan in a meeting and you can see a real problem with it. Nobody else has spoken up. What do you do…". The next one (`give-belong-no-one-minds`) was written only when that Conversation ended, and was put in the third. With the number set to 3: two asked and one waiting, and the next end wrote none. With the days set to 0: the Reply Plan was not offered the waiting starter, and the next end closed it. Tests: the six `plan_starters` rule tests in `test_familiarity_rules.py`, `test_starters_stay_within_the_admin_set_number_and_days`, `test_no_starter_is_written_without_pattern_exploring`, `test_switching_a_starter_off_closes_its_waiting_curiosity_at_once`.
- **Stop once getting to know.** Running app: at the Conversation end that made the User `getting_to_know`, the waiting starter was closed; the next reply's input held no starter. Tests: `test_starters_stop_once_zeph_is_getting_to_know_them` (2 cases), `test_starters_stop_and_the_agenda_takes_over_once_zeph_is_getting_to_know_them`.
- **A starter answer alone never makes a Pattern suspected.** Running app: the real tagger kept "I like being the person people can count on, it feels good to be needed." as APPR.GIVE.NEEDED, `what_if_answer`; the Pattern was noticed. With two more strong "what if" answers about two other people added with SQL (124 points, over the 100 bar, three made-up situations), the next real Conversation end left it noticed, with no Exploration. (The first starter's answer was not tagged by the model at all.) Tests: `test_what_if_answers_alone_never_make_a_situation`, the chat-path test above (two answers, 112 points, still noticed).
- **Admins see Familiarity on the Users page.** Browser at 1280 and 390, real data: the made-up User's panel showed "Familiarity: Getting to know", the Admin's "Familiarity: New"; no sideways scroll at 390. Fixture mode: Alex's panel, opened, matches the reference row for row ("Familiarity: Knows well" first). Pixel test (git-ignored copy of `compare.cjs` blocking Clerk's protect probes): `FAIL AdminUsers 3.74% differs, height 800 vs 978`. This page failed before this branch (issue 12 recorded 2.80%, 800 vs 933, the same with main's code): in fixture mode the app doesn't open the panel, show "Sample data" or "128 users · 2 admins" as the reference draws. Not fixed here. Tests: `AdminUsers.test.tsx`, `test_admin_sees_every_user_with_counts_but_no_message_text`.
- **Onboarding has no new step.** Running app: the made-up User signed up, connected Telegram and chatted with no added step; the starter came through chat. The diff touches no onboarding file.
- **Each bar and limit a Platform Setting with a hint.** Browser, Platform settings, 1280 and 390: all six fields shown with their hints; two changed, saved and kept after reload. Tests: `test_every_bar_and_limit_is_a_setting_with_a_hint_and_an_eval_override`, `test_every_editable_setting_comes_with_a_short_hint`.
- **Checks.** On the final code: ruff clean, ruff format clean, mypy clean (254 files), pytest 2182 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 138 files, 960 tests passed. Migration: `test_the_migration_keeps_user_data_and_reloads_the_reply_plan_prompt` (down to 0094 and back, no User data lost).
- **Review.** Standards and spec reviews run; fixed: Familiarity now worked out while User Memory is off, two unclear names, a hint. Left as is and listed above: the wider "what if" rule, the third bar, starters stopping on "drop it".

## Completion

- Completed: 2026-11-25
- Commit: <filled in after the merge>
