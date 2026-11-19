# 07 — Copy: Check-ins and Account

Status: completed

Lane: B.

## Parent

`.scratch/copy/PRD.md`

## What to build

The Check-ins and Account pages read every word from Copy, including empty, loading and web-side error messages, dialogs and tab titles, each with its own tab on the Copy page. Live values use placeholders, and counts use one/many slots as in issue 06 (if 06 isn't merged yet, follow its approach).

Not part of this issue:
- The Delete My Data description and the Photo Viewing explanation stay where they are until issue 08 moves them.
- Backend rule messages (e.g. Quiet Hours validation) are not Copy.

## Acceptance criteria

- [x] Check-ins and Account show only Copy text, with placeholders filled; no default text in web code.
- [x] Their empty, loading, error and dialog text is Copy.
- [x] The Copy page shows Check-ins and Account tabs, slots in page order.
- [x] Seed text matches the references; the pixel test passes for both pages at both widths.
- [x] Tests cover the converted pages and states; all Python and web checks pass.
- [x] `/run`: as an Admin, edit a Check-ins heading and an Account dialog line, then see both as a User.

## Blocked by

- `.scratch/copy/issues/01-landing-end-to-end.md`

## Comments

- 2026-11-19 — From issue 03: `LocationFields` and `CheckInFrequencyPicker` now take their words from the page. `ProfileForm` and `UserCheckInSettingsPanel` pass the old words in code until this issue makes them Copy. Onboarding has its own slots for the same words (`onboarding.location.*`, `onboarding.check_ins.frequency_*`); decide whether Account and Check-ins share those (one home) or get their own.
- 2026-11-19 — From issue 05: Home's Check-ins card reads the frequency names from `onboarding.check_ins.frequency_*`, their one home for now; if they move to the Check-ins tab, move Home's reads too (`lib/home.ts` `checkInFrequencyText`, and `pickCopy` in `app/page.tsx`). Home has its own slots for "until you resume", "until {day}", "Not available on your account" and "Changed in chat · {day}" (`home.check_ins.*`); the Check-ins page still writes them in code (`pauseEndText`, `notAvailableText`, `ChangedInChatCaption`'s default). Decide one home, and drop `ChangedInChatCaption`'s default once every caller passes Copy.
- 2026-11-19 — From issue 06: Memories has its own "Not available on your account" (`memories.switch.not_available`) and "Changed in chat · {day}" (`memories.switch.changed_in_chat`), like Home; Account's `ProfileForm` is now the last caller of `ChangedInChatCaption`'s default text. Counts use a `_one`/`_many` slot pair picked with `countSlotKey` (`lib/copy.ts`); the Copy page shows such a pair side by side on its own.
- 2026-11-19 — Done (branch `copy-07-check-ins-account`).
  - Seed: a **Check-ins** tab (`check_ins.*`, 54 slots) after Memories and an **Account** tab (`account.*`, 54 slots) after Connect Telegram, as the PRD lists them; each tab's slots in page order. Check-ins: tab title and description, hero, switch (on, off, paused, not available, screen-reader name), loading, couldn't load, couldn't save, the not available, paused (with and without `{day}`) and off notes, the settings card (how often, changed in chat and by an Admin with `{day}`, quiet hours with From and Until, pause buttons), "tell Zeph", what a check-in can be, recent check-ins (heading, empty, the four kinds of line, the four tags, ignore rule). Account: tab title and description, header, loading, couldn't load, Profile (labels, no email, changed in chat, save, saving, saved, couldn't save), the Memory and photo switch titles, "Not available on your account", couldn't change, Your stickers (lead, couldn't remove, loading, couldn't load, picture and remove names with and without `{emoji}`, empty), Delete my data (retention one/many with `{count}`, button, "Deleting…", dialog, done, couldn't delete), Delete account (description, button, dialog, couldn't delete).
  - Web: `/check-ins` and `/account` read Copy on the server (`loadCopy`), take their title and description through `pageMetadata` and show `CopyLoadFailed` when Copy can't be read; only their own slots go to the browser (`pickCopy`), plus onboarding's frequency names (Check-ins) and location labels (Account). Every Check-ins and Account component takes `copy`; `QuietHoursFields`, `CheckInFrequencySegments`, `ChangedByAdminCaption` and `DeletionRow` take their words as props. `ChangedInChatCaption`'s default text is gone (`text` is required). `lib/check-ins.ts`: `pausedText`, `recentCheckInTitle` and the new `checkInStatusText` and `checkInFrequencyChoices` read Copy; the unused `pauseEndText` and `notAvailableText` are removed.
- Decisions:
  - **One home for the frequency names and the location labels: Onboarding.** Check-ins reads `onboarding.check_ins.frequency_*` (like Home) and Account reads `onboarding.location.*`. Same parts, same words, so one edit changes every page; CONTEXT's Copy entry now says so.
  - **Own slots for "Not available on your account" and "Changed in chat · {day}"** in each tab, following Home and Memories, where they sit in different places with different names. Account uses one slot of each for all its switches, the time zone and stickers. "Changed by an Admin · {day}" is a new Check-ins slot.
  - **Admin words stay in code** (PRD: not Copy): `UserCheckInSettingsPanel` passes "Quiet hours", "From", "Until" and the admin frequency names, and `LoadFailed` keeps "Try again" as the default admin pages use.
  - The Delete my data dialog body is the Platform Setting description followed by the Copy line `account.delete_data.dialog_body` ("This can’t be undone."), joined in code until issue 08 moves the description.
  - The User's email, country and time zone names, sticker emoji and notes, Check-in Kind names and descriptions and Check-in days are values, not Copy.
- Left for later: the Memory-off note (`me.memory_note`), the User Memory and Photo Viewing explanations and the Delete My Data description on Account stay Platform Settings until issue 08.
- Environment: the first fixture dev server could not download Outfit from Google Fonts and fell back to another font, so every page (touched or not) failed by 1.5–5%. After a restart with a fresh `.next`, Outfit loaded and every page passed.

### Evidence per criterion

1. Only Copy text: `CheckInsSettings.test.tsx` "reads every word from Copy" runs `wordsNotFromCopy` (page text, icons aside, plus every `aria-label`) with marked Copy and marked data with Check-ins on, settings changed in chat and by an Admin, and recent Check-ins of every kind; while paused until resumed and until a day; while off; with Check-ins not available; after a failed save; while loading and when loading fails. `AccountSettings.test.tsx` does the same with everything on and changed in chat with stickers with and without an emoji; with no email, every feature off by an Admin and no stickers; after a save and after failed saves; in both delete dialogs, after a delete and after failed deletes; while loading and when loading fails; while the stickers load and when they can't. A `grep` of the converted components finds no literal words. Country and time zone names are left out as values, as in Onboarding.
2. Empty, loading, error and dialog text: covered by the states in 1. The page tests `app/(dashboard)/(user)/check-ins/page.test.tsx` and `account/page.test.tsx` cover the couldn't-load block when Copy can't be read.
3. Copy page: `tests/test_copy.py::test_admin_sees_each_tab_with_slots_in_page_order` (… Home, Memories, Check-ins, Connect Telegram, Account, Shared; each tab's keys in seed order). Live: the `/run` script opened the Copy page's "Check-ins" and "Account" tabs by name; the Check-ins slots read in page order (`07-screenshots/admin-check-ins-heading.png`).
4. Seed text: all slots are the removed web strings. The spec review checked them against the references and found two curly apostrophes where `Account.html` has straight ones (`account.stickers.lead`, `account.delete_account.description`); fixed to match the reference. `test_the_design_fixture_copy_is_the_seed_copy` passes. Pixel test (fixture dev server, `STATE_USER` session): `PASS CheckIns 0.03%, height 1516 vs 1516`, `PASS M-CheckIns 0.06%, 2348 vs 2348`, `PASS Account 0.03%, 1503 vs 1503`, `PASS M-Account 0.06%, 2275 vs 2275`. Neighbours: `PASS Dashboard`, `Dashboard--menu-folded`, `M-Dashboard`, `Memories` and its five tabs, `M-Memories`.
5. Tests and checks (after rebasing on main): `ruff check` All checks passed!, `ruff format --check` 506 files already formatted, `mypy src` no issues in 188 source files, `pytest -n auto` 1333 passed; `pnpm lint` clean, `pnpm format:check` All matched files use Prettier code style!, `pnpm typecheck` clean, `pnpm test` 128 files, 856 passed; `pnpm build` compiled successfully. New: the two page tests, the only-Copy tests above, the one-day retention test ("one" slot for 1, "many" for 14), and the `lib/check-ins.test.ts` tests for each line read from Copy.
6. `/run` (worktree stack, Playwright): as an Admin on the Copy page, set Check-ins "Heading" to "When Zeph says hello" and Account "Delete account, asking first: message" to "Your account and everything in it goes for good. No undo.", saving each tab (each row shows "Last saved … by Run check"; `admin-check-ins-heading.png`, `admin-account-dialog.png`). The account was then made a plain User; `/admin/copy` sent it to `/`. At 1280 and 390, `/check-ins` (title "Zeph — Check-ins") showed the heading "When Zeph says hello" (`user-check-ins-1280.png`, `user-check-ins-390.png`), and on `/account` (title "Zeph — Account & privacy") Delete my account opened "Delete your account? | Your account and everything in it goes for good. No undo. | Keep my account | Permanently delete account" (`user-account-dialog-1280.png`, `user-account-dialog-390.png`). No page errors.

## Completion

- Completed: 2026-11-19
- Commit: merge `1e4e1f9` into main — "Merge Copy issue 07: Check-ins and Account read every word from Copy (Check-ins and Account tabs, every state and dialog); frequency names and location labels keep one home in Onboarding; ChangedInChatCaption has no default text"
  - Branch `copy-07-check-ins-account`:
    - `70b73da` Copy 07: Check-ins and Account read every word from Copy (Check-ins and Account tabs)
    - `beca491` Copy 07: Account seed keeps the reference's straight apostrophes; ProfileForm's Copy helper named for its tab (review)
    - `f516255` Copy 07: test the one-day retention slot
    - `daa12d9` Copy 07: evidence recorded, issue completed and archived, screenshots; CONTEXT gives the location labels one home in Onboarding; handover note on 08

