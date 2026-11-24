# 01 — Each Need says how Curiosities are treated, and a picked Curiosity is part of the plan

Status: completed
Track: A
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 1, 11, 76, 81). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Zeph is passive because a Curiosity can be dropped twice (the Reply Plan is told to leave it out unless the moment is right, then the Reply gets it as an optional extra) and a model writes it with nothing to aim at (ADR-0026). This slice changes its standing. It needs no Pattern Catalog.

Each Need gets an Admin-set field for how Curiosities are treated while it is picked: ask by default, only if it fits, or never (test the water comes in issue 02). Under ask by default the Reply Plan must bring up a due Curiosity or give its reason for not doing so. A Curiosity the Reply Plan picks reaches the Reply at the Reply Plan's level of the priority order, not among the optional extras. Every Curiosity records its aim (a commitment to follow up, a look-back, a guess to check, an unmade next Move; Exploration and Prediction aims come later), and the keeping step makes none without one. The Model Call Log's Reply Plan shape records how many Curiosities were offered and whether one was asked.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [x] On the Needs admin page each Need has a Curiosities field with a hint, saved and applied from the next reply; Being heard starts as never, the fallback Need as only if it fits, the rest as agreed with the owner in the issue
- [x] With a Need set to ask by default and a Curiosity due, the Reply Plan is told to ask one or say why not, and its reason is saved when it doesn't
- [x] With a Need set to never, no Curiosity is offered to the Reply Plan
- [x] A picked Curiosity appears in the Reply's instructions at the Reply Plan's level, not under optional extras, and the reply asks it
- [x] The existing rules still hold: one question per reply, the per-Conversation limit, never while struggling
- [x] Every new Curiosity has an aim; the keeping step saves none without one; existing waiting Curiosities are given an aim by migration and none are lost
- [x] The Model Call Log shows Curiosities offered and asked for each reply
- [x] A Variant can override a Need's Curiosities field in an Eval Run
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

None - can start immediately

## Comments

Decisions made while building (24 Nov 2026, branch `pattern-01-needs-curiosities`):

