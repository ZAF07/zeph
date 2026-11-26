# 03 — Users set how direct Zeph is with its Read

Status: completed
Track: A
Blocked by: none

## Parent

`.scratch/pattern-pipeline/PRD.md` (user stories 59, 60, 61, 62, 63). Design: `docs/pattern-pipeline/README.md`. Decisions and starting numbers: `.scratch/pattern-pipeline/grill-decisions.md`.

## What to build

Each User sets how direct the Companion is with its Read: gentle, balanced (to start) or direct. It changes how soon and how plainly the Read is said, never whether Zeph has one, and never whether a Pattern is ready. It is ignored while the User is struggling. Users change it on the Dashboard or by telling Zeph in chat (a Chat Setting Change, marked "Changed in chat"). The Reply Plan is given it as one more input.

This adds Dashboard UI: read `web/design/README.md` first, add or extend the reference in `web/design/reference/`, and check the page with the pixel test (ADR-0018).

## Acceptance criteria

- [x] A User can pick gentle, balanced or direct on the Dashboard; balanced is the default for existing and new Users
- [x] A User can change it in plain words in chat, and the Dashboard marks it "Changed in chat"
- [x] The Reply Plan is given the setting, and the Reply Plan prompt says what each level means
- [x] On gentle, a User who asks for Zeph's view still gets its Read
- [x] While the Understanding says the User is struggling, the setting isn't given to the Reply Plan
- [x] A Settings Eval case covers the chat change
- [x] New Copy slots hold the setting's name, help text and level names
- [x] Each criterion above was checked in the running app (`/run`) before being ticked, and the checks for the languages touched pass

## Blocked by

None - can start immediately

## Comments

Evidence (24 Nov 2026, worktree stack, branch `pattern-03-directness`):

- **Dashboard, balanced default:** on `/account` as a plain User, at 1280 and 390: Balanced picked on load, Direct clicked, still Direct after reload. Existing Users: migrated the stack down to the migration before (column gone) and back up. All 3 Users came back on `balanced`. Tests: `test_a_new_user_starts_on_balanced`, `test_an_existing_install_puts_users_on_balanced_and_reloads_the_prompts`.
- **Chat change, "Changed in chat":** through the real webhook and model (`InProcessCompanion` in the backend container, signed in as the Clerk test User), "could you go easier on me when you tell me what you think?" called `change_directness`. The User was saved as `gentle` with `settings_changed_in_chat.directness`, and `/account` showed Gentle picked and "Changed in chat · 24 Nov" at 1280 and 390.
- **Reply Plan given the setting:** the logged Reply Plan input held "How direct they want you to be with your Read: gentle". `reply_plan_prompt` now has `- gentle:`, `- balanced:` and `- direct:` (reloaded by migration 0086).
- **Gentle, asks for a view:** on gentle, not struggling, "what do you honestly think is going on with me?" gave `say_read: true`. The Read was sent at once, softly ("…That's one way of seeing it, anyway.").
- **Struggling:** "I'm completely overwhelmed… can't cope with work" gave an Understanding with `struggling: true`, and the Reply Plan input had no directness line. Test: `test_a_struggling_users_reply_plan_is_not_given_the_directness`.
- **Settings Eval:** new cases `more-direct` and `gentler`. Live runs: more-direct passed 1 of 3, gentler 1 of 2. The Reply model calls the tool unreliably; this is logged in issue 20.
- **Copy:** `account.directness.title`, `.help`, `.gentle`, `.balanced`, `.direct`, read by `DirectnessSetting`. The every-word-from-Copy test covers the card.
- **Pixel test:** Account, M-Account, CheckIns and M-CheckIns PASS (0.19%, 0.45%, 0.03%, 0.06%), using the Clerk-probe workaround copy of `compare.cjs`. The `Account` and `M-Account` references and baselines are extended with the new card.
- **Checks:** pytest 1902 passed; ruff, ruff format and mypy clean; pnpm lint, format:check and typecheck clean; vitest 936 passed.


## Completion

- Completed: 2026-11-24
- Commit: 78bbd8e (merge "Merge pattern-03-directness: Users set how direct Zeph is with its Read"; work in c47da90 "Pattern pipeline issue 03: Users set how direct Zeph is with its Read", b1f75e7 "Directness review fixes: one ChoiceSegments for Check-ins and directness, a missing directness line means follow the three conditions, direct never cuts in mid-vent", 48afc4b "Issue 03 done: archived with evidence, findings logged in issue 20, docs say the directness setting is built", 586044d "Directness migration follows 0084 from main: now 0085", 5ed5570 "Directness migration follows 0085 from main: now 0086; Account baselines rebuilt with issue 13's change")
