# 12 — Patterns are scored from Observations and moved between states by code, with a log

Status: completed
Track: B
Blocked by: 11

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 21, 22, 23, 24, 25, 32, 80, 83). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

After tagging, code scores each of the User's catalog Patterns from its Observations and moves it between states. Score: each Observation's weight is its sign's strength times its kind of evidence, reduced when unclear, zero when situational, negative when against, fading by a half-life at read time. A situation is one Life Thread (with no Thread, the same person and setting); within a Thread only the strongest Observation per person counts, up to a cap of people. The score is always computed from Observations, never stored as the source of truth.

This issue covers the states noticed, suspected and closed (ready, shared, confirmed and contested come with issues 07 to 09, and the state type has all seven from the start). Every move is saved in an append-only log with its cause. Starting numbers are in `.scratch/pattern-pipeline/grill-decisions.md` (decision 29). Still silent: nothing reaches a reply.

## Acceptance criteria

- [x] A first Observation for a Pattern Type creates a noticed Pattern for the User
- [x] A Pattern moves to suspected at the Admin-set situations and score, and to closed under the Admin-set floor
- [x] Ten Observations about one person in one Life Thread count as one
- [x] Observations about different people in one Life Thread add weight up to the Admin-set cap, and still count as one situation
- [x] An unclear Observation counts at the reduced weight toward each Pattern Type; a situational one counts nothing; one against lowers the score
- [x] Older Observations count for less by the Admin-set half-life
- [x] Deleting an Observation changes its Pattern's score and state at once
- [x] Every state move is logged with its cause and is never edited or removed except by Delete My Data and Account Deletion
- [x] Scoring, counting situations and the state moves are pure functions with their own tests
- [x] Admins see how many Patterns a User has in each state, never their content
- [x] Every number is a Platform Setting with a hint and can be overridden in an Eval Variant
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `11-tagging-step-keeps-observations.md`

## Comments

Plan (24 Nov 2026, branch `pattern-12-scoring`, worktree `ai-chat-companion-pattern-12`):