- **Starting values, agreed with the owner.** Be heard and Get it done: never. Think it through and Accountability: ask by default. Advice, Just chatting, the fallback Need (Ask more) and any Need an Admin added or renamed: only if it fits. Just chatting moves to test the water in issue 02. Migration 0080 sets them by name, ignoring case.
- **"Never" is held by code, not by hiding.** The Reply Plan picks the Need and the Curiosity in one call, so it still sees the due Curiosities, with one line per Need saying how that Need treats them ("Be heard: never: ask none"). Code drops any pick under a Need set to never and the Model Call Log records 0 offered. Hiding them would need a second model call per reply. Accepted by the owner. A Need set to never stops Curiosities, not questions the reply comes up with itself (e.g. the Get curious Move).
- **Aims.** `commitment`, `look_back`, `guess`, `next_move`. A follow-up on an event that was coming up ("how did the presentation go?") is a look-back. A Curiosity that holds a guess aims at checking it, whatever the model wrote. Migration 0080 gives every saved Curiosity an aim: `guess` if it holds a guess, `look_back` otherwise (old rows can't be told apart further).
- **Prompts reloaded.** Migration 0080 reloads `reply_plan_prompt` and `curiosity_keeping_prompt` from the seed, even where an Admin edited them, as 0073 and 0078 did: an old keeping prompt gives no aim, so nothing would be saved. Any Admin edit to these two prompts in production has to be made again.
- **Rules now in code.** At most one Curiosity per reply (a picked one is asked, so two would be two questions). None while the Understanding finds the User struggling (before, only the prompt said so). None in a reply that asks why they feel as they do; under ask by default the saved reason says so.
- **The reason** is the Reply Plan's `no_curiosity_why`, saved in the form as `curiosity_not_asked_why`; "No reason given." when the model gave none, "The Reply Plan couldn't be made." on a fallback Reply Plan. It is not shown on the Dashboard.
- **Variants.** A Need override may carry `curiosities`; one without it (saved before this) keeps the live Need's choice.
- **Design files.** `web/design/README.md` says agents never edit `reference/`. Nothing there was changed: the Needs page has no reference of its own (card-list template) and the new field is an existing field row with the existing select. The trace page shows "Curiosities offered" and "Curiosity asked" only on traces that have them, so its fixture page is as drawn. Accepted by the owner.
- **Seen on the way, not changed:** hints on the Needs page still say "the Understanding picks" the Need (it is the Reply Plan); the Eval environment's copy of Moves leaves out `asks_a_question`.

Evidence (24 Nov 2026, worktree stack on ports 3010/8010; the real backend with only the chat channel swapped for one that logs texts; real DeepSeek calls; a signed-in Admin test user linked to a made-up Telegram chat):

- **Needs page field.** Browser, `/admin/needs`: every card has a Curiosities select with the hint "Whether the Reply Plan asks a due Curiosity while this Need is picked. Ask by default means it asks one or says why not." As loaded: Be heard never, Think it through ask by default, Advice only if it fits, Accountability ask by default, Get it done never, Ask more only if it fits, Just chatting only if it fits. Advice set to Ask by default, Saved, still so after reload; looked at 1280 and 390, no page errors. The next message asking for advice was told "Advice: ask by default: ask one in this reply, or say why not". Tests: `test_each_starting_need_says_how_curiosities_are_treated`, `test_an_admin_saves_a_needs_curiosities_field_and_the_next_reply_plan_sees_it`, `NeedsManager.test.tsx`.
- **Ask by default: ask one or say why.** "what do you think: should I do the test in Mei's car or the instructor's car?" picked Advice; the Reply Plan's input listed 4 due Curiosities with aims and the line per Need; it picked one. With Just chatting set to Ask by default on the Dashboard, "ok gtg, boss just walked in, ttyl!" asked none and saved `curiosity_not_asked_why`: "They're rushing out the door mid-sentence; a question would hold them when they've said they have to go." Tests: `test_under_ask_by_default_the_reason_for_not_asking_is_saved`, `test_the_reply_plan_prompt_says_to_ask_one_or_say_why_not`.
- **Never.** With Just chatting set to Never on the Dashboard and 3 Curiosities due, "hey just had lunch, nasi lemak again lol" picked Just chatting, asked none, shape `curiosities_offered: 0, curiosity_asked: false`. Test: `test_a_need_set_to_never_asks_no_curiosity_and_logs_none_offered`.
- **Part of the plan, and asked.** In the advice reply's instructions the Curiosity sits under "## 3." after the Threads, before "## 4. What you remember", as "Ask them this in this reply, the way a friend would. It is part of the plan, not an extra to leave out"; no "## 6." section. Zeph sent: "Instructor's car. It's the one you've practiced in…" then "Did you get through to Mei about borrowing her car though?". The Curiosity was marked raised, and "engaged" when the Conversation ended. Test: `test_a_picked_curiosity_is_part_of_the_plan_not_an_optional_extra`.
- **Existing rules.** One question: that reply had one question, lead Move Suggest. Limit: the next text in the same Conversation saw "raised 1 of at most 1 in this Conversation: None." and logged 0 offered. Struggling: "boss tore into me… shaking and crying" was read as struggling; the Reply Plan saw "None.", picked Be heard and asked nothing. Tests: `test_a_reply_asks_at_most_one_curiosity`, `test_no_curiosity_is_offered_while_they_are_struggling`, `test_a_reply_that_asks_why_asks_no_curiosity_too`, and the existing `test_curiosities.py` and `test_moves_that_ask_a_question.py`.
- **Aims.** The first Conversation's end (time moved back in the database) saved four Curiosities from the real keeping call: two `commitment`, one `next_move`, one `look_back`; the next one saved a `guess`. Migration: on those 5 rows the database was taken back to the revision before and forward again: 5 rows before, 5 after, the guess `guess` and the rest `look_back`, Needs back on the agreed values, both prompts dropped and reloaded on start. After the rebase a fresh database migrated to 0080 with the same Need values and both new prompts. Tests: `test_the_keeping_step_saves_no_curiosity_without_an_aim`, `test_a_new_curiosity_is_saved_with_its_aim`, `test_the_migration_gives_saved_curiosities_an_aim_and_needs_their_treatment`.
- **Model Call Log.** Browser, the advice reply's trace: Reply Plan shows "Curiosities offered 4" and "Curiosity asked Yes". Tests: `test_a_plain_users_understanding_and_reply_plan_show_shapes_and_never_words`, `model-calls.test.ts`.
- **Variant override.** Browser, New Eval Run: Understanding, single case `curiosity-raised-once`, Variant B with "Need: Just chatting" and its Curiosities select (starting on the live choice) set to Never. Estimate shown: S$0.0069 per Variant; run with the owner's OK. Result: Variant A (live, ask by default) was told "Just chatting: ask by default", 1 offered, asked; Variant B was told "Just chatting: never: ask none", 0 offered, none brought up, so its "curiosity raised" check failed as it should. The live Need was unchanged. In B the reply still asked about the presentation from its memory of the week, the limit noted above. Tests: `test_a_variant_can_override_how_a_need_treats_curiosities`, `test_a_need_override_with_an_unknown_curiosities_choice_is_refused`.
- **Checks, after the rebase on main.** ruff, ruff format and mypy clean (230 files); pytest 1742 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean; `pnpm test` 136 files, 926 tests passed.
- **Pixel test.** `AdminModelCallTrace` with a git-ignored copy of `compare.cjs` that blocks Clerk's `protect.clerk.com` probes: 0.02% of pixels differ, but FAIL on page height (1357 vs 2274). It fails the same way on `main`'s Dashboard code (issue 10's evidence notes the same). The Needs page has no reference file.
- **Review.** Standards and spec reviews run. Fixed: an odd `curiosities` value in an override or an odd `aim` (a list, a number) is refused, not an error; the override reader split into a check and a reader; a fallback Reply Plan gives its own reason; a test for the treatment helpers. Left: a Variant that overrides either prompt with old text gets no aims or reasons in that run; the reason is not shown on the Dashboard.

## Completion

- Completed: 2026-11-24
- Commit: <filled in after the merge>
