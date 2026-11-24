# 13 — "Things you said that Zeph kept": Users see and delete their kept quotes

Status: completed
Track: B
Blocked by: 11

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 20, 51, 52, 53, 54, 55, 58). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Quotes kept as evidence are the User's own words, so they must see and be able to delete them even while the Pattern is hidden (ADR-0027). A new list on the Memories page shows every kept quote with its context line (shown apart, as Zeph's note) and day, with no Pattern named. Deleting one removes the Observation and scores its Pattern again.

Wherever Message Retention is explained, Copy says plainly that quotes kept as evidence stay until deleted. Before Pattern noticing starts for an existing User, they are told what has changed.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [x] The Memories page lists every kept quote with its context line and day, newest first, with no Pattern Type or Pattern named
- [x] The quote and Zeph's note are shown apart
- [x] A User can delete a quote; it is gone at once and can't come back from a Conversation end already under way
- [x] The list works whether User Memory is on or off
- [x] New Copy slots hold the list's title, explanation and empty state, and the retention wording names kept quotes
- [x] An existing User is told what changed, in chat or on the Dashboard as agreed with the owner in this issue, before their first Observation is kept
- [x] Admins see only how many kept quotes a User has
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

- `11-tagging-step-keeps-observations.md`

## Comments

Plan (24 Nov 2026, branch `pattern-13-kept-quotes`, worktree `ai-chat-companion-pattern-13`):

