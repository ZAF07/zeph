# 11 — A tagging step keeps checked Observations, silently

Status: completed
Track: B
Blocked by: 10

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 56, 68, 79, 82). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

A new Conversation-end step, after Life Threads and before Pattern keeping, behind a new Feature, Pattern noticing (off for everyone to start). It is given the Conversation, the Threads it touched and the whole Pattern Catalog, and writes Observations: Pattern Type (one, or two when it can't tell, which makes it unclear) and the sign matched; for or against; the User's exact quote; a context line; who it is about; relationship, power, setting and stance from the fixed lists; the kind of evidence (real story, reported habit, answer to a "what if", own opinion). Code marks one situational when its tags match its Pattern Type's "anyone would do this" description.

Code keeps only Observations whose Pattern Type and sign exist, whose quote is word for word in the User's own texts of that Conversation (never the Companion's), and whose tags come from the lists. Each kept Observation stores the catalog version it was tagged under and stays after Message Retention deletes its message (ADR-0027). Nothing changes in chat. Own prompt, model and thinking switch as Platform Settings.

## Acceptance criteria

- [x] With Pattern noticing on for a User, ending a Conversation runs the tagging step and saves the valid Observations
- [x] An Observation with an unknown Pattern Type or sign, a quote not word for word in the User's texts, a quote from the Companion's texts, or a tag outside its list is dropped
- [x] An Observation naming two Pattern Types is saved as unclear
- [x] An Observation whose tags match the "anyone would do this" description is saved as situational
- [x] Each Observation keeps its catalog version, day, Life Thread if any and who it is about
- [x] The Model Call Log shows the tagging step with how many Observations were tagged and how many dropped, never their words
- [x] Observations survive Message Retention deleting their message
- [x] With User Memory off, or Pattern noticing off, the step doesn't run and nothing is deleted
- [x] Deleting a Life Thread removes its Observations; Delete My Data and Account Deletion remove them all
- [x] The tagging prompt, model and thinking switch are Platform Settings with hints, and show in the core services list
- [x] Replies are unchanged
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `10-pattern-catalog-loads-and-admins-read-it.md`

## Comments

Plan (24 Nov 2026, branch `pattern-11-tagging-step`, worktree `ai-chat-companion-pattern-11`):

