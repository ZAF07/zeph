# 02 — Test the water, pace between Curiosities, and backing off after brush-offs

Status: completed
Track: A
Blocked by: 01

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 9, 10, 12, 13, 14, 15, 77). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Being proactive must not turn banter into an interview. This slice adds the fourth choice for a Need's Curiosities field and the rules for how often Zeph asks, all as code with Admin-set numbers.

Test the water: Zeph may drop one light opener; if the User doesn't engage, none for the rest of the Conversation. Just chatting starts on it. Pace: a fewest replies between two Curiosities (start 3). Follow-ups on a story the User is telling right now (the Get curious Move) don't use the Curiosity budget and have their own cap per Conversation (start 3). Backing off: after brush-offs in a row (start 2), none for the rest of the Conversation and the spacing doubles for a time (start 3 days); one engaged answer ends it. A topic the User asked to drop stays dropped.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [x] A Need can be set to test the water; Just chatting starts on it
- [x] Under test the water at most one Curiosity is offered as a light opener; after the User doesn't engage, none are offered for the rest of that Conversation
- [x] No Curiosity is offered until the Admin-set number of replies has passed since the last one
- [x] Get curious follow-ups on the User's current story don't count toward the Curiosity limit and stop at their own cap
- [x] After the Admin-set number of brush-offs in a row, none are offered for the rest of the Conversation and the spacing is doubled for the Admin-set time
- [x] One engaged answer returns the spacing to normal
- [x] Each new number is a Platform Setting with a hint, and can be overridden in an Eval Variant
- [x] The pace and backing-off rules are pure functions with their own tests
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `01-needs-say-how-curiosities-are-treated.md`

## Comments

Plan (24 Nov 2026, branch `pattern-02-test-the-water`, worktree ports 3010/8010):

- **How Zeph knows a Curiosity was brushed off mid-Conversation.** Today the reaction is only judged when the Conversation ends. The Reply Plan of the next reply is now shown "the Curiosity Zeph asked in its last reply" and says how they took it (`curiosity_taken`: engaged / brushed off / asked to drop); code saves it on that Curiosity straight away. The Conversation-end keeping step still judges it again. With the fewest replies between Curiosities at least 1, the reply right after one can't ask another, so reading it there is in time. The Understanding stays free of Curiosities. `reply_plan_prompt` is reloaded from the seed by migration (as 0080 did, a day ago).
- **Pure rules in `core/curiosities.py`**, tested with plain values: brush-offs in a row (newest first, stopping at an engaged answer, unknown skipped); the replies needed (doubled while backing off); whether a Curiosity may be offered now; whether test the water still allows one. They run in `CuriosityRaiser.due`, before the Reply Plan call; test the water depends on the picked Need, so it runs in `offered_under`, like never.
- **Pace counts replies across Conversations** (Reply Plans since the newest Curiosity was raised): the live limit is 1 Curiosity per Conversation, so spacing inside one Conversation would do nothing.
- **Follow-ups (Get curious)**: code knows them as Moves that ask a question (`asks_a_question`), not by name. Once this Conversation's Reply Plans made the cap of them, none is offered. They never use the Curiosity budget.
- **Asked to drop stays dropped**: the keeping step is always shown every Curiosity the User asked to drop, not only the last 10 raised.
- **Settings** (seeded, editable with hints, so Variants can override them): `curiosity_replies_between` 3, `follow_ups_per_conversation` 3, `curiosity_brush_offs_to_back_off` 2, `curiosity_back_off_days` 3.
- **Needs**: new choice `test_the_water`; migration 0081 moves Just chatting to it (by name) and the seed starts it there.
- **Dashboard**: "Test the water" in the Needs select; four field rows in the Settings page's Curiosities group. No new parts, no reference edits.

Decisions made while building (24 Nov 2026):

