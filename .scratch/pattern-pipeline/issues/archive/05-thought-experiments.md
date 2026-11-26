# 05 — Thought Experiments: Admins manage them, Zeph asks them in chat and as a Check-in

Status: completed
Track: A
Blocked by: 04

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 6, 8, 71, 72, 73, 74, 75). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

A Thought Experiment is a made-up scenario written to tell two look-alike Pattern Types apart. Admins manage them on a new Dashboard page: wording, the two Pattern Types it separates, how sensitive it is, whether it is a starter, on or off. They are archived, never deleted. A check on save flags leading wording. A first set is loaded from a seed file.

For an Exploration, code picks the Thought Experiment for the look-alike pair with the most unclear evidence, at most one per Pattern per week (Admin-set). It is asked as a Curiosity in its own words, in chat or through the existing Curiosity Check-in Kind and its weekly limit. The User's answer becomes an Observation of the "what if" kind.

Also in this issue: the agent drafts the first set (about 30, each naming its pair) and writes `docs/thought-experiments/README.md`: how they work, where to find material, how to write a good one, how to manage them, and what an edit changes. The owner then refines the set.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [x] Admins can add, edit, switch off and archive Thought Experiments on the Dashboard; an archived one is never asked and past tries still show it
- [x] Each has its wording, two Pattern Types, sensitivity, starter flag and on/off, each with a hint
- [x] Saving one with leading wording shows a warning the Admin can act on
- [x] The first set is loaded once from the seed; a seed never overwrites an edited one or brings back an archived one
- [x] Code picks the Thought Experiment for the pair with the most unclear evidence and never more than the Admin-set number per Pattern per week
- [x] It is asked in its own words in chat, and can be sent through the Curiosity Check-in Kind within its weekly limit
- [x] An answer is tagged as an Observation of the "what if" kind
- [x] `docs/thought-experiments/README.md` exists and covers how they work, sourcing, writing, managing and what an edit changes
- [ ] The owner has reviewed the drafted first set (comment on this issue when done) — left open: the owner approved merging before reviewing (25 Nov 2026); the review is still to come
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `04-explorations-and-the-agenda.md`

## Comments

Plan (24 Nov 2026, branch `pattern-05-thought-experiments`, worktree `ai-chat-companion-pattern-05`; started once issue 04 was archived, merged and torn down):

