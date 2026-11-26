# 08 — Zeph shares a ready Pattern with the User's quotes and a Prediction

Status: completed
Track: A
Blocked by: 07

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 33, 34, 35, 36, 38, 39, 40, 41, 42, 43, 44). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Behind a new Feature, Pattern sharing (works only when Pattern exploring does). The Reply Plan is offered only ready Patterns to share and picks the moment; other Patterns in mind are marked not to be said, though the Read may think with them. A shared Pattern is Zeph's view, never fact, in three parts: the Pattern in warm words from its Pattern Type's approved wording fitted to the User's own people, two or three of their quotes from different Life Threads, and one Prediction. Zeph asks what would prove it wrong. A small check after the Reply says whether it was shared; only then does it move to shared and count toward the Admin-set weekly limit (start 1). A ready Pattern with no good moment within an Admin-set time (start 5 days) goes out as a Check-in.

Reactions: the model reads agreed, pushed back or brushed off; code counts agreement as a weak sign for, and makes a rejected Pattern contested: never offered again unless the User raises it. A contested Pattern keeps gathering evidence only while the User's own switch allows (on to start, on the Dashboard and in chat).

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [x] With Pattern sharing on, a ready Pattern is offered to the Reply Plan; a Pattern that isn't ready is marked not to be said and never reaches the Reply as a Pattern
- [x] A shared Pattern's reply has the Pattern in the approved wording, two or three quotes from different Life Threads, one Prediction, and asks what would prove it wrong
- [x] It is worded as Zeph's view, with no clinical words
- [x] The after-reply check decides whether it was shared; if not, it stays ready and doesn't count toward the limit
- [x] No more than the Admin-set number of new Patterns are shared in a week
- [x] It is never shared while the User is struggling
- [x] A ready Pattern not shared within the Admin-set time is sent as a Check-in
- [x] Agreement adds a weak sign for and never confirms by itself
- [x] Rejection makes the Pattern contested and it is never offered again unless the User raises it
- [x] The User's switch for silent gathering on contested Patterns works on the Dashboard and in chat; off stops new Observations for them
- [x] The Model Call Log's Reply Plan shape records whether a Pattern was offered and shared
- [x] With Pattern sharing off, nothing is shared and ready Patterns wait
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `07-ready-gate.md`

## Comments

- 25 Nov 2026 (from issue 07): the ready gate is built (`core/ready_gate.py`). For sharing: (1) a ready Pattern is judged again only at a Conversation end or when Observations are deleted, so look again before sharing (`ReadyKeeper.look` does it with no model call), and check struggling there, which the gate doesn't; (2) "not rejected" has no source yet: make a rejected Pattern contested and the gate will never look at it; (3) the narrowing is on the Pattern (`CatalogPattern.narrowings`: tag, holds with, not with) for the wording; (4) pick quotes from Observations that are not `excluded` and not on a ruled-out topic the User didn't raise.

### 25 Nov 2026: plan (branch `pattern-08-sharing-a-ready-pattern`)

Started once issue 07 was merged (f480706). Slices, each test-first:

1. **Feature** Pattern sharing (needs Pattern exploring, off to start). Settings `patterns_shared_per_week` (1) and `pattern_share_wait_days` (5).
2. **Offer.** New `core/pattern_sharing.py`. Before each reply, when sharing works, they aren't struggling and the weekly limit isn't reached: look again (`ReadyKeeper.look`, no model call), then offer the Reply Plan the oldest ready Pattern with its approved wording, narrowing, two or three quotes from different Life Threads (pure `pick_quotes`) and the Prediction wording. The form gains `share_pattern`.
3. **Reply and check.** The reply gets the three parts at level 3. A small check after the reply (fixed prompt, Check-in model, like the brought-up check) says whether it was shared and reads the Prediction as worded. Only then: ready → shared (logged), share and Prediction saved. The Reply Plan shape records offered and shared.
4. **Check-in.** A new Check-in Kind with fixed behaviour `shares_pattern`, offered only when a ready Pattern has waited the Admin-set days; the same check after it is sent.
5. **Reactions.** Read by the tagging step at Conversation end (it is shown the Patterns told to them): agreed, pushed back, brushed off. Code: agreed adds a weak sign for; pushed back makes it contested (logged) with a weak sign against. Kept as rows (`pattern_reactions`), so agreeing adds up.
6. **Contested.** Never ready again (the gate skips it). The Reply Plan sees contested ones marked "only if they raise it". A User switch `contested_gathering` (on to start) on Account & privacy and as a chat settings tool; off drops new Observations of contested Pattern Types at tagging.
7. Dashboard: the switch (reference + pixel test), Features page, Platform settings, Check-in Kinds, trace page. Docs.