- **Test the water is one per Conversation.** Read strictly from "at most one Curiosity is offered as a light opener": a Need that tests the water asks at most one Curiosity in a Conversation, however the User took it, and the reply is told to ask it "lightly, in passing, as something they can let go". (The first build let more through after an engaged answer; the spec review flagged it.)
- **Reactions are read by the next Reply Plan.** It is shown "a Curiosity an earlier reply in this Conversation was meant to ask" whose reaction isn't known, and fills `curiosity_taken`, null if Zeph's messages never really asked it. Code saves it once the reply is sent. The Conversation-end step still judges it again. The Understanding stays free of Curiosities.
- **Pace counts Reply Plans across Conversations** made after the newest raised Curiosity's `raised_at`. Reply Plans deleted by Message Retention no longer count, which only makes it stricter.
- **The doubled spacing runs from the last brush-off's `raised_at`**, not from when it was judged.
- **Follow-ups are Moves with `asks_a_question`** (only Get curious today), not found by name.
- **The Eval environment now copies `asks_a_question`** with its Moves (`adapters/evals/environment.py`). Without it the follow-up cap, and issue 01's one-question rules, did nothing in Eval Runs. Found by the Variant test.
- **Prompt reloaded.** Migration 0081 drops the stored `reply_plan_prompt` so it reloads from the seed, as 0080 did a day earlier. Any Admin edit to it has to be made again.
- **Design files.** Nothing in `web/design/reference/` changed. The Needs and Settings pages have no reference file of their own. The change is a new option in an existing select and four ordinary field rows with hints, so the pixel test has no page to check. Both pages were compared by eye at 1280 and 390, as the README says for pages built from a template.
- **Left as limits (in the message-pipeline guide):**
  - Curiosity Check-ins keep their own weekly limit and ignore pace and backing off.
  - The Reply sometimes leaves out a Curiosity the Reply Plan picked, and it is still marked raised. This was seen 3 times in the live runs; it is issue 01's path, not changed here.
  - Topics asked to drop are shown only to the keeping step, not to the Reply Plan's Get curious questions.
  - Only one of the four settings has a Variant test; the other three use the same generic path.

Evidence (24 Nov 2026, worktree stack on ports 3010/8010):
- The chat checks ran the real app (the Eval `InProcessCompanion`) on the worktree database, with real DeepSeek calls. Only the chat channel was swapped (it records texts), along with the timer and a clock that can be moved.
- Five waiting Curiosities were inserted with SQL for a made-up User. The harness read each Reply Plan's input and the database.
- Settings changed with SQL for the runs: Curiosities per Conversation 5, follow-up cap 1.

- **Test the water; Just chatting starts on it.**
  - Fresh database: the migration went to 0081 and `needs` has Just chatting as `test_the_water`.
  - Migration on data: with Just chatting set back to only if it fits, the database was taken to 0080 and forward again. Before, at 0080 and after: 1 User, 5 Curiosities, 17 Reply Plans, 40 messages, 4 reactions. Just chatting became `test_the_water` and the stored prompt was dropped; it reloaded on the next start with the new text.
  - Browser, `/admin/needs`: each Curiosities select offers Ask by default, Test the water, Only if it fits, Never, and Just chatting shows Test the water. Advice was set to Test the water and saved; it was still so after a reload. Checked at 1280 and 390 with no page errors.
  - Tests: `test_an_admin_can_set_a_need_to_test_the_water_and_the_reply_plan_is_told`, `test_each_starting_need_says_how_curiosities_are_treated`, `test_the_migration_moves_just_chatting_to_test_the_water`, `NeedsManager.test.tsx`, `curiosity-treatment.test.ts`.
- **At most one light opener; none after it.**
  - Run 1, Just chatting: A1 "heyy just got back from the gym" picked "Did you end up signing up for the 10k?".
  - A2 "lol ya. anyway what should i eat for dinner" read it as `brushed_off`, and the database saved the reaction straight away.
  - At A5 the Reply Plan was again shown 4 due Curiosities, but the Model Call Log shows "Curiosities offered 0": test the water held it back.
  - Tests: `test_under_test_the_water_the_opener_is_asked_lightly`, `..._none_is_asked_once_they_let_the_opener_pass`, `..._none_more_is_asked_even_after_an_engaged_opener`.
- **Replies between Curiosities.**
  - Run 1, pace 3: after A1 raised one, A2, A3 and A4 were shown "None." and A5 was offered 4.
  - Run 2, pace 2: M1 raised, M3 was shown "None.", M4 was offered and asked "Did you ever finish that Murakami book?".
  - Tests: `test_no_curiosity_is_offered_until_the_set_number_of_replies_has_passed`, `test_the_replies_between_curiosities_count_across_conversations`, `test_curiosity_pace.py`.
- **Follow-ups and their cap.**
  - Run 1, cap 1: A2 made Get curious, and A3 to B6 had no "- Get curious:" in their Moves.
  - The next Conversation offered it again (C1). C2 led with Get curious and C3 had none.
  - Throughout, the Curiosity count only rose with Curiosities raised ("raised 1 of at most 5"), never with Get curious replies.
  - Tests: `test_follow_ups_stop_at_their_cap_and_use_none_of_the_curiosity_limit`, `test_follow_up_cap.py`.
- **Backing off.**
  - Run 2: M1 asked "Did the Grab thing come through in the end?" and M2 "meh. anyway…" was read `brushed_off`. M4 asked about the Murakami book and M5 "nah. anyway the food is here bye" was read `brushed_off`. M6 was shown "None." for the rest of that Conversation.
  - Ten hours later, in the next Conversation, C1 and C2 were shown "None." with 2 and 3 replies since the last Curiosity. Normal spacing (2) would have allowed one; the doubled spacing (4) didn't. C3 was offered at 4.
  - Tests: `test_after_brush_offs_in_a_row_none_is_offered_for_the_rest_of_the_conversation`, `test_after_backing_off_the_spacing_is_doubled_in_the_next_conversation`, `test_the_doubled_spacing_ends_after_the_set_days`.
