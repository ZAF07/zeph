# 18 — The Patterns tab shows Patterns being tested, confirmed, disagreed with and that didn't hold up

Status: completed
Track: B
Blocked by: 08

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 45, 46, 47, 48, 49, 50). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Users see a Pattern only once the Companion has told them about it. The Memories page's Patterns tab shows: shared ones as being tested, with their quotes, the Prediction and how it went; confirmed ones with their evidence and Prediction record; contested ones as "you disagreed", where the User can delete it or turn silent gathering off; and closed ones only if they were ever shared, as "didn't hold up". Never a score or percentage: words and evidence only. Noticed, suspected, ready and unmatched Patterns never show.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [x] The tab shows shared, confirmed, contested and once-shared closed Patterns, each under its own wording
- [x] Each shows its quotes grouped by part of life, its Prediction and how it went
- [x] No score, percentage or state name from the code is shown
- [x] Noticed, suspected, ready, never-shared closed and unmatched Patterns are not returned by the API at all
- [x] A User can delete any shown Pattern; it is gone at once and the User Portrait is rewritten without it
- [x] The contested section has the silent gathering switch
- [x] New Copy slots hold every heading, label and empty state
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `08-sharing-a-ready-pattern.md`

## Comments

- 25 Nov 2026 (issue 24): the line "Confirmed Patterns from before this work still show" was removed. The owner had the confirmed and closed Patterns kept before the Pattern Catalog deleted, so the tab is empty until this issue fills it from Patterns of Pattern Types. The tab, `GET /api/patterns` and `DELETE /api/patterns/{id}` still read the old confirmed rows (`list_confirmed`, `delete_confirmed`); rewire them here.
- 25 Nov 2026 (from issue 08): the states shared and contested exist now, with `patterns.shared_at`, `predictions` and `pattern_reactions`. The silent gathering switch is `contested_gathering_enabled` on `/api/me` (PATCH to change), already on Account & privacy as "Keep noticing after I disagree" (`PreferenceSwitch`), shown while `pattern_sharing_works`. Which quotes a share used isn't stored: show the Pattern's Observations. Deleting a shared or contested Pattern has no API yet (`delete_confirmed` only).
- 25 Nov 2026 (from issue 09): the state confirmed is reached now, and a Pattern closed after it was shared stays closed (`patterns.shared_at` is set, so "didn't hold up" = closed with `shared_at`). Why it was confirmed or closed is `pattern_moves.reason`. How a Prediction went is `predictions.outcome` (`came_true`, `did_not`, `not_come_up`, `not_followed_up`; empty while open) with `outcome_at`; a Pattern can have several Predictions, oldest first. Deleting a confirmed Pattern of a Pattern Type still has no API, and the Portrait reads confirmed ones through `list_of_pattern_types`.
- 25 Nov 2026 (done, branch `pattern-18-patterns-tab`): built, then held until issue 09 was merged so "how it went" could show the stored outcome. After the rebase the API sends `prediction.outcome` (`PredictionResponse.outcome` is a `PredictionOutcome`), and the unused `list_confirmed` is gone.

What was built (25 Nov 2026):