### 25 Nov 2026: built

What was built (details in `docs/pattern-pipeline/README.md`, "sharing a ready Pattern"):

- **Feature** Pattern sharing, off to start, needs Pattern exploring. A Feature now also counts as off when the one it needs is off because of the one before it.
- **Offer** (`core/pattern_sharing.py`): before each reply code looks again at the ready Patterns (no model call) and offers the Reply Plan the one ready the longest, with its approved wording, where it shows and two or three quotes, one per situation (`pick_quotes`). `share_pattern` picks the moment.
- **Reply**: three parts at level 3, as Zeph's view, then "what would prove it wrong". A reply that shares asks nothing else.
- **Check**: after the reply is sent, one small call (fixed prompt, Check-in model) says whether it was told and reads the Prediction. Only then ready → shared, logged, Prediction kept.
- **Check-in**: a new Check-in Kind with fixed behaviour, "Something I've noticed", offered alone once a ready Pattern has waited `pattern_share_wait_days`.
- **Reactions**: read by the tagging step at Conversation end; kept in `pattern_reactions`; pushing back makes the Pattern contested.
- **Contested**: never offered; the Reply Plan sees it marked "never bring one up" and may talk about it only when they raise it. The User's switch `contested_gathering_enabled` on Account & privacy and in chat.
- **Settings**: `patterns_shared_per_week` 1, `pattern_share_wait_days` 5. Migration 0100.

Decisions made while building (owner may want to look):

- **Reactions are read when the Conversation ends**, by the tagging step, not on each reply. A rejection takes effect then.
- **The check after the reply uses a fixed prompt on the Check-in model**, like the Woven-in Check-in's check. It runs after the reply is sent, so the reply isn't slowed.
- **A Check-in shares a Pattern through its own Kind**, like the Curiosity one; while a Pattern waits, only that Kind is offered.
- **The weekly limit is counted from the log of moves**, so deleting a Pattern doesn't free a slot.
- **The switch is one per User**, shown only while Pattern sharing works for them. With it off, agreement with a contested Pattern isn't kept either.
- **A reply that shares a Pattern asks no Curiosity, doesn't ask why and makes no asking Move.**
- **A line was added to `reply_plan_prompt`**: a Read is about this situation and is never called a pattern.
- The words on the new Account card and the new Kind are drafts for the owner.

Limits and findings are in `20-findings-for-the-owner.md` (08). The one to read first: **asked outright for a pattern, Zeph's own Read says one that code never offered** (see the first criterion below).

Evidence (25 Nov 2026, worktree stack on 3010/8010, real model (`deepseek-v4.1-flash`), the running backend's own scheduler; a made-up User only. Chat went in through `/telegram/webhook`; the backend ran with the chat channel that logs instead of sending (a Compose override, since a made-up chat can't receive Telegram sends), so replies were read from `conversation_messages`. The User's evidence (four Observations in three Life Threads, two past Conversations) was put in with SQL; everything after that was done by the running app. Conversation ends and due Check-ins were brought on by moving timestamps back. Dashboard checks in a real browser (Playwright) as a signed-in Admin who was also that User. The checks were made before the last rebase onto main (openrouter issue 11); after it the stack was rebuilt and the sharing path run once more.)

