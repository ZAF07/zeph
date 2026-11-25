# 07 — Ready gate: code decides when a Pattern may be shared

Status: completed
Track: A
Blocked by: 04

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 26, 27, 30, 31, 66). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

A Pattern becomes ready only when code finds all ten checks true (listed in `docs/pattern-pipeline/README.md`): enough situations; enough Conversations; resting on clear Observations; score past the bar; a counter-test asked and answered with the evidence against under a bar; situational Observations carrying no weight; every quote checked; one model call arguing the other side found no better explanation (it can only block); safe; not rejected and its Pattern Type approved.

Safe means: no exclusion of its Pattern Type applies (the tagging step flags these from open Life Threads and recent Day Summaries; the catalog says whether evidence is ignored or counted but not shared), no Safeguard Event within an Admin-set time (start 14 days), and not a topic on the Admin-set ruled-out list unless the User raised it. A counter-test showing the behaviour doesn't happen in some kind of situation narrows the Pattern ("with seniors, not with friends") instead of failing it. Nothing is shared in this issue: a ready Pattern waits.

## Acceptance criteria

- [x] A Pattern moves to ready only when all ten checks pass, and the log records which check last blocked it
- [x] A Pattern of a draft Pattern Type never becomes ready, however strong its evidence
- [x] A Pattern with no answered counter-test never becomes ready
- [x] A counter-test showing it doesn't happen with some kind of person narrows the Pattern, and the narrowing is saved
- [x] The other-side model call runs only when the other checks pass, and its "better explanation" answer blocks; a failed call blocks
- [x] An active exclusion stops scoring or sharing as its Pattern Type says
- [x] A Safeguard Event within the Admin-set time blocks ready
- [x] A ruled-out topic blocks unless the User raised it; Admins edit the list
- [x] A ready Pattern returns to suspected when evidence against arrives
- [x] The gate is a pure function with tests for each check; the other-side prompt, model and thinking switch are Platform Settings
- [x] Admins see how many Patterns a User has ready, never their content
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `04-explorations-and-the-agenda.md`

## Comments

- 25 Nov 2026 (from issue 06): scoring now counts a situation only when something other than a "what if" answer counts for the Pattern there (`score_situation` in `core/pattern_scoring.py`). The ready gate should use the same situations count, so Thought Experiment answers alone never make a Pattern ready.

### 25 Nov 2026: built

What was built:

- **The gate** (`core/ready_gate.py`): `ready_check`, one pure function, names the first of the ten checks a Pattern fails, from facts worked out by `gate_facts` (pure). `ReadyKeeper` judges a User's suspected and ready Patterns from what is stored (no model call) and moves them; `ReadyGate` runs it right after scoring at Conversation end, while Pattern noticing works, and makes the last two checks: every quote read again against the texts still kept, then one model call that argues the other side.
- **Other side**: `pattern_other_side_prompt`, `_model`, `_thinking` (core service "Other side", step `pattern_other_side`). It runs only when the other nine checks pass. A yes, an unreadable answer or a failed call blocks. Its last answer is kept with the Pattern and stands for the same evidence.
- **Narrowing** (`narrowings_of`, pure): evidence against that is all with other kinds of people than the evidence for narrows the Pattern, is saved on it (`patterns.narrowings`) and isn't counted against it.
- **Safe**: the tagging step now flags which Pattern Type exclusions apply to the User (from their open Life Threads and latest Day Summaries) and which ruled-out topic an Observation touches, with whether the User raised it. A Safeguard Event within the Admin-set days blocks.
- **The log**: `patterns.blocked_by` keeps the check that last stopped a Pattern; the move to ready records it, and a move back from ready records the check it now fails (`pattern_moves.blocked_by`).
- **Settings**, in the Patterns section of Platform settings, with hints and Eval Variant overrides: `pattern_ready_situations` 3, `pattern_ready_conversations` 2, `pattern_ready_points` 300, `pattern_ready_against_under_points` 100, `pattern_safeguard_quiet_days` 14, `pattern_exclusion_summary_days` 7, `pattern_ruled_out_topics`.
- Migration 0098. Docs: `docs/pattern-pipeline/README.md`, `docs/message-pipeline/README.md` (b4), `docs/pattern-catalog/README.md`, `CONTEXT.md`.

Decisions made while building (owner may want to look):