- **Backend.** `told_patterns` in `core/told_patterns.py` (pure) picks the Patterns a User may see: shared, confirmed, contested, and closed only with `shared_at`, of a Pattern Type in the catalog now. `UserMemoryService.list_told_patterns` and `GET /api/patterns` return each with its state, approved wording, where it shows, when it was told, quotes grouped by Life Thread and Predictions, newest first. No score. `DELETE /api/patterns/{id}` deletes only a Pattern they were told (404 otherwise), under the User's lock, then scores again and asks for a new Portrait. Each Prediction comes with how it went (`predictions.outcome`, empty while open). The old `delete_confirmed` and `list_confirmed` are gone.
- **Dashboard.** `PatternsList` shows four headings (Being tested, Confirmed, You disagreed, Didn't hold up), each only when it has a Pattern; `PatternCard` is one Pattern. Under "You disagreed" is the same switch card as on Account & privacy.
- **Copy.** `memories.patterns.*`: intro, four headings, told on, where it shows, two labels, "Other moments", quote marks, asked on, five "how it went" wordings, delete label, empty title and message. The old `lead`, `agreed`, `based_on`, `evidence_when` and `empty_body` slots are removed; the changed texts use new keys so no migration is needed.
- **Design.** As issues 10, 13 and 08 did: the Patterns panel in `Memories--tab-patterns.html` and `M-Memories--tab-patterns.html` was redrawn from the old Patterns card's parts, the Memories group heading and the Account switch card; the empty state words in `States.html` changed; three baselines reshot (only those three changed).

Decisions made while building:

- **Deleting a Pattern deletes its quotes too**: the Observations whose first Pattern Type is its own. Otherwise the next scoring would start it again from the same words and it could be told again. An unclear quote that names it second stays (it belongs first to another Pattern). The tab's intro says so.
- **Which quotes show**: the ones that may be quoted back when sharing (`may_be_quoted`): clear evidence for it from their own life. Evidence against, unclear, "what if" answers and ones where anyone would act the same are left out. The quotes a reply really used aren't stored (issue 08).
- **Part of life** is the Life Thread's title; quotes in no Thread go last under "Other moments".
- **Where it shows** (narrowings) is on the card, in words said to the User ("people above you").
- **The switch** shows whenever they have a Pattern they disagreed with, also while Pattern sharing is off for them, since it still decides what the tagging step keeps.
- **Left from review:** the backend's state order and the tab's heading order are each written once on their side; the tab's row markup copies the old card (it is the drawn design); a told Pattern whose Pattern Type left the catalog isn't listed.

Evidence (25 Nov 2026, worktree stack on 3020/8020, a made-up run User signed in through Clerk, driven in a real browser with Playwright at 1280 and 390 wide. The Patterns, quotes and Predictions were put in by SQL, one Pattern in every state, with outcomes in the columns issue 09 added; the real path to each state and outcome was run by issues 08 and 09. Checked twice: before the rebase, and again on the final code after issue 09 was merged.)

- **Four kinds, each under its own wording.** The tab showed "Being tested" (shared), "Confirmed", "You disagreed" (contested) and "Didn't hold up" (closed with `shared_at`), in that order, each Pattern in its Pattern Type's approved wording. No sideways scroll at 390, no page errors. Tests: `test_each_pattern_zeph_told_them_shows_and_no_other_is_returned`, `PatternsList` in `Memories.test.tsx`.
- **Quotes by part of life, Prediction, how it went.** Quotes sat under their Life Thread's title, with "Other moments" last; evidence against and an unclear quote were not shown. All five wordings showed from stored outcomes: open → "Zeph hasn't asked how it went yet."; `came_true` → "How it went: it happened as Zeph thought." (both of the confirmed Pattern's); `not_come_up` → "it hasn't come up yet."; `did_not` → "it didn't happen as Zeph thought."; `not_followed_up` → "Zeph didn't get to ask how it went." Tests: `test_a_user_sees_a_pattern_zeph_told_them_with_quotes_by_thread_and_prediction`, `test_a_prediction_shows_how_it_went_once_it_is_known`, `tests/test_told_pattern_rules.py`.
- **No score, percentage or state name.** The panel's text holds none; the `/api/patterns` answer has only `id`, `state`, `pattern`, `where_it_shows`, `told_at`, `quote_groups`, `predictions`. The `state` value is used to pick the heading and is never drawn.
- **Hidden ones are not returned.** The run User also had a noticed, a suspected, a ready, a never-shared closed and an unmatched Pattern, each with a quote marked HIDDEN: `/api/patterns` returned four Patterns and no HIDDEN text.
- **Delete.** Each of the four was deleted in the browser: the card went at once; its row, its Predictions and the Observations first its own were gone from the database; a Pattern closed after sharing stayed closed through the re-scoring. Deleting the confirmed one set `user_portraits.rewrite_requested_at`, and the scheduler's next tick rewrote the Portrait with the real model: the new text says "There are no patterns they've agreed with yet". After the last delete the tab showed "No patterns yet". Test: `test_deleting_a_pattern_removes_it_with_its_own_quotes_and_rewrites_the_portrait` (a confirmed Pattern's wording is in the Portrait's input before and not after), `test_a_user_cannot_delete_a_pattern_never_told_or_another_users_pattern`, `test_with_user_memory_off_a_user_still_sees_and_deletes_patterns`.
- **Switch.** "Keep noticing after I disagree" sat under "You disagreed"; clicking it went on → off and `users.contested_gathering_enabled` became false (before the rebase also off → on).
- **Copy.** Every heading, label, wording and the empty state comes from `memories.patterns.*` slots (and the Account switch's slots); `tests/test_copy.py` keeps the design fixture equal to the seed.
- **Pixel test** (before the rebase; no Dashboard file changed after it): `Memories--tab-patterns` PASS 0.13%, `M-Memories--tab-patterns` PASS 0.29%, `Account` PASS 0.17%, `M-Account` PASS 0.38%, with a copy of `compare.cjs` that blocks Clerk's probes. `Memories--tab-summaries`, `M-Memories` and `M-Memories--tab-quotes` fail as they do on main.
- **Checks** on the final code: ruff, ruff format and mypy clean; pytest 2413 passed; `pnpm lint`, `format:check`, `typecheck` clean; Vitest 140 files, 982 tests passed. No error in the backend log during the run.
- **Review.** Standards and spec reviews run. Fixed: deleting a Pattern deleted quotes that belong first to another Pattern; a method name; when it was told worked out in two places.
- **Not checked in the running app:** a Pattern reaching confirmed or closed by real chat on this branch (issue 09 ran that); the tab with User Memory off (test only).

## Completion

- Completed: 2026-11-25
- Commit: MERGE_COMMIT (merge of `pattern-18-patterns-tab` into main)
