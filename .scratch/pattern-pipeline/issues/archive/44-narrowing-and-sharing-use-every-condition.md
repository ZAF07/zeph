# 44 — Narrowing and sharing use every Condition

Status: completed
Track: A
Blocked by: 41, 43 (43 builds the coverage table this issue reads)

## Parent

Issue 23, decisions D9, D10 and D11 (point 3), and the owner's principle there. ADR-0031. Today's rules: `narrowings_of` in `core/pattern_scoring.py`, "the ready gate", "sharing a ready Pattern" and "the Patterns tab" in `docs/pattern-pipeline/README.md`.

## What to build

A Pattern can be narrowed by any Condition, with guards so it can still be shown wrong. When it is shared, Zeph also says one thing it hasn't seen.

- **Narrowing (`narrowings_of`):**
  1. each Condition is looked at alone; no combinations;
  2. a Condition narrows only when at least `narrowing_stories_needed` (2) clear stories for have it known on the side that holds, and the clear evidence against is all with other values (today's rule, with the bar raised from 1);
  3. at most `narrowings_per_pattern` (2) narrow one Pattern: those with the most stories behind them, ties by a fixed order of Conditions;
  4. evidence against that the kept narrowings don't explain counts against the Pattern in full.
- **Where it shows** (the gate's other-side call, sharing, the Patterns tab): every kept narrowing in plain words for each Condition ("in a group; not one-to-one", "when a lot is riding on it"). For state, gentle words about the moment ("on days you were worn out"), never a label for the User.
- **One thing not seen, when sharing:** code hands the reply at most one gap from the coverage table (the open missing-Condition need of issue 43, read from its coverage table; build no second version of that rule), to say as something Zeph doesn't know ("I've only heard about this in meetings. I don't know if it's the same when it's just the two of you"), never as a claim. A state gap is never handed over, since Zeph never names a state first. The reply that shares still asks nothing else beyond "what would prove it wrong".
- **The Prediction** is unchanged, set inside the narrowing as today.
- **Scoring:** Conditions never add points or situations; a situation stays one Life Thread and the cap stays per person. Add tests that say so.
- **Numbers:** `narrowing_stories_needed` and `narrowings_per_pattern` are Platform Settings with hints in the Patterns section, overridable in Eval Variants.
- **Copy:** new words for the Patterns tab are Copy slots (`memories.patterns.*`); UI work follows `web/design/README.md` and the pixel test.

## Acceptance criteria

- [x] A Condition narrows only with at least 2 clear stories for on the side that holds; one story no longer narrows
- [x] With three Conditions able to narrow, only the two with the most stories do, and evidence against that those don't explain counts against the Pattern
- [x] Evidence against that a kept narrowing explains is not counted against the Pattern, as today
- [x] Two Observations in one Life Thread with different Conditions count as one situation, and the cap inside it is per person
- [x] The ready gate's other-side call, the shared Pattern and the Patterns tab show each kept narrowing in plain words, state in gentle words
- [x] A sharing reply is handed at most one unseen value, marked to be said as not known; never a state; none when nothing is one-sided
- [x] The Prediction is still set inside the narrowing
- [x] The two numbers are on Platform settings with hints and can be overridden in an Eval Variant
- [x] `docs/pattern-pipeline/README.md`, `lifecycle.md` and the `CONTEXT.md` Pattern entry say what is built
- [x] `pytest`, `ruff`, `ruff format` and `mypy` pass; `pnpm lint`, `format:check`, `typecheck` and `test` pass for any Dashboard change, with the pixel test
- [x] Checked in the running app (`/run`): a Pattern seen in a group and shown not to happen one-to-one is shared with that narrowing, the reply says one thing Zeph hasn't seen, and the Patterns tab shows where it shows

## Comments

## For the owner afterwards (not acceptance criteria)

- The Patterns tab's new line ("It shows in a group; not one-to-one.") and its 25 value words are new Copy that no reference file draws. `web/design/README.md` says the reference changes first. The drawn line (relationship) still passes the pixel test; please look at the new words on Admin → Copy and update `Memories--tab-patterns.html` if you want them drawn.
- Relationship words on the tab are seeded as the reference draws them ("family, friend", "colleague"), next to "your partner" and "strangers". Reword on Admin → Copy once the reference says how.
- Decide: when the most one-sided Condition is the state going in, the sharing reply is handed nothing, even if another Condition is one-sided too.

### 26 Nov 2026 — built, checked and closed

**What was built.** `narrowings_of` (`core/pattern_scoring.py`) reads the coverage table: each Condition alone, at least `narrowing_stories_needed` (2) clear stories for that say it, evidence against all under other values, at most `narrowings_per_pattern` (2) kept, most stories first, ties by `CONDITION_ORDER`. `core/narrowing_words.py`: plain words for every value of every Condition. `core/pattern_sharing.py`: `not_seen_yet` (the Agenda's own `missing_condition_need`, never a state) and `describe_not_seen`. The Patterns tab words each narrowing from 26 new Copy slots. Two Platform Settings.

**Decisions made while building.**
- No migration: a stored narrowing keeps its shape (`tag` now holds any Condition; the old values relationship and power are still valid).
- The two numbers travel in `ScoringNumbers`, so every place that counts a Pattern's evidence uses the same rule.
- "Stories behind a narrowing" is the number of clear stories for that say the Condition.
- The Patterns tab gets the Condition and stored values from the API and words them from Copy: one slot per value, the old line for relationship and power ("with …"), a new line (`memories.patterns.shows_when`) for the rest.
- The rule to say a state gently goes only to the reply or Check-in that shares; everywhere else the words alone are about the day ("on days they were worn out").
- The unseen value's example sentence is written from the real words, after the first run's reply mixed the fixed example into its own.

**Review.** Two reviews (standards, spec). Fixed: "every story" became "so far you have only heard"; the gentle-state rule no longer lands in the Portrait and follow-up prompts; a named helper for the Copy slot. Left as judgement calls: the field is still `PatternNarrowing.tag`; the value words live twice (about them in code, to them in Copy); `ScoringNumbers` holds two numbers that aren't weights.

**Checks.** ruff clean, ruff format clean, mypy clean, pytest 2693 passed; web: eslint, prettier and tsc clean, Vitest 991 passed (141 files). Pixel test: `Memories--tab-patterns` PASS (0.13%), `M-Memories--tab-patterns` PASS (0.29%), run from a copy of `compare.cjs` that blocks Clerk's protect probes (the shipped one hangs on this machine).

**Evals.** None run, so no cost. No Eval case covers the unseen value.

**How it was checked in the running app.** On this worktree's stack (fresh database, seeds loaded), as a signed-in test Admin with Pattern noticing, exploring and sharing on, real models, and the chat channel swapped for the one that logs instead of sending. Texts were posted to the Telegram webhook; each Conversation's times were moved back a day and the running backend ended it itself. Nothing about the Pattern was set by SQL before the first share. For the second share the Pattern was put back to ready by SQL.

**Evidence per criterion**

- **At least 2 stories; one no longer narrows.** `test_one_story_for_no_longer_narrows`, `test_stories_that_dont_say_the_condition_dont_count_toward_the_bar`. Running app: the Pattern had 3 clear group stories (a fourth was situational). With the setting at 4 the next look found no narrowing, the one-to-one story counted against (415 to 276 points) and the Pattern went back to suspected, blocked by counter-test; back at 2 it was narrowed and ready again, with no new other-side call.
- **Three Conditions, two narrow; unexplained evidence counts.** `test_only_the_two_conditions_with_the_most_stories_narrow`, the tie test, `test_the_most_narrowings_is_the_admin_set_number`. Running app: the real `PatternScorer` and `ReadyKeeper`, run inside the backend container on a made-up User with 5 stories for and 3 against (stakes, state and audience could each narrow), saved the narrowings stakes and state going in, and the score was 560: 700 less the one-to-one story audience would have explained.
- **Explained evidence isn't counted.** `test_evidence_against_a_kept_narrowing_explains_is_not_counted`. Running app: with the audience narrowing the Pattern scored 415 with the one-to-one story left out, and became ready.
- **One Life Thread is one situation; the cap is per person.** `test_one_life_thread_is_one_situation_whatever_its_conditions`, `test_the_cap_inside_a_situation_is_per_person_not_per_mix`, `test_conditions_never_add_points_or_situations`. Running app: the made-up User's 5 stories, each under different Conditions, gave 5 situations and 140 points each, no more.
- **Plain words in the gate, sharing and the tab; state gently.** `test_each_condition_is_said_in_its_own_plain_words`, `test_every_value_of_every_condition_has_plain_words`, `test_the_state_going_in_is_said_gently_about_the_day_never_as_a_label`, `test_the_other_side_is_given_every_kept_narrowing_in_plain_words`, and the Vitest Patterns tab test ("It shows on days you were worn out; not on days you felt steady."). Running app: the other-side call read "- It shows in a group; not one-to-one"; the reply's instructions read "It shows in a group; not one-to-one."; the Patterns tab showed "It shows in a group; not one-to-one." at 1280 and 390. State wording was checked by tests only: no real story in the run gave a state narrowing.
- **At most one unseen value, as not known; never a state; none when nothing is one-sided.** `test_a_sharing_reply_is_handed_one_unseen_value_of_a_one_sided_condition`, `test_the_unseen_value_is_the_agendas_open_missing_condition_need`, `test_a_value_a_useful_try_closed_is_not_handed_over`, `test_nothing_is_handed_over_when_no_condition_is_one_sided`, `test_a_state_gap_is_never_handed_to_a_sharing_reply`, and `test_a_pattern_heard_about_only_in_a_group_is_shared_with_one_thing_not_seen` through the app. Running app: the reply was handed "so far you have only heard about this in a group, and you haven't heard how it goes with other people watching. Say that in a sentence as something you don't know … never as a claim about them, and don't ask about it."
- **The Prediction is still inside the narrowing.** `test_a_shared_pattern_says_its_narrowing_one_unseen_value_and_the_prediction`. Running app: the reply gave "notice whether the yes is out of your mouth before you've decided" after the narrowing, the check kept it as the Prediction, and the Pattern moved to shared.
- **The two numbers.** `test_every_scoring_number_is_a_setting_with_a_hint_and_an_eval_override` (`tests/test_pattern_states.py`) and the Vitest form test. Running app: both are in the Patterns section with their hints; "Stories before a Condition narrows a Pattern" was changed to 3 in the browser, saved and still 3 after a reload; both keys are in the Eval Variant choices, and a Variant with 0 was refused ("must be a whole number from 1 to 50").
- **Docs.** `docs/pattern-pipeline/README.md` (a "Built" paragraph), `lifecycle.md` (Narrowing, Sharing), `tagging.md`, `CONTEXT.md` (Pattern, Condition), ADR-0031's status.
- **Checks pass, with the pixel test.** Above.
- **The /run check.** A User told four stories of going along in a group (team meeting, dinner with friends, family lunch, flat meeting) and one of speaking up one-to-one with their brother. The tagging model tagged audience group and one-to-one; the Pattern became ready, narrowed by audience (relationship didn't narrow: family was on both sides). Asked "what patterns have you noticed in me?", Zeph said: "you protect closeness by keeping disagreements small…", quoted them, then "there's one thing I don't know: I've only ever heard about this in a group. I don't know if it's the same with other people watching — or not watching at all. With Dan one-to-one you said straight out that you disagreed about the flat.", gave the Prediction and asked "And what would prove me wrong?". The Patterns tab then showed the Pattern under "Being tested" with "It shows in a group; not one-to-one."

**Not done.** No real story gave a state narrowing, so its gentle wording was seen only in tests. The Check-in that shares was not run (it uses the same three parts). The run's test Users were deleted afterwards, so the evidence is this note.

## Completion

- Completed: 2026-11-26
- Commit: 5113b328 ("Merge pattern-44-narrowing-every-condition: narrowing and sharing use every Condition", the merge of pattern-44-narrowing-every-condition into main; work commits 7cf4f5bf, d8463034, 4e89eedf, 0673550b)