- **Owner's choices.** The list is a new eighth Memories tab, "Things you said" (`?tab=quotes`), last in the row. Users are told on the Dashboard: a notice on Home and Memories with a "Got it" button; no Observation is kept for a User until they press it. One rule for every User, new or existing.
- **Backend.** `UserMemoryService` lists a User's kept quotes (quote, context line, day; newest day first) and deletes one, then scores their Patterns again (`observations_deleted`). Routes `GET /kept-quotes` and `DELETE /kept-quotes/{id}`; the list doesn't look at User Memory. No Pattern Type or Pattern leaves the API.
- **Can't come back.** Scoring and deleting a quote each take a lock on the User's row, in one transaction with their reads and writes, so a Conversation end already scoring can't save a state worked out from a quote deleted meanwhile, and the deletion's own rescoring waits for it.
- **Told first.** New `users.pattern_noticing_told_at` (migration 0084). `/me` says whether to show the notice (Pattern noticing works for them and not told yet); `POST /me/pattern-noticing-told` sets it. The tagging step runs only once it is set.
- **Admins.** The Users API gives `kept_quote_count`; the user panel adds a "Kept quotes" row in "What Zeph holds".
- **Copy.** New slots: the tab name, heading, explanation, Zeph's note label, delete button, empty title and body; the notice's title, body and button; and `account.delete_data.kept_quotes`, shown after the retention line on Account ("Quotes Zeph keeps as evidence stay until you delete them."). A new slot, so the live text reaches existing databases.
- **Design.** Following the issue (as issue 10 did): new `Memories--tab-quotes.html` and `M-Memories--tab-quotes.html` built from the Patterns tab's parts, the tab added to every Memories reference, the sentence added to `Account`/`M-Account`, the notice sample in `States`, baselines reshot. The "Kept quotes" Admin row isn't drawn in `AdminUsers` (as with issue 12's rows), flagged for the designer.

Decisions made while building (24 Nov 2026):

- **Admin row** "Kept quotes" shows only when above 0, like the Pattern state rows (not drawn in `reference/AdminUsers.html`, flagged for the designer).
- **Quote marks** are their own Copy slot (`memories.quotes.quote`, "“{quote}”"); "Got it" that can't be saved has its own slot (`shared.pattern_noticing.save_failed`).
- **Retention wording** is a new slot (`account.delete_data.kept_quotes`) shown after the retention line, so the live text reaches existing databases (a changed seed text would not replace a stored slot).
- **Told is kept** after Delete My Data: it records that the User was told, not their data.
- **Field name** `show_pattern_noticing_notice` on `/api/me` (renamed in review).
- **Left from review:** the quote card's note row copies the Patterns tab's markup (it is the drawn design); one shared delete lock disables every card's delete button while one deletes (same as the Patterns tab); tagging's insert isn't under the User lock, which is safe while nothing tags a Conversation twice.

Evidence (24 Nov 2026, worktree stack on 3020/8020, real DeepSeek model, made-up User "Run check" only):

- **List, newest first, no Pattern named.** Signed-in plain User, `/memories?tab=quotes` at 1280: “I had plans with friends but I cancelled them so she would not be upset with me.” (You said this on 24 Nov, Zeph's note under it) above “I just said sure, no problem” (21 Nov, its day moved back in the database). The panel holds no "pattern", "CONF", "AVOID" or "BELONG". Tests: `test_kept_quotes_are_listed_newest_first_with_their_line_and_day_and_no_pattern`, Memories "lists each kept quote apart from Zeph's note…".
- **Shown apart.** Each card: the quote in quote marks with its day, then a "Zeph's note" label and the context line in its own row. 390: no sideways scroll. Reference: `Memories--tab-quotes.html`, `M-Memories--tab-quotes.html`.
- **Delete, at once, can't come back.** Clicking "Delete quote: I smiled and said it was fine" removed it from the page straight away and after reload, and from `observations`. In the backend container on the real database, a quote was deleted while scoring was under way (the race test's set-up): the deletion waited 1.05 s for scoring to finish, and afterwards there were 0 quotes and 0 Patterns, so the quote didn't come back. Without the locks the same test fails. Tests: `test_a_quote_deleted_while_a_conversation_end_scores_does_not_come_back`, `test_deleting_a_kept_quote_removes_it_and_scores_its_pattern_again_at_once`, `test_a_deleted_quote_moves_its_pattern_back_and_logs_why`, `test_a_user_can_not_delete_a_quote_that_is_not_theirs`.
- **User Memory on or off.** With the Memory switch turned off on the page ("Memory is paused" shown), the tab still listed both quotes and the delete worked; switched back on after. Tests: `test_kept_quotes_are_listed_and_deletable_with_user_memory_off`, Memories "still shows and deletes kept quotes when User Memory is off".
- **Copy and retention wording.** All words on the tab and notice come from the new slots (the Memories "reads every word from Copy" tests include the new tab). Account: "Messages are otherwise kept for 30 days. Quotes Zeph keeps as evidence stay until you delete them." Tests: `AccountSettings.test.tsx` retention tests, `test_the_design_fixture_copy_is_the_seed_copy`.
- **Told first.** With Pattern noticing off, Home showed no notice. Switched on for this User only: Home (390) and Memories showed "Zeph now keeps some of your words." with Got it. A Conversation ended by the quiet gap before Got it: Day Summary written, no tagging call, 0 Observations. Pressing Got it hid the notice (also after reload) and set `pattern_noticing_told_at`. The next ended Conversation was tagged by the real model: 2 Observations kept, a noticed Pattern logged `conversation_tagged`. Only one tagging call in all, after Got it. Tests: `test_no_quote_is_kept_until_the_user_has_been_told`, `test_the_notice_shows_while_pattern_noticing_works_until_the_user_says_got_it`, `DashboardHome.test.tsx`, Memories notice tests (incl. save failed).
- **Admins see only the count.** Signed-in Admin, Users page, this User's panel: "Kept quotes 2" under What Zeph holds; the `/api/admin/users` answer held none of the quote words. Test: `test_admins_see_only_how_many_kept_quotes_a_user_has`, `AdminUsers.test.tsx`.
- **Checks.** `make check` on the rebased final code: ruff clean, ruff format clean, mypy clean (237 files), pytest 1900 passed; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` clean, `pnpm test` 136 files, 941 tests passed. Pixel test (git-ignored copy of `compare.cjs` blocking Clerk's protect probes, design sessions from `design-sessions.sh`): PASS Memories, all six desktop tabs but Day Summaries, Memories--tab-quotes (0.28%), Account, M-Account, Dashboard, M-Dashboard. FAIL Memories--tab-summaries 0.75%, M-Memories 0.91%, M-Memories--tab-patterns 0.58%, M-Memories--tab-quotes 0.64%: all from the seed Copy's Memories hero line ("short summaries of past Conversations") and "Conversation Summaries" tab and heading, which differ from the references' "Day Summaries" wording. Main fails the same pages by the same amounts (0.71%, 0.91%, 0.58%), so not from this branch. `shoot.cjs` on the new references changed only the Memories, Account and States baselines.
- **Final build.** After the review fixes and rebase, the stack rebuilt and the notice checked again: shown on Memories and Home (390, no sideways scroll), gone after Got it and after reload, told time saved, no page errors.
- **Review.** Standards and spec reviews run. Fixed: field renamed to `show_pattern_noticing_notice`, a `to_kept_quote_response` mapper like the others, `newest_first` placed with the service, a test for "Got it" failing. Left: see above.

## Completion

- Completed: 2026-11-24
- Commit: <to be filled in after the merge>