- **The gate runs while Pattern noticing works.** Pattern sharing is issue 08's Feature. A ready Pattern waits.
- **The ruled-out list starts with four topics I picked**: abuse, sexual trauma, self-harm or suicide, eating and body image. For the owner to correct on Platform settings.
- **Order of the checks.** Situations, Conversations, counter-test, score, clear, situational, safe, allowed, quotes, other side. Too much evidence against is named before the low score it causes.
- **Situations bar**: the Admin-set number, or the Pattern Type's `situations_needed` when that is more.
- **Counter-test "asked and answered"** uses the Agenda's rule: an Observation against came, or a counter-test try was useful.
- **"Situational carry no weight"** is judged by the catalog now, so a rule added after an Observation was tagged still counts.
- **"Every quote checked"**: read again against the Conversation's texts still kept; one whose texts Message Retention deleted was checked at tagging and counts as checked.
- **Exclusions**: a flag stays until the User's next tagged Conversation. With `ignored`, Observations tagged then are marked excluded and never carry weight.
- **"Not rejected"** has no source yet: after issue 24 no User has a Pattern from before the catalog, and the contested state comes with issue 08. The gate never looks at a contested Pattern.
- **A new setting not in the issue**: `pattern_exclusion_summary_days`.
- **A ready Pattern that fails goes to where its score puts it** (suspected, noticed or closed), in one logged move.

Limits:

- Scoring still counts evidence against that only narrows, so it can pull a Pattern under the suspected bar, where the gate doesn't look.
- A topic added to the ruled-out list doesn't reach Observations tagged before. The list can't be emptied.
- Between two looks a ready Pattern can be stale (a Safeguard Event mid-Conversation, fading). Issue 08 must look again before sharing. Struggling is not looked at here.
- The log holds the blocking check only on moves to or from ready; a suspected Pattern's is on the Pattern.
- Admins see the ready count only, not which check blocks.
- The Tagging Eval's cases don't cover exclusions or ruled-out topics. No Eval was run (Evals cost money).
- Migration 0098 reloads `pattern_tagging_prompt` from the seed, so an Admin's edit to it is lost.