- **Store.** `thought_experiments` (migration 0089): wording, the two Pattern Types it tells apart, sensitivity (low, medium, high, as a Curiosity's), starter, on, archived (when), a seed key. Never deleted. `exploration_tries.thought_experiment_id` links a try to the one it asked, so past tries keep showing it after an edit or archive.
- **Seed.** `seed/thought_experiments.yaml`, each with a `key`. At start, code adds each seeded one whose key isn't stored yet, in any state, so a seed never overwrites an edit and never brings back an archived one.
- **Admin page** `/admin/thought-experiments`, from the card-list template: one card each with Wording, Tells apart (two Pattern Types from the catalog), Sensitivity, Starter and On, each with a hint; add, edit, switch off and archive (with confirm); archived ones listed apart, read only, with how often they were asked. New reference `AdminThoughtExperiments.html` from card-list parts only, its baseline, the menu link on the other admin references (as issues 10 and 14 did).
- **Leading wording.** A pure code check on save (no model call): phrases that suggest the answer ("wouldn't you", "surely", "most people would", …) or a question offering only one side. Save is refused with the flags unless the Admin presses "Save anyway"; the card shows each flag with what to change.
- **Picking (code).** A new way between "would it differ with someone else" and "notice this week": for an unclear need, code takes the look-alike pair with the most unclear Observations of that Pattern, and picks a Thought Experiment for that pair that is on, not archived and never put to this User, starter or not. Never more than `thought_experiments_per_pattern_per_week` (1, Patterns section, hint, Eval override) per Pattern in 7 days (asked or waiting). None to pick: the next way is used. Other needs skip this way.
- **Asking.** It is an aimed Curiosity whose question tells the Reply to put the made-up situation in its own words (quoted), with the Thought Experiment's sensitivity. So it is asked in chat as any aimed Curiosity, or by the Curiosity Check-in Kind under its weekly limit. Switching one off or archiving it closes its waiting Curiosities at once; the Agenda also closes any left.
- **"What if" answers.** The tagging step is shown the Thought Experiments asked in the Conversation, numbered; an Observation that answers one says its number, and code makes its kind "what if" answer. Tagging prompt reloaded from the seed.
- **Docs.** `docs/thought-experiments/README.md`; the first set (~30, every look-alike pair of issue 15's catalog, one starter per area) for the owner to review.
- **Tests.** Pure tests for the leading check, picking and the weekly limit, the way order; HTTP-edge tests for the Admin API, seeding, the Conversation-end chain and tagging; web tests for the manager.

Decisions made while building (24 Nov 2026):

- **Migration is 0094.** Main took 0089 (tagging context without he or she), 0090 (DeepSeek served model names), 0091 (Claude models), 0092 (unmatched Patterns) and 0093 (Opus and Fable) while this was built; it was checked in the running app as 0091, then renumbered on the last rebase. Its downgrade removes no User data: tries only lose the link.
- **The tagger reads the words as asked** (the aimed Curiosity's question), not the Thought Experiment's current wording, so an edit mid-Conversation can't mislead it. Only a whole number matches a Thought Experiment shown; `true` doesn't count as 1.
- **The pair is picked across the Pattern's unclear stories**, as the PRD says ("the pair with the most unclear evidence"); the try still aims at the top unclear story, so the "way" order of that need moves on as before.
- **The weekly limit is per Exploration**, which is one per Pattern (unique) and goes with it.
- **No one-sided-question check.** The leading check is a word list only (phrases that suggest the answer, words that make a choice sound bad, with endings: "weakness" counts). "Save anyway" covers a word that is fine where it is. Noted in the guide's limits.
- **Pattern Type options show IDs only**, so a long name is never clipped in the select; names are on the Pattern Catalog page.
- **Starter and On are switches** (the references draw on/off as switches, not tick boxes), saved with the card's save bar.
- **Design files.** As issues 10 and 14 did, the issue's "add the reference" was followed: new `AdminThoughtExperiments.html` built only from card-list and field-row parts, its baseline and lines in `routes.json` and `manifest.json`, and the menu link on the other twelve admin references. `shoot.cjs` on the untouched references changed no baseline; after the link it changed none either, since the sidebar is cut at the 800px viewport above the new link.
- **Review (standards and spec).** Fixed: migration number and downgrade, tagger words as asked (and no per-item lookups), `true` ≠ 1, a named `way_after`, shared "times asked" words and save-failed text, a checked sensitivity instead of a cast, fixture import order. Left as judgement calls: `close_waiting` lives on the Thought Experiment repository (it closes only the Curiosities of its tries), the API counts all asks to answer for one (Admin page only), `LeadingWordingConfirm` borrows the remove confirm part (no warning part exists in the design).

- **A Thought Experiment answer can settle its unclear story.** Its Curiosity aims at the unclear story (as any aimed Curiosity for that need), so the tagging step may settle it from the answer. Seen in the running app: the Mei story became clear after the answer.

Evidence (24–25 Nov 2026, worktree stack on 3010/8010, migration 0091 (renumbered 0094 on the last rebase, unchanged otherwise); signed-in Admin in a real browser (Playwright); chat through the real webhook with the real model (`InProcessCompanion` in the backend container on the worktree database, recording chat channel), Conversation ends run by the running backend's scheduler, times moved back with SQL instead of waiting; made-up User only. Where noted, Observations and earlier tries were added with SQL, quoting the User's own texts):

- **Add, edit, switch off, archive; archived never asked; past tries show it.** Browser at 1280: added one (Add stayed off with the same Pattern Type twice), edited its wording, switched it off (folded row "Off"), archived it after the confirm ("Zeph never asks it again… Past tries still show it."); it moved to the read-only archived list; no page errors. No delete route (405 in tests). Archiving the Thought Experiment whose Curiosity was waiting closed that Curiosity at once (`curiosities.state` closed); it is never picked again. The one Zeph asked shows "1 time asked" on its card, and its try keeps `thought_experiment_id` and the words as asked. Tests: `test_admins_add_edit_switch_off_and_archive_but_never_delete`, `test_switching_one_off_or_archiving_it_closes_its_waiting_curiosity_at_once`, `test_a_waiting_thought_experiment_switched_off_or_archived_is_closed`, `ThoughtExperimentsManager.test.tsx` (7).
- **Each field with a hint.** Browser at 1280 and 390, real data (31 seeded): Wording, Pattern Type, Its look-alike, Sensitivity, Starter, On, each with its hint; no sideways scroll at 390. Pixel test (git-ignored copy of `compare.cjs` blocking Clerk's protect probes): `PASS AdminThoughtExperiments 0.07% differs, height 1370 vs 1370`; `PASS AdminPatternCatalog 0.03%`. AdminUsers, AdminCheckInLog, AdminPersona, AdminModelCallTrace, AdminCheckInKinds and its all-folded state fail on height with the same numbers recorded on main by issues 10 and 12; their baselines didn't change on this branch.
- **Leading wording warning.** Browser: adding "Surely you would tell them, wouldn't you?" showed "This wording may lead them to an answer" with "“Surely” suggests the answer…" and "“wouldn't you” suggests the answer…"; "Keep editing" closed it with nothing saved; "Save anyway" saved it. Tests: `test_leading_wording_is_refused_until_saved_anyway`, `test_wording_that_suggests_the_answer_is_flagged` (6), `test_open_wording_is_not_flagged`.
- **Seed once, never overwriting or reviving.** Fresh worktree database: 31 loaded, 5 starters, all on. Edited one seeded row and archived another, restarted the backend (seed runs again): still 33 rows (31 seeded + 2 added), the edit kept, the archived one still archived, no errors. Tests: `test_the_first_set_comes_from_the_seed_with_every_detail`, `test_a_seed_never_overwrites_an_edit_or_brings_back_an_archived_one`, `test_the_first_set_has_a_starter_per_area_and_no_leading_wording`.
- **Picked for the pair with the most unclear evidence; weekly limit.** Running app: after a real Conversation end made CONF.AVOID.BELONG suspected (Mei story unclear with ACH.WORTH.PERF), and two earlier tries backdated as vague with SQL, the next real Conversation end wrote a `thought_experiment` try for `belong-worth-team-plan` (oldest for that pair), low sensitivity. Later, with a second unclear story due the Thought Experiment way and one already asked that week, the real Agenda wrote `notice_this_week` instead; after raising "Thought Experiments per Pattern a week" to 2 on Platform settings (hint shown, kept after reload) it wrote one for `belong-worth-friend-feedback`, never repeating the first, with its Dashboard-edited wording. Tests: `test_the_thought_experiment_for_the_pair_with_most_unclear_evidence_is_picked`, `test_the_next_pair_is_used_when_the_top_pair_has_none_left`, `test_never_more_than_the_admin_set_number_a_week_for_a_pattern`, `test_a_counter_test_never_gets_a_thought_experiment`, `test_this_weeks_count_is_those_asked_in_seven_days_or_waiting`.
- **Asked in its own words; Curiosity Check-in.** Running app: Zeph asked it in chat: "Though I'm curious about something, totally made up: say your team lead shares a plan you get on well with them, and you can see a real problem with it. Nobody else has said anything. What do you do, and what's going on in your head as you decide?" (`raised`). Check-in: two real Check-in ticks (in the backend container with a recording channel) offered it as Curiosity 1 under "Something I've been wondering"; the real Check-ins model chose "A casual hello" and "A follow-up" both times, so the send itself is shown by test: `test_a_waiting_thought_experiment_can_be_sent_by_the_wondering_check_in` (sent, Curiosity raised). Chat path: `test_the_thought_experiment_for_the_unclear_pair_is_asked_and_tagged_what_if`.
- **Answer tagged "what if".** Running app: the User answered "honestly I would keep quiet in the meeting. I would not want things to get awkward with her…"; at the real Conversation end the tagger kept "I would not want things to get awkward with her, we get on so well" as CONF.AVOID.BELONG, sign I4, `what_if_answer`, and the try came back `useful`. (The backend keeps no content of that tagging call for this User, so which of the model or code set the kind isn't visible; tests show the input section and the number rule.) Tests: `test_an_answer_to_a_thought_experiment_shown_is_a_what_if_answer` (5 cases, `true` is not 1), the chat-path test above.
- **Guide.** `docs/thought-experiments/README.md`: what it is, how Zeph uses one, where they live and the seed rule, the fields, where to find material, how to write one (with a too-leading and a better example), the leading check, managing them, what each change does, the first set, limits.
- **Checks.** `make check` on the final code, rebased on main (OpenRouter 04, 06, 08, issues 16 and 22; the tagger's shared `_tag` helper from issue 16 now also passes the Thought Experiments asked, so re-tagging a past Conversation keeps answers as "what if"): ruff clean, ruff format clean, mypy clean (246 files), pytest 2095 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 138 files, 960 tests passed (two menu tests updated for the new link).
- **Seen on the way, not from this change.** Pace held the first chance to ask it (an ordinary Curiosity had just been raised), as designed. The Check-ins send fails at Telegram for the made-up chat in a worktree, as known.

## Completion

- Completed: 2026-11-25
- Commit: 96dd733 (merge "Merge pattern-05-thought-experiments: Admins manage Thought Experiments, code picks one for a User's unclear look-alike pair, answers are tagged what if"; work in 3f9f1f3 "Thought Experiments: Admins manage them, code picks one for the unclear pair, answers are tagged what if", 1c74f9a review fixes, 70f48bc Check-in test, be33458 docs, b7bbd45 menu tests, 27adee0 issue archived, 150801e migration 0094 and rebase fixes)