- **One engaged answer.**
  - Run 3, same User, still backing off: D1 was shown "None." (3 replies, against 4). D2 was offered and asked "How did the dentist go, by the way?".
  - D3 "oh the dentist was fine actually! no cavities…" was read `engaged` and saved. D4 was shown "None." (1 reply). D5 was offered at 2 replies, the normal spacing again.
  - Test: `test_one_engaged_answer_returns_the_spacing_to_normal`.
- **Platform Settings with hints, overridable in a Variant.**
  - Browser, `/admin/settings`: the Curiosities group shows "Fewest replies between Curiosities" (replies), "Most follow-up questions per Conversation" (per chat), "Brush-offs before backing off" (in a row) and "Days of doubled spacing" (days), each with its hint, at 1280 and 390.
  - 3 was changed to 4 and saved; it read 4 after a reload, then it was set back.
  - Browser, `/admin/evals/new`: all four are among the Variant override choices.
  - No real Eval Run was started, to spend nothing on it.
  - Tests: `test_a_variant_can_override_the_follow_up_cap` (Variant B with the cap at 0 has no Get curious; red before the Eval environment fix), `test_every_editable_setting_comes_with_a_short_hint`, `PlatformSettingsForm.test.tsx`.
- **Pure rules**: `core/curiosity_pace.py` (`brush_offs_in_a_row`, `backed_off_by`, `replies_needed`, `may_offer_curiosity`) and `follow_ups_made` / `moves_within_follow_up_cap` in `core/reply_plan.py`, tested in `tests/test_curiosity_pace.py` and `tests/test_follow_up_cap.py` with plain values.
- **Checks (last run on 55c03b8)**:
  - ruff, ruff format and mypy clean (226 files); pytest 1769 passed.
  - `pnpm lint`, `pnpm format:check` and `pnpm typecheck` clean; `pnpm test` 136 files, 927 tests passed.
  - The tests written after the code were checked by turning off the pace, test-the-water and cap rules for a moment: 6 of the new end-to-end tests went red.
- **Review.** Standards and spec reviews were run. Fixed: test the water is one per Conversation; the reaction is saved once the reply is sent, so a dropped try saves none; the wording after a fallback Reply Plan; the stale `CuriosityTreatment` TSDoc; a name. A live run then showed a false brush-off on a Curiosity the reply never asked, fixed in 55c03b8. The fix's null case wasn't seen live: in runs 2 and 3 every pick that had a next message was asked.
- **Cost.** About 50 messages across three runs, roughly 5 DeepSeek-flash calls each.

Eval Runs (24 Nov 2026, after the merge, on a fresh worktree off main; the owner asked for them; estimate S$0.23):

- **Whole Understanding Eval, live settings**: 22 of 30 passed, S$0.21.
  - Passed: `curiosity-raised-once`, under Just chatting's new test the water. The opener asked "How'd the board thing go on Thursday?" and nothing was asked on the next message.
  - The 8 failures don't touch this work's rules:
    - asked why (`strong-mood-unknown-cause`)
    - the Need (`knowledge-for-a-reflective-question`)
    - a judge rule on a vent (`no-knowledge-for-a-vent`)
    - a woven-in Check-in (`check-in-not-now-while-asking-for-help`)
    - lead Moves (`internal-testing-finish-line`, `small-talk-makes-no-move`)
    - the next Move (`next-move-held-then-made`)
    - `guess-checked-gently`
  - `guess-checked-gently` flips between tries. When its Curiosity is asked, issue 01's one-question rule drops Get curious, which the case expects to lead.
  - No run of these cases from before this work was at hand to compare against.
- **Variant run, follow-up cap**: S$0.02. Variant A ran live settings; Variant B overrode `follow_ups_per_conversation` to 0.
  - `passing-update-gets-curious`: A led with Get curious and passed. B led with Suggest and failed, as it should.
  - `guess-checked-gently`: A led with Get curious. B made no Move.
  - So a Variant override of the new setting changes a real run, and the live settings were untouched.

## Completion

- Completed: 2026-11-24
- Commit: 0280619 (merge "Merge pattern-02-test-the-water: test the water, pace between Curiosities and backing off after brush-offs"; work in c2351af "Test the water, pace between Curiosities and backing off after brush-offs", c9a16cc "Review fixes: test the water asks one opener per Conversation", 55c03b8 "Ask how a Curiosity was taken only if it was really asked; docs", 5eaaf58 "Archive pattern-pipeline issue 02: test the water, pace and backing off, verified", 6a75a44 "CONTEXT: say what asking to drop a Curiosity means, not how")