- **Ready is offered; not ready is never offered.** Not ready: with sharing on and the Pattern suspected, the Reply Plan's input had no "A Pattern you may tell them now" and the shape said `pattern_to_share_offered: false`; the Agenda listed it as "only suspicions: never name them". After the next Conversation end the real gate made it ready (`suspected → ready`, real other-side call). Ready: "quick one, I'm rushing out the door…" → input held the offer with the approved wording, "It shows with colleague, family, friend; not with partner" and three quotes (Jun, Mei, Dana); the plan left it (`share_pattern: false`) and it stayed ready. **Caveat, for the owner:** asked outright "what patterns do you see in me? tell me one" while it was only suspected, the reply said "the yes comes out before you've checked whether you want to give it", with their people as examples. That came from the Reply Plan's own Read, not from the Pattern: nothing was offered, no approved wording, quote list or Prediction reached the reply, and nothing was recorded. Code holds the criterion; the model's Read can still say much the same when asked. Logged as the first finding for issue 08 in issue 20. Tests: `test_a_ready_pattern_is_offered_to_the_reply_plan_with_quotes_from_many_threads`, `test_a_pattern_that_is_not_ready_is_never_offered_and_never_reaches_the_reply`.
- **Three parts.** "home now, feet up… is there anything you've noticed about me that I might not see?" → the plan chose to share and the reply said: the Pattern ("you keep disagreements small… Keeping things smooth is a way of protecting the closeness"), their words ("stewed about it all evening", "fuming on the train home", went along with Jun "because you didn't want to make it weird"), where it doesn't show ("You don't do it with your partner"), one Prediction ("Next time Jun asks for something you'd rather not do, notice whether you say yes before you've decided") and "What would prove me wrong?". Test: `test_the_reply_is_told_the_three_parts_as_zephs_view_with_no_clinical_words`.
- **Zeph's view, no clinical words.** Same reply: "Here's what I'd watch for, and I could well be wrong"; the Check-in: "I could be reading it wrong". No clinical word or Pattern Type name in either. A catalog test already checks the approved wording holds no clinical terms.
- **The check decides.** After that reply the Model Call Log had a `pattern_shared_check` call answering `{"shared": true, "prediction": "Next time Jun asks…"}`; the Pattern moved `ready → shared (shared_in_chat)` with `shared_at`, and the Prediction was kept. Not shared: the real check, run in the backend container on the real services, on the potluck reply answered not shared; the Pattern stayed ready with no Prediction. Tests: `test_only_when_the_check_says_so_is_it_shared_with_its_prediction_and_logged`, `test_a_failed_or_unreadable_check_leaves_it_ready_and_the_reply_still_goes`.
- **Weekly limit.** With one share in the log and the Pattern put back to ready by hand, an open invitation ("tell me something else you've noticed about me?") got no offer in the Reply Plan's input. In the browser, Platform settings showed "New Patterns shared a week" (1, with its hint) and "Days a ready Pattern waits for a moment in chat" at 1280 and 390; set to 2, saved, kept after reload; the next message was offered it again. Tests: `test_no_more_than_the_admin_set_number_are_shared_in_a_week`, `test_the_two_sharing_numbers_are_settings_with_hints_and_eval_overrides`.
- **Never while struggling.** "the project I spent 3 months on is cancelled. I feel sick, I can't think straight" → Understanding shape `struggling: true`; no offer in the input; the Pattern stayed ready. Tests: `test_it_is_never_offered_while_the_user_is_struggling`, `test_a_check_in_never_shares_one_after_a_message_read_as_struggling`.
- **Check-in after the wait.** Ready for 1 day with a Check-in due: the Check-in model was not offered the Kind and sent "A follow-up". Ready for 6 days: it was offered only "Something I've noticed" and sent the Pattern with three quotes, "I could be reading it wrong", a Prediction and "What would show me I've got this wrong?"; the check ran and the move was logged `ready → shared (shared_in_check_in)`. Browser: Check-in Kinds shows the Kind with "Shares a Pattern" (1280, 390); the User's Check-ins page lists it. Tests: `test_a_ready_pattern_not_shared_within_the_admin_set_days_goes_out_as_a_check_in`, `test_users_see_the_kind_that_shares_a_pattern_only_while_sharing_works_for_them`.
- **Agreement is a weak sign, never confirms.** "huh. yeah, that's actually spot on. I did exactly that with Mei again last night" → at Conversation end the tagging call was shown "Patterns Zeph has told them: [1] You seem to protect closeness…" and a reaction `agreed` was kept; the Pattern stayed shared. Tests: `test_agreeing_adds_a_weak_sign_for_and_never_confirms_by_itself`, `test_agreeing_adds_a_weak_sign_for_that_fades_and_adds_up` (30 points, 60 for two, 15 after a half-life). Limit: nothing reads a shared Pattern's score yet (issue 09).
- **Rejection makes it contested, never offered again.** "I disagree with what you said about me keeping disagreements small… you've got that one wrong" → reaction `pushed_back`; `shared → contested (user_reacted)`. With the limit at 7, "anything you've noticed about me you want to share?" got no offer; the input held "Patterns you told them that they disagreed with. Never bring one up…"; the reply spoke of something else. When they raised it themselves ("so, about me keeping disagreements small… say a bit more"), the saved plan named it as raised, the reply was told "have now brought it up themselves" and talked about it; it stayed contested. Tests: `test_rejecting_makes_it_contested_and_it_is_never_offered_again`, `test_a_contested_pattern_is_talked_about_only_when_the_user_raises_it`.
- **The User's switch.** Browser, Account & privacy at 1280 and 390: the card "Keep noticing after I disagree" with its two paragraphs; switched off there. Then the Priya story ("I hate orange but I said sure, looks great") → the real tagger wrote one Observation for the Pattern Type and code dropped it (`tagged 1, dropped 1`; Observations stayed at 5). In chat: "you can keep quietly noting it when it comes up" → the reply called `turn_noting_on_disagreed_patterns_on_or_off`, the setting was on and the card showed "Changed in chat · 25 Nov". Then the Tom story was kept (6 Observations). Pixel test (a copy of `compare.cjs` that blocks Clerk's probe requests, as before): `Account` PASS 0.17%, `M-Account` PASS 0.38%, `CheckIns` and `M-CheckIns` PASS. Tests: `test_the_users_switch_stops_new_observations_for_a_contested_pattern`, `test_the_switch_is_changed_in_chat_only_while_pattern_sharing_works`.
- **The Reply Plan shape.** Browser, the trace of the sharing reply at 1280 and 390: "Pattern to share: Shared" and a "Pattern shared check" step. In the log: offered, not picked (potluck); picked and shared. Test: `test_the_reply_plan_shape_records_whether_a_pattern_was_offered_and_shared`.
- **Sharing off.** With the Feature off for the User and the Pattern ready, "slow afternoon… got time to think" got no offer and the Pattern stayed ready; switched on, it was offered. Browser: Features lists "Pattern sharing" with its line (1280, 390). Tests: `test_with_pattern_sharing_off_nothing_is_shared_and_a_ready_pattern_waits`, `test_pattern_sharing_is_off_to_start_and_works_only_while_exploring_works`.
- **Checks.** On the final code, rebased onto main: ruff clean, ruff format clean, mypy clean (263 files), pytest 2364 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 140 files, 980 tests passed. After the rebase the stack was rebuilt and one more reply shared the Pattern end to end (offered, picked, shared; `ready → shared (shared_in_chat)`; Prediction kept; no error in the backend log). Migration: `test_the_migration_keeps_user_data_and_reloads_the_three_prompts`.
- **Review.** Standards and spec reviews run. Fixed: with the switch off a past Conversation tagged again could still add Observations; a push-back left unsettled by a failed run is settled at the next Conversation end; one helper for sign strengths; names. Left as is and logged in issue 20: the check runs after the reply is sent; a share can have no Prediction; nothing reads a shared Pattern's score with reactions yet.
- **Not checked in the running app:** the pixel test for `AdminModelCallTrace` and `AdminCheckInKinds` fails on page height only, as it did before this work; the Users panel's counts for shared and contested were not opened (not a criterion). No Eval was run (Evals cost money): the Tagging Eval hasn't seen the new `reactions` part of the prompt.

## Completion

- Completed: 2026-11-25
- Commit: d92dd80 (merge of `pattern-08-sharing-a-ready-pattern` into main; work commits 189969b, 293bb75, 7d32884, 40c06e9, 8858909, eda5a1e)
