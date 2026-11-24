# 04 — Explorations and the Agenda: Zeph knows what it is trying to learn and comes back to it

Status: completed
Track: A
Blocked by: 01, 12

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 2, 3, 4, 5, 7, 29). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Zeph needs to remember what it is exploring. An Exploration is its ongoing effort on one suspected Pattern: what it still needs to learn (an unclear story to settle, a part of the User's life it hasn't seen, a counter-test), each try (which Curiosity, when, whether what came back was useful, vague or brushed off), and what to try next and not before when. The Agenda is the User's active Explorations, at most an Admin-set number (start 3), ranked by code.

After scoring at Conversation end, code keeps the Agenda and writes the next aimed Curiosity for each Exploration, least pushy way first: a follow-up on a story, "would it have gone differently with…", then (issue 05) a Thought Experiment, then "this week, notice when…". A try that gets nothing useful leaves the need open. An Exploration is never worked on two Conversations in a row, waits after a try with nothing (start 3 days), rests after tries with nothing (start 4) and wakes on new evidence. The Reply Plan sees the Agenda with each Exploration's earlier tries on every reply, and Get curious is aimed by its open needs. All behind a new Feature, Pattern exploring, which works only when Pattern noticing does.

## Acceptance criteria

- [x] A suspected Pattern gets an Exploration with its open needs worked out by code from its Observations (unclear, missing part of life, counter-test)
- [x] At most the Admin-set number of Explorations are active for a User, ranked by code
- [x] Code writes an aimed Curiosity for an Exploration's top need; the model only words it
- [x] Each try is saved with its Curiosity, when it was asked and how it went
- [x] A try that came back vague or brushed off leaves the need open, and the next try uses a different way after the Admin-set wait
- [x] The same Exploration is not worked on in two Conversations in a row
- [x] An Exploration rests after the Admin-set number of tries with nothing, frees its place, and wakes when a new Observation arrives for its Pattern
- [x] The Reply Plan is given the Agenda with earlier tries, and Get curious is given the open needs
- [x] An answer to an aimed Curiosity that settles an unclear Observation is tagged as clear at Conversation end
- [x] With Pattern exploring off for a User, no Explorations or aimed Curiosities are made and none are deleted
- [x] Delete My Data and Account Deletion remove Explorations
- [x] Agenda ranking and the Exploration rules are pure functions with their own tests; every number is a Platform Setting with a hint
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `01-needs-say-how-curiosities-are-treated.md`
- `12-patterns-scored-and-moved-by-code.md`

## Comments

Plan (24 Nov 2026, branch `pattern-04-explorations`, worktree `ai-chat-companion-pattern-04`):