- **"Anyone would do this" as tags.** Code can't match free text, so each Pattern Type gets `anyone_would_when`: a list of tag matches (e.g. `relationship: [stranger]`, `power: [above]`). An Observation is situational when its tags fit any one match. The Admin page isn't changed in this issue. (Changed while building: only CONF.AVOID.BELONG goes to 0.2.0 with matches. ACH.WORTH.PERF's and CTRL.UNCERT.PLAN's "anyone would" is about stakes and crises, not people or places, so it can't be put as tags; the field is optional and they stay at 0.1.0, and none of their Observations is situational yet.)
- **New step** `PatternTagger` in `core/observations.py`, after Life Threads and before Pattern keeping, only while User Memory and the new Feature Pattern noticing work (off for everyone to start, not in the reply note). It is given today, the Threads touched (numbered), every current Pattern Type (signs, signs against, look-alikes, anyone-would), the tag lists and the Conversation. Own prompt, model and thinking switch (`pattern_tagging_*`), in the core services list. Unreadable answer asked once more.
- **Checks in code (pure):** Pattern Type exists (one, or two different ones = unclear); sign is in that Pattern Type's signs for "for", signs against for "against"; quote is word for word in one of the User's own texts of the Conversation (spaces and curly quotes evened out, nothing else); relationship, power, setting and stance are from their lists or empty; kind of evidence from its list; who it's about given; exact repeats dropped. Thread number not shown → no Thread.
- **Saved** in a new `observations` table: User, Conversation, Pattern Type and its version (and the second when unclear), sign, for/against, quote, context line, day (of the text quoted, User's time zone), Life Thread (deleted with it), who, the four tags, kind, unclear, situational. No link to the message, so Message Retention can't touch it. Delete My Data and Account Deletion remove them.
- **Model Call Log:** a tagging shape (tagged, dropped) on the step's call, for every User; counts only. Shown on the trace page.
- Not here: linking Observations to Patterns and scoring (12), the kept-quotes list (13), the Eval (14), the exclusion flag.

Decisions made while building (24 Nov 2026):

- **Word for word** means the quote is inside one of the User's own texts of that Conversation (text messages and photo captions, never the Companion's texts or a photo's description), starting and ending on whole words, after evening out runs of spaces and curly quotes. Nothing else is forgiven (not case, not spelling) and a quote can't join two texts. The review caught that a plain substring let "aid yes" match "said yes"; fixed with a test. No minimum length: a one-word quote is still the User's own word.
- **Also dropped:** an exact repeat (same Pattern Type, sign and quote), and one with no context line or no "who it's about". Both are counted as dropped.
- **Unclear:** the sign is checked against the first Pattern Type named; the second only has to be a different Pattern Type in the catalog. Both versions are kept.
- **Empty tags:** relationship, power, setting and stance may be empty (null) when there is no one else or it isn't clear; a value given must be from its list. The kind of evidence is required.
- **Model Call Log:** "tagged" is everything the model wrote, "dropped" what code refused; kept = tagged − dropped. Also added to Eval traces' table (`eval_model_calls`), since Eval traces read through the same row reader.
- **Migration** is 0081: pattern-01 merged its own 0080 first.
- **Design reference:** the Pattern Catalog design fixture now says CONF.AVOID.BELONG 0.2.0 (a backend test keeps it equal to the real catalog). `reference/AdminPatternCatalog.html` still draws "v0.1.0"; the pixel test passes at 0.03%, so it was left for the designer to update.

Evidence (24 Nov 2026, worktree stack on 3020/8020, real DeepSeek model, made-up Users only; final build `cd19c8f`):

- **Runs and keeps valid Observations.** Made-up User Robin, Pattern noticing on for them only (switch row), one ended Conversation about saying yes to their sister Mei. The scheduler tick ran conversation_end → life_threads → pattern_tagging → patterns → curiosities → portrait. Three Observations kept: CONF.AVOID.BELONG 0.2.0, signs I2, I4 and I5, "for", each linked to the new Thread "Helping Mei move", about "Mei, their sister", family / equal / neutral, real_story, day 2026-11-24. Repeated on the rebased build and on the final build with the same result. Tests: `test_with_pattern_noticing_on_a_conversation_end_keeps_the_valid_observations`, `test_tagging_runs_after_life_threads_and_before_pattern_keeping_and_sees_it_all`.
- **Drops.** The real tagger, run in the backend container on the real database with a scripted answer of 8 entries: unknown Pattern Type, unknown sign, a quote not in their texts, a quote from Zeph's text, a tag off its list and a quote cutting into a word were dropped; 8 tagged, 6 dropped. Tests: 20 cases in `test_an_observation_that_fails_a_check_is_dropped`, `test_a_quote_that_cuts_into_a_word_is_not_word_for_word`, photo caption vs description.
- **Unclear.** The same run kept "KEEP unclear" with second Pattern Type ACH.WORTH.PERF 0.1.0. Tests: `test_two_pattern_types_make_an_unclear_observation`, `test_unclear_and_situational_observations_are_saved_as_such`.
- **Situational.** The same run kept one tagged relationship "stranger" as situational (CONF.AVOID.BELONG's `anyone_would_when`). Tests: `test_situational_means_the_tags_fit_one_anyone_would_situation` (5 cases).
- **Version, day, Thread, who.** In the rows above: `pattern_type_version` 0.2.0, `day`, `life_thread_id` set, `about`. After `make restart` the catalog held CONF.AVOID.BELONG 0.2.0 current.
- **Model Call Log.** Signed-in Admin on the trace page: the "Pattern tagging" card shows "Observations tagged 3", "Dropped by code 0" and "No content kept for this User". No `model_calls` row held the quotes. Tests: `test_the_model_call_log_shows_how_many_were_tagged_and_dropped_never_words`, `ModelCallTraceView.test.tsx`.
- **Survives Message Retention.** Robin's messages moved back 40 days (retention 30); after the next tick 0 messages were left and all 5 Observations stayed. Test: `test_observations_stay_after_message_retention_deletes_their_messages`.
- **Off means off.** With User Memory off a new Conversation ended with no tagging call and Observations stayed at 5. With User Memory on and the Pattern noticing switch removed (default: off), Life Threads ran but tagging didn't, still 5. Tests: the three "off" tests in `test_pattern_tagging.py`.
- **Deletions.** A signed-in plain User whose Conversation was tagged by the real model (2 Observations on Thread "Helping Mei move", plus 1 with no Thread): deleting the story on the Memories page's "What's going on" tab removed the 2 and kept the 1. "Delete my data" on Account & privacy removed it (account kept). After adding one again, "Delete my account" removed the account and the Observation. Tests: `test_deleting_a_life_thread_removes_its_observations`, `test_delete_my_data_removes_every_observation`, `test_account_deletion_removes_every_observation`, `test_delete_my_data_removes_every_kind_of_data_but_keeps_the_account`.
- **Settings.** Prompts & models page: "Pattern tagging" card ("Conversation end · after Life Threads, while Pattern noticing works") with its model, thinking and prompt, each with its hint. Features page: "Pattern noticing", "Never changed", off. Tests: `test_the_tagging_prompt_model_and_thinking_are_settings_in_core_services`, `test_core_services_list_their_prompt_and_model_settings`, `test_admins_see_every_feature_with_its_default_and_no_change_yet`.
- **Replies unchanged.** The real reply path, run in the backend container with a recording chat channel (worktree Telegram limit), for Robin (made an Admin for the run so content was kept) after their Observations were saved: a text about Mei got a real two-part reply. Its Safeguard, Understanding, Reply Plan and Reply calls held no Observation context line, no Pattern Type ID and no "Observation". No reply-path file changed on the branch. Test: `test_replies_are_not_given_observations`.
- **Checks.** `make check` on the final build: ruff clean, ruff format clean, mypy clean (232 files), pytest 1813 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 136 files, 928 tests passed. Pixel test (git-ignored copy of `compare.cjs` blocking Clerk's protect probes): `PASS AdminPatternCatalog 0.03% differs, height 2514 vs 2514`. `AdminModelCallTrace` fails on height (1357 vs 2274), with the same numbers with this branch's web changes stashed, so not from this branch.
- **Review.** Standards and spec reviews run. Fixed: whole-word quotes (above), catalog service passed in, one plain helper for fixed-list values, checks return early, the shared `read_text` docstring, a clearer name. Left: the four tag names are listed in several places (a shared table could gather them), and Pattern Type ID/version pairs could be one small type; both left for issue 12, which reads these.