Evidence (25 Nov 2026, worktree stack on 3010/8010, real model, Conversation ends run by the running backend's scheduler; a made-up User only, their Conversations put in with SQL three hours old so the next tick ended them; signed-in Admin in a real browser (Playwright)). Two runs: **run 1** on the branch before it was rebased onto issues 17 and 24, **run 2** on the final rebased build with a fresh database (migrations 0096 to 0098 applied by the running backend). After run 1 the gate changed in two ways only: the check for Patterns rejected before the catalog was removed, and the other-side call uses the shared "thinks only when the model can" rule. Run 2 redid the checks those touch. One later change (excluded Observations left out of narrowing) is covered by a test only.

- **Ready only when all ten pass; the log says which check last blocked.** Run 2: after two stories the Pattern was suspected, `blocked_by` situations, no other-side call. After a second Conversation: `blocked_by` clear (one story was unclear), narrowing saved. After a third: the real other-side call ran, then `suspected → ready`, 497 points, 5 situations, log `blocked_by` clear. Run 1 the same, with `blocked_by` score. Tests: `test_a_pattern_becomes_ready_once_all_ten_checks_pass_and_the_log_says_what_blocked`, `test_each_check_alone_blocks_ready` (16 cases).
- **Draft Pattern Type never ready.** Run 2 and run 1: with CONF.AVOID.BELONG made draft in the database, the next Conversation end moved the ready Pattern back, `blocked_by` allowed, no other-side call. Tests: `test_a_pattern_of_a_draft_pattern_type_never_becomes_ready`, `test_a_pattern_of_a_draft_pattern_type_is_never_ready`.
- **No answered counter-test, never ready.** Run 2 and run 1: with the Observation against removed, the Pattern stayed suspected, `blocked_by` counter_test, no other-side call, though its score passed. Tests: `test_a_pattern_with_no_answered_counter_test_never_becomes_ready`, `test_a_counter_test_that_was_only_brushed_off_does_not_count`.
- **Narrowing saved.** Run 2 and run 1: the real tagger read "With my partner Sam I just say it straight" as D1 against, partner; the Pattern kept `{"tag": "relationship", "holds_with": ["colleague", "friend"], "not_with": ["partner"]}` and became ready with that evidence not counted against it. Tests: `test_a_counter_test_showing_it_doesnt_happen_with_a_partner_narrows_it_and_is_saved`, four `narrowings_of` rule tests.
- **Other side only when the others pass; "better" blocks; a failed call blocks.** Run 2: no `pattern_other_side` call in the Model Call Log at any Conversation end where another check blocked; with the prompt made to answer "better", `blocked_by` other_side; with the real prompt back, the real call cleared it and it became ready, log `blocked_by` other_side. Run 1 the same, plus: with the model set to one that doesn't exist, the call was logged with `HTTPStatusError`, the backend logged "Could not argue the other side of a Pattern", the Pattern stayed blocked and the later steps ran. Tests: `test_a_better_explanation_blocks_and_is_argued_again_only_on_new_evidence`, `test_a_failed_or_unreadable_other_side_call_blocks_and_the_rest_goes_on` (2 cases), `test_checks_made_on_other_evidence_than_is_stored_now_never_make_it_ready`.
- **An active exclusion stops scoring or sharing.** Run 2: a Conversation about a parent who died nine days ago; the real tagger flagged Grief for nine Pattern Types (seven `ignored`, two `counted_not_shared`), the two Observations from it were kept as `excluded` and the score stayed 455, and the ready Pattern went back, `blocked_by` safe. (In run 1 the flags were saved but the model wrote no Observation; the prompt now says to keep noting them.) Tests: `test_an_exclusion_whose_evidence_is_ignored_stops_scoring_and_ready`, `test_an_exclusion_whose_evidence_is_counted_scores_but_is_never_ready`, `test_only_exclusions_the_catalog_lists_are_flagged_once_each`.
- **Safeguard Event within the Admin-set time.** Run 1: an event 13 days old moved the ready Pattern back, `blocked_by` safe; moved to 15 days old, the next end made it ready again with no new other-side call. Tests: `test_a_safeguard_event_within_the_admin_set_days_blocks_ready`, `test_a_pattern_taken_back_for_safety_is_ready_again_without_asking_the_model`.
- **Ruled-out topic unless the User raised it; Admins edit the list.** Browser, Platform settings, 1280 and 390 (both runs): "Ruled-out topics" shown with its hint; "money" added, saved and kept after reload. Run 1: the real tagger marked "My friend Jun asked to borrow 500 dollars…" as `money`, raised by the User, and the Pattern stayed ready; with that Observation set to not raised, the next end moved it back, `blocked_by` safe; set back, it was ready again. Tests: `test_a_ruled_out_topic_blocks_unless_the_user_raised_it_and_admins_edit_the_list`, `test_a_ruled_out_topic_the_user_raised_does_not_block`.
- **Ready returns to suspected on evidence against.** Run 1: a Conversation where they told Jun and Priya straight; the real tagger wrote two D1 against (friend, colleague), the narrowing went and `ready → suspected`, `blocked_by` counter_test. Tests: `test_a_ready_pattern_returns_to_suspected_when_evidence_against_arrives`, `test_a_ready_pattern_goes_back_at_once_when_its_evidence_is_deleted`.
- **Pure function with tests for each check; other-side prompt, model and thinking are Platform Settings.** `tests/test_ready_gate_rules.py` (39 tests, no database). Browser, Prompts & models, 1280 and 390: "Other side" listed with "Conversation end · after scoring, only for a Pattern that passed every other ready check". Browser, Platform settings: the six numbers shown with their hints. Tests: `test_the_gate_numbers_and_the_other_side_call_are_settings_with_hints`, `test_the_other_side_call_uses_its_own_prompt_model_and_thinking`.
- **Admins see how many are ready, never content.** Browser, Users page, the made-up User's panel: "Ready Patterns 1" at 1280 and 390 (run 1), the row again at 390 (run 2); the page held no Pattern Type ID or name, no person's name and no quote. No Dashboard file for this page changed. Test: `test_admins_see_how_many_patterns_a_user_has_ready_never_their_content`.
- **Checks.** On the rebased code: ruff clean, ruff format clean, mypy clean (266 files), pytest 2288 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 140 files, 973 tests passed. After the last small change (narrowing) the two gate test files were run again (63 passed), with ruff and mypy. Migration: `test_the_migration_keeps_user_data_and_reloads_the_tagging_prompt` (down to 0097 and back, no User data lost).
- **Review.** Standards and spec reviews run. Fixed: a Pattern could stay blocked by "other side" for good after being taken back; checks made while the evidence changed could make a Pattern ready; a ready Pattern whose Pattern Type left the catalog stayed ready; narrowing wasn't saved for a ready Pattern; names. Left as is and listed above: scoring counts narrowing evidence, the counter-test rule, ruled-out topics not reaching older Observations.
- **Not from this issue's own design files:** no reference HTML was changed; Platform settings and Prompts & models are not drawn field by field in the references.

## Completion

- Completed: 2026-11-25
- Commit: <to be filled in after the merge>