- **Feature Pattern exploring**, off to start; works only while Pattern noticing works (a general "needs Feature" rule beside the Stickers one, with its own reason).
- **Store.** `explorations` (one per User and Pattern, goes with its Pattern): state active (on the Agenda), waiting (for a place, or its Pattern isn't suspected) or resting; when it rested and woke. `exploration_tries`: one per aimed Curiosity (its question and when it was asked come from the Curiosity), with the need, the way, the Observation or part of life aimed at, and the outcome (useful, vague, brushed off). Curiosities get the aim `exploration`, plus `exploration_id` and `source_observation_id`, so deleting the Exploration or the Observation deletes its waiting Curiosity (like Threads and Memory Items today).
- **Open needs, worked out by code from the Pattern's Observations** (pure): unclear (each unclear Observation, newest first), missing part of life (home, work or with friends: one with no Observation while another has one), counter-test (no Observation against yet and no useful counter-test try). Top need is the first in that order.
- **Ways, least pushy first:** story follow-up → "would it have gone differently with…" → "this week, notice when…" (Thought Experiments slot in with issue 05). Each try with nothing moves that need to the next way, round again after the last.
- **Outcome, decided by code from the reaction:** brushed off or asked to drop → brushed off; engaged and a new Observation of its Pattern Type came from that Conversation (or its unclear Observation is now clear) → useful; otherwise vague.
- **Agenda step** at Conversation end, after Curiosities, while Pattern exploring works (User locked, like scoring): save the outcome of every aimed Curiosity asked in the Conversation; give each suspected Pattern an Exploration; wake resting ones with a new Observation since they rested; rest one after `exploration_rest_after_tries` (4) tries with nothing in a row, or at once when asked to drop; rank the rest by score (highest first, then oldest) and put the top `agenda_size` (3) on the Agenda; close the waiting aimed Curiosity of any that leave it. For each active one with no waiting aimed Curiosity, not tried in this Conversation (so never two in a row), code writes one for its top need with the next way, not before the last try's day + `exploration_wait_days` (3) after a try with nothing.
- **Wording.** Code writes the Curiosity's question as a plain instruction from the Observation's day and context line, the Pattern Type's "if" and a part of life ("Go back to what they told you on 3 Nov (…): ask what they did next and what they hoped wouldn't happen"); the Reply words it as today. No Pattern name reaches the Reply.
- **Reply Plan** gets the Agenda each reply while Pattern exploring works: each Exploration (Pattern Type name, marked never to say), its open needs and earlier tries (day, way, question, outcome), and a line saying Get curious aims at an open need. Aimed Curiosities come first among the due ones, and are offered only while Pattern exploring works. The Curiosity keeping model never sees or closes waiting aimed ones.
- **Settling unclear.** The tagging step is shown the aimed Curiosities asked in the Conversation that aim at an unclear Observation, and may answer `settled` with the Observation's number, the Pattern Type and a sign; code accepts only one of its two Pattern Types and a sign of that type in the same direction, and makes the Observation clear. Prompts for tagging and the Reply Plan are reloaded from the seed (migration).
- **Off:** nothing made, nothing deleted, no Agenda in the Reply Plan, aimed Curiosities not offered.
- **Deletion:** Delete My Data and Account Deletion remove Explorations and tries.
- **Settings** in the Patterns section with hints: `agenda_size` 3, `exploration_wait_days` 3, `exploration_rest_after_tries` 4; overridable in Eval Variants.
- **Tests:** pure tests for needs, ways, outcomes, ranking and the Agenda plan; HTTP-edge tests for the Conversation-end chain, the Reply Plan input, Feature off and deletion.

Decisions made while building (24 Nov 2026):

- **Needs the Curiosities Feature too.** No Agenda is kept while Curiosities doesn't work for the User, since an aimed Curiosity couldn't be asked (found in review).
- **Way order.** Only a try with nothing moves a need to the next way; after a useful try the same way is used again (review).
- **Settled is useful.** A try whose unclear story the tagger settled is useful unless brushed off, even when no reaction was recorded (review).
- **Asked to drop** rests the Exploration at once (story 15); new evidence still wakes it.
- **Not while struggling.** The Reply Plan gets no Agenda while the Understanding finds the User struggling, as with Curiosities.
- **Deleting a story** deletes the tries aimed at it with their Curiosities, since their wording describes that story; their count and a met counter-test can start over (review, kept on purpose).
- **Check-ins** may ask an aimed Curiosity, under the existing weekly Curiosity Check-in limit (decision 28). One that gets no reply is a vague try; the wait still applies.
- **Useful evidence** is any Observation of the Pattern Type from the Conversation it was asked in, including ones from before the question (Observations keep a day, not a time).
- **Saving the Agenda** adds and closes aimed Curiosities in the Exploration repository, so it is one step under the User lock; the port says so.
- **Migration** is 0088 (main took 0087 for OpenRouter model names while this was built).

Evidence (24 Nov 2026, worktree stack on 3010/8010, real DeepSeek model through the real webhook (`InProcessCompanion` in the backend container on the worktree database, recording chat channel), Conversation ends run by the running backend's scheduler, times moved back with SQL instead of waiting; made-up User only. Some Observations were added with SQL, quoting the User's own texts, where noted):

- **Exploration with needs from Observations.** Conversation 1 ("I said yes to my sister Mei again… it's fine honestly", "…my coworker Jun asked me to cover his shift and I just said sure") plus one unclear Observation added with SQL (CONF.AVOID.BELONG or ACH.WORTH.PERF, home). The real tagger kept 3 more; CONF.AVOID.BELONG went suspected. The Agenda step made one active Exploration; its try aimed at the unclear story (`unclear`, `story_follow_up`). Tests: `test_a_suspected_pattern_gets_an_exploration_and_an_aimed_curiosity`, `test_unclear_stories_come_first_then_a_missing_part_then_a_counter_test`, `test_a_part_of_life_is_missing_only_while_another_is_seen`, `test_the_counter_test_closes_with_evidence_against_or_a_useful_counter_test`.
- **At most the Admin-set number, ranked.** With "Explorations on the Agenda" at 1: belonging rested, and self-worth (suspected after two stories) took the place. Belonging then woke on new evidence and, scoring higher, took the place back; self-worth went off the Agenda. Tests: `test_only_the_admin_set_number_are_active_highest_score_first`, `test_explorations_rank_by_score_then_oldest`, `test_only_the_admin_set_number_of_explorations_are_active`.
- **Code writes the aimed Curiosity; the model only words it.** Saved question: "Go back to what they told you about Mei, their sister on 24 Nov 2026 (Said yes to helping Mei move, then played it down as fine.). Ask what they did next, and what they were most hoping would or wouldn't happen then." The real reply worded it as "Long day and then round two with Mei. What was she after this time?". No Pattern name and no quote in it. Test: `test_every_aimed_question_is_written_by_code_without_the_pattern` (9 cases).
- **Each try saved with its Curiosity, when asked, how it went.** `exploration_tries` rows joined to their Curiosities: raised with `raised_at`, reaction `engaged` → `useful`; reaction `brushed_off` → `brushed_off`. Tests: `test_code_decides_how_a_try_came_back` (7 cases), `test_a_try_asked_in_this_conversation_is_judged_and_none_is_written_now`.
- **Nothing useful leaves the need open; a different way after the wait.** The "with friends" need, asked as a story follow-up, was brushed off ("idk just hanging out. not really in the mood for deep stuff tonight tbh"). At the next Conversation's end the same need came back as "Ask whether it goes the same way with friends, say with a friend…" (`other_person`), not before 27 Nov 2026 (asked 24 Nov + 3 days). Tests: `test_after_a_try_with_nothing_the_next_is_a_different_way_after_the_wait`, `test_each_try_at_a_need_moves_to_a_different_way_least_pushy_first`, `test_never_two_conversations_in_a_row_and_a_try_with_nothing_waits_a_new_way`.
- **Never two Conversations in a row.** Conversations 2 and 5, where a try was asked, ended with no new aimed Curiosity; the next one was written at the end of Conversations 3 and 6. Tests as above.
- **Rests, frees its place, wakes.** With "Tries with nothing before resting" set to 1 on the Platform settings page, the next Conversation end rested the belonging Exploration (`rested_at` set) and closed its waiting aimed Curiosity; self-worth then took the single place. A later Conversation ("my friend Lena wanted to pick the restaurant again… I just said whatever works for you") gave a new belonging Observation, which woke it (`woke_at` set) with a new aimed Curiosity about the Lena story. Tests: `test_it_rests_after_the_tries_with_nothing_and_frees_its_place`, `test_a_resting_exploration_wakes_only_on_a_new_observation`, `test_asked_to_drop_rests_it_at_once`, `test_it_rests_after_the_tries_with_nothing_and_wakes_on_a_new_observation`.
- **Reply Plan given the Agenda with earlier tries; Get curious given the open needs.** The real Reply Plan's input (Model Call Log) had "What you are exploring about them (the Agenda)…" with the Pattern Type marked never to say, "Still to learn: …" and "Tried before: - Nothing yet.", and the aimed Curiosity as [1] among the due ones. Every later reply whose lead Move was Get curious was told "…aim it at one of these: how it goes for them with friends, not heard yet; a time it didn't happen, when it might have.", with no Pattern name. The one Get curious reply from before any Exploration had none. Tests: `test_the_reply_plan_sees_the_agenda_and_the_aimed_curiosity_first`, `test_a_move_that_asks_a_question_is_given_the_open_needs`.
- **An answer that settles an unclear Observation is tagged clear.** After the aimed question, the User wrote "honestly I only said yes because I was scared she would be hurt and pull away from me if I said no, it was never about doing it perfectly". At Conversation end the real tagger settled it: the Observation became clear (CONF.AVOID.BELONG, sign I5, no second Pattern Type), and the try came back `useful`. (The tagger's input isn't in the Model Call Log for this User, but only the settling step clears an Observation, and it runs only on stories an aimed Curiosity asked about.) Tests: `test_an_answer_that_settles_the_unclear_story_is_tagged_clear_and_useful`, `test_a_settled_unclear_story_becomes_clear_under_the_pattern_type_named`, `test_code_keeps_a_settling_only_for_one_of_its_two_pattern_types_and_a_sign` (6 cases), `test_a_story_is_settled_once_and_an_answer_with_no_settled_list_settles_none`, `test_a_settled_unclear_story_is_a_useful_try`.
- **Pattern exploring off.** Switched off for this User: the Reply Plan got no Agenda and the waiting aimed Curiosity wasn't offered; the Conversation end changed nothing (before and after: 2 Explorations, 5 tries, 5 aimed, 1 waiting). The Features page lists Pattern exploring, off for everyone. Tests: `test_with_pattern_exploring_off_nothing_is_made_offered_or_deleted`, `test_pattern_exploring_works_only_while_pattern_noticing_works`, `test_no_agenda_is_kept_while_curiosities_is_off`, `test_admins_see_every_feature_with_its_default_and_no_change_yet`.
- **Delete My Data and Account Deletion.** `DELETE /api/me/data` as the User: 2 Explorations, 5 tries, 21 Curiosities and 8 Observations → all 0, account kept. Reconnected and rebuilt one Exploration; `DELETE /api/me`: 1 Exploration, 1 try, 2 Curiosities and the User → 0. Tests: `test_delete_my_data_and_account_deletion_remove_explorations` (both routes), `test_delete_my_data_removes_every_kind_of_data_but_keeps_the_account`.
- **Pure functions; every number a setting with a hint.** `open_needs`, `next_way`, `try_outcome`, `tries_with_nothing`, `rank_explorations`, `aimed_question`, `not_before_after`, `judge_tries`, `next_state`, `with_place`, `next_try_for` and `plan_agenda` in `core/agenda.py`, and `plan_settled` in `core/observations.py`, are tested with plain values in `tests/test_agenda.py` (37) and `tests/test_observation_checks.py`. Platform settings (browser, 1280 and 390): the Patterns section shows "Explorations on the Agenda" 3, "Wait after a try with nothing" 3 and "Tries with nothing before resting" 4, each with its hint; saving 1 for the last kept it after reload. The new Eval run page's override picker lists all three. Tests: `test_every_agenda_number_is_a_setting_with_a_hint_and_an_eval_override`, `PlatformSettingsForm.test.tsx`. Migration: `test_the_migration_keeps_user_data_and_reloads_the_two_prompts`.
- **Seen on the way, not from this change.** The Safeguard took "I was scared she would be hurt and pull away from me if I said no" as a crisis and sent the Crisis Reply (likely a false alarm worth a look). Under machine load the worktree's Postgres briefly went into recovery mode, and one reply fell back to "my thoughts got tangled".
- **Checks.** `make check` on the final code after rebasing on main (issue 14 and OpenRouter issues 01 to 03): ruff clean, ruff format clean, mypy clean (246 files), pytest 2027 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 137 files, 953 tests passed. No pixel test: no page layout changed (three fields added to an existing section and a Feature row).
- **Review.** Standards and spec reviews run. Fixed: rank order for the Reply Plan, way order, settled stories, no Agenda while Curiosities is off, next-try planning returns its changes, shared helpers. Left: `aimed_question`'s need × way branches and `agenda.py`'s size (rules, wording and two services in one module).

## Completion

- Completed: 2026-11-24
- Commit: <merge commit, filled in after merging>