- **One store.** Catalog Patterns live in the existing `patterns` table (ADR-0024 rejects two stores), with a new `pattern_type_id` (one per User and Pattern Type) and `pattern` text made optional. Every old-style reader (Pattern keeping, coming to mind, the Patterns tab, the Portrait, delete-without-evidence) keeps reading only rows with no Pattern Type, so nothing reaches a reply. Issue 16 joins them up.
- **Pattern state** gets all seven values. This issue moves only noticed, suspected and closed; a Pattern in ready, shared, confirmed or contested is left alone.
- **Pure rules** in a new `core/pattern_scoring.py`: an Observation's weight; grouping into situations (a Life Thread; with none, the same person and setting); within one, per direction, only the strongest Observation per person counts, up to the cap of people; the score is the sum; situations counted are those where it showed (weight for it above 0); the state each Pattern should be in: under the floor → closed, at the suspected situations and score → suspected, else noticed. States follow the evidence, so moves go back too (a deletion can take suspected back to noticed, and a closed one whose score comes back over the floor is noticed again).
- **Linking.** No link column: a User's Pattern for a Pattern Type is fed by their Observations naming it, first or second (unclear counts toward both). Any Observation, even against or situational, makes a noticed Pattern. One left with no Observations is deleted; its log stays.
- **Scoring step** at Conversation end, right after tagging, while Pattern noticing works: rescores all the User's catalog Patterns (fading can move them too). Deleting a Life Thread rescores at once.
- **Log** `pattern_moves`, append-only: User, Pattern, Pattern Type, from, to, cause (Conversation tagged, with its ID, or Observations deleted), score and situations at the move, when. No content. Only Delete My Data and Account Deletion remove it.
- **Settings**, whole numbers so the Platform settings page needs no new kind: sign weights in points (weak 30, moderate 70, strong 140; 100 points = decision 29's 1.0), kind of evidence and unclear as percents (100/70/40/30, 25), half-life 75 days, people per Thread 3, suspected 2 situations and 100 points, closed under −150 points. New "Patterns" section on Platform settings; each overridable in an Eval Variant like any editable setting.
- **Admins** see counts per state: the Users API gives counts by state, and the user panel adds a row per state with a count above 0 in the existing "What Zeph holds" style (agreed with the owner, flagged for the designer).

Decisions made while building (24 Nov 2026):

- **Admin counts** replace `confirmed_pattern_count` with `pattern_counts` (every state, with or without a Pattern Type) in the Users API. The panel keeps "Confirmed Patterns" and adds a row per other state with a count above 0, in the "What Zeph holds" row style (owner chose this; `reference/AdminUsers.html` doesn't draw them yet, flagged for the designer).
- **Unclear Observations** count toward the second Pattern Type with the sign strength of the first (one Observation, one sign).
- **Per-person cap** applies to for and against apart: up to 3 people's strongest for, and up to 3 people's strongest against.
- **Kept states.** Scoring never moves or deletes a Pattern in ready, shared, confirmed or contested (found in review); only noticed, suspected and closed ones left with no Observations are deleted.
- **Rescoring after a Thread deletion** logs a failure instead of raising, so the deletion still answers and the Portrait is still rewritten (found in review).
- **Number fields** on Platform settings accept a leading minus (for the floor); the backend still checks every range.
- **Migration** is 0083.

Evidence (24 Nov 2026, worktree stack on 3010/8010, made-up User only; build `6886441` plus docs):

- **First Observation → noticed.** Made-up User with Pattern noticing on for them only; one Conversation (Mei asking for help moving, manager Daniel's extra report) seeded and ended by the quiet gap. The scheduler ran the real chain with the real DeepSeek model: Threads "Helping sister Mei move" and "Extra report from manager Daniel", two CONF.AVOID.BELONG Observations (Daniel's situational: power above), a noticed Pattern at 140 points in 1 situation, and the log row `— → noticed, conversation_tagged`, with the Conversation's ID. The old Pattern keeping step wrote its own suspected Pattern beside it, unchanged. Tests: `test_a_first_observation_notices_a_pattern_and_logs_why`, `test_a_first_observation_starts_a_noticed_pattern_and_logs_it`.
- **Suspected / closed at the Admin-set bars.** Real `PatternScorer` run in the backend container on the real database after seeded Observations: a clear one in the work Thread made 490 points in 2 situations → suspected. Admin lowered "Score that closes a Pattern" to −100 on the Platform settings page; a score of −140 then moved noticed → closed; set back to −150 through the UI it moved closed → noticed. Tests: `test_two_situations_with_enough_score_make_it_suspected`, `test_the_admin_set_bars_decide_when_it_is_suspected_and_closed`, `test_a_pattern_moves_by_its_score_and_situations` (13 cases).
- **Ten about one person count as one.** Ten more Observations about Mei in her Thread (11 in all): still 140 points, 1 situation. Test: `test_ten_observations_about_one_person_in_one_thread_count_as_one`.
- **Different people add weight up to the cap, one situation.** Adding mum: 280, 1 situation; adding dad and aunt (5 people, cap 3): 420, still 1 situation. Tests: `test_different_people_in_one_thread_add_weight_up_to_the_cap_in_one_situation`, `test_the_cap_keeps_the_strongest_people`.
- **Unclear, situational, against.** A strong unclear one (with ACH.WORTH.PERF) added 35 points to each and noticed ACH.WORTH.PERF; a situational one added nothing; a strong one against took off 140. Tests: `test_an_observation_is_worth_its_sign_times_its_kind_of_evidence` (9 cases), `test_an_unclear_observation_counts_toward_each_of_its_pattern_types`, `test_one_against_lowers_the_score_even_about_the_same_person`.
- **Half-life.** The Mei Thread's Observations moved back 75 days: its 420 became 210 (total 105); back 150 days: total 0, and fading alone moved it suspected → noticed. Test: `test_older_observations_count_for_less_by_the_half_life`.
- **Deleting changes score and state at once.** As the User, deleting "Extra report from manager Daniel" on the Memories page's "What's going on" tab moved the Pattern suspected → noticed (420 points, 1 situation), logged `observations_deleted`, at once. Tests: `test_deleting_its_observations_moves_it_back_at_once_and_the_log_stays`, `test_deleted_evidence_moves_a_pattern_back_with_its_cause`, `test_a_pattern_with_no_observations_left_is_deleted_without_a_move`.
- **Log, append-only.** 8 moves logged through the run, each with its cause, never edited (no code updates or deletes a move except below). "Delete my data" on Account & privacy removed every Pattern, all 8 moves and every Observation, account kept; after seeding one again, "Delete my account" removed the User, their Pattern, its move and the Observation. Tests: `test_delete_my_data_and_account_deletion_remove_patterns_and_their_log` (both routes); the log staying after its Pattern is deleted in the deletion test above.
- **Pure functions.** `observation_points`, `situation_of`, `score_situation`, `score_observations`, `state_for`, `observations_by_pattern_type` and `plan_pattern_moves` in `core/pattern_scoring.py`, tested with plain values in `tests/test_pattern_scoring.py` (41 tests, no database or model).
- **Admins see counts, never content.** Users page, this User's panel at 1280 and 390: "Confirmed Patterns 0, Noticed Patterns 1, Suspected Patterns 1, Closed Patterns 1", in the same rows as the others; no Pattern words. Tests: `test_admins_see_how_many_patterns_a_user_has_in_each_state_never_content`, `AdminUsers.test.tsx`, `users.test.ts`.
- **Settings with hints, Eval Variant overrides.** Platform settings has a Patterns section with the 13 numbers, each with its hint and seeded value. New Eval run page: the Variant override picker lists all 13; picking "Situations to be suspected" shows its hint and "Live: 2" (no run started: runs cost money). Tests: `test_every_scoring_number_is_a_setting_with_a_hint_and_an_eval_override`, `PlatformSettingsForm.test.tsx` (negative floor saved).
- **Silent.** In the container on the real database, the old-style readers (Recall, Pattern keeping) returned only the old suspected Pattern; confirmed (Patterns tab, Portrait) none; the User's Patterns tab showed "No patterns yet". Test: `test_patterns_of_pattern_types_reach_no_reply_and_no_old_pattern_step`. Migration: `test_the_migration_keeps_every_old_pattern_with_its_evidence`.
- **Checks.** `make check` on the final code: ruff clean, ruff format clean, mypy clean (236 files), pytest 1891 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 136 files, 932 tests passed. Pixel test (git-ignored copy of `compare.cjs` blocking Clerk's protect probes): `FAIL AdminUsers 2.80% differs, height 800 vs 933`, and the same numbers with main's `web/src`, so not from this branch.
- **Review.** Standards and spec reviews run. Fixed: Patterns past suspected are never deleted by scoring, rescoring after a deletion can't break it, clearer planner branches, `HAS_PATTERN_TYPE`. Left: some parameters travel together in `pattern_scoring.py` (a small "why and when" type could gather them); `save_moves` takes the plan's four parts one by one; `list_moves` has no app caller yet (it is the log's reader for tests and later pages).
