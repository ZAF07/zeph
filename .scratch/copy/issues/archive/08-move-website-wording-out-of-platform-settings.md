# 08 — Copy: move website wording out of Platform Settings

Status: completed

Lane: whichever lane is free first.

## Parent

`.scratch/copy/PRD.md`

## What to build

The website wording that is a Platform Setting today becomes Copy, so every website word has one home:

- AI notice and short AI notice
- User Memory explanation and Photo Viewing explanation
- "Memory is paused" and "Memory isn't available" notes, each split into a title slot and a body slot (the title and body of the design's "Memory is off" notice in `States`, as `PausedNotice` draws them; no `**` markup remains)
- Delete My Data description

Each moves into the Copy tab of the page that shows it (Shared if more than one page shows it). The Settings page drops these fields. Endpoints that sent this wording inside other data (e.g. the Home data and the signed-in User's Memory note) stop sending it; the web app picks the right slot from the flags it already gets. A migration drops the old settings; no backfill (the platform isn't live).

Stays as is: the onboarding reason choices and all chat wording (Platform Settings), and the Crisis Reply (Safety).

## Acceptance criteria

- [x] Each listed wording is a Copy slot on the right tab and no longer a Platform Setting (not in the settings read or save, not on the Settings page).
- [x] The Memory notes show as `PausedNotice` title and body, exactly as the "Memory is off" notice in `States` draws them, picked by the User's Memory flags.
- [x] No endpoint sends this wording outside the Copy reads.
- [x] Onboarding reason choices, chat wording and the Crisis Reply are untouched.
- [x] Seed text matches the references; the pixel test passes for every page showing this wording at both widths.
- [x] Tests cover the move and the note picking; all Python and web checks pass.
- [x] `/run`: as an Admin, edit the "Memory is paused" lead, turn Memory off as a User and see it bold on Home and Memories; the Settings page no longer shows these fields.

## Blocked by

- `.scratch/copy/issues/03-onboarding.md`
- `.scratch/copy/issues/05-home-and-connect-telegram.md`
- `.scratch/copy/issues/06-memories.md`
- `.scratch/copy/issues/07-check-ins-and-account.md`

## Comments

- 2026-11-19 — From issue 05: Home and the Dashboard menu read Copy now, except the AI notice (Home's footer, from `/home`'s `ai_notice`), the short AI notice (`SidebarAiNotice`, from Platform Settings) and the Memory-off note (`HomeMemoryLine`'s `note`, with `**bold**`). Home's "Memory is on." note is already Copy (`home.memory.on_title`, `on_body`); the paused and not-available notes can sit next to it in the Home tab. The frame gives the menu only `shared.dashboard.*` and `shared.wordmark` (`DashboardFrame` `pickCopy`); widen it when the short AI notice moves.
- 2026-11-19 — From issue 06: Memories reads Copy now, except the Memory-off note (`MemoryOffNotice`'s `note`, from `me.memory_note`, with `**bold**` split into title and body). Its "Turn memory on" button is already Copy (`memories.memory_off.turn_on`, passed as `turnOnLabel`); the paused and not-available notes can sit next to it in the Memories tab. `/memories` gives the page only `memories.*` slots (`pickCopy`); widen it if a moved note lives in another tab. Account shows the same notice without the button.
- 2026-11-19 — From issue 07: Check-ins and Account read Copy now. Account still shows four Platform Settings: the Memory-off note (`MemoryOffNotice`'s `note`, from `me.memory_note`, no button on Account), the User Memory and Photo Viewing explanations (`PreferenceSwitch`'s `explanation`, from `usePlatformContent`) and the Delete My Data description (`YourDataSection`). The Delete my data dialog body joins that description with the Copy line `account.delete_data.dialog_body` ("This can’t be undone.") in code. Once these move, `AccountSettings` may no longer need `usePlatformContent` except for `message_retention_days`. `/account` gives the page only `account.*` and `onboarding.location.*` slots (`pickCopy`); widen it if a moved note lives in another tab.
- 2026-11-19 — Done (branch `copy-08-website-wording`).
  - Seed: ten new slots. **Onboarding** `onboarding.hello.ai_notice` (the full AI notice, above the tick box). **Home** `home.footer.ai_notice` (the footer line). **Account** `account.photos.explanation` and `account.delete_data.description`. **Shared** `shared.dashboard.ai_notice` (the menu's short notice), `shared.memory_explanation` (Onboarding and Account), and `shared.memory_off.paused_title`, `paused_body`, `not_available_title`, `not_available_body` (Home, Memories and Account). No `**` is left anywhere in Copy.
  - Backend: the seven settings are gone from the Platform Settings seed, the editable list and `/api/platform-content` (now only the reason choices and message retention). `UserMemoryService.memory_note` is removed. `/api/me` drops `memory_note`; `/api/home` drops `memory_note` and `ai_notice` and sends `user_memory_enabled` and `user_memory_available` instead. `MeService` needs only the Feature service. Migration `0063` deletes the old settings rows, with no backfill.
  - Web: `memoryOffNote` (`lib/memory-off-note.ts`) picks the paused or not-available slots from the two flags, and the Admin's switch wins. `MemoryOffNotice` draws it as `PausedNotice` on Home, Memories and Account. Home's line now only says "Memory is on". `SidebarAiNotice` reads `shared.dashboard.ai_notice` from the menu's Copy and is no longer a client component. Onboarding, Account and `YourDataSection` read their slots. The Settings page drops the seven fields. The Home, Memories, Account and onboarding pages pass the extra Shared slots (`pickCopy`); the frame already passed `shared.dashboard.*`.
- Decisions:
  - **Home's footer notice is its own Home slot.** `Dashboard.html` draws different words in the footer ("Zeph is an AI companion. It isn't a mental-health service…") from the menu's short notice. The rule "seed matches the references" plus one home per page gives two slots. Before this, the footer showed the short notice.
  - **Home sends the two Memory flags**, as `/me` does. Home got no flags before, so the web had nothing to pick the slot from.
  - **Home shows the Memory-off note as `PausedNotice`**, like Memories and Account (the criterion names all three). It has no "Turn memory on" button: Home has no switch, as on Account. The Memories page has the button.
  - **The Memory-off wording keeps the existing words** ("Memory is paused." / "Memory isn’t available on your account." plus "Nothing is deleted…"), split into title and body. The `States` notice ("Memory is off" / "Zeph isn’t keeping new details…") is a sample of the notice's shape. The current words were chosen on purpose in migration 0034 to name Delete My Data.
  - **The Memory explanation follows the references**: "details: your goals" (colon) and straight apostrophes, as `Onboarding.html` and `Account.html` draw it.
  - **Onboarding's AI notice is seeded with the real notice.** `Onboarding.html` draws the placeholder "[AI NOTICE, WORDED BY ADMINS IN PLATFORM SETTINGS]" there. The design fixture serves that placeholder for this one slot (`referencePlaceholders` in `design-fixtures/copy.ts`), so the pixel test still compares the page as drawn. The Copy admin fixture still serves the seed.
  - Max lengths are fitted to the design: AI notice 600, explanations 1000, menu notice 120, note titles 60, bodies and the delete description 400.
  - The two "paused" and "not available" bodies have the same seed text but stay two slots, so Admins can word each one.
- Review (`/code-review`): fixed Home not using `PausedNotice`, the test key list written twice, the flag type (`Pick<Me, …>`) and a doubled Copy read. Kept on purpose: the web picks the slot (the issue asks for it), plus the decisions above.

### Evidence per criterion

1. A Copy slot on the right tab, no longer a Platform Setting: `tests/test_copy.py::test_the_wording_moved_from_platform_settings_is_copy_on_its_page_tab` checks each key's tab and text. `tests/test_admin_settings.py::test_website_wording_moved_to_copy_is_no_longer_a_setting` covers all seven keys: absent from the settings read, and a save is turned away with 422. `PlatformSettingsForm.test.tsx` "leaves the website wording to the Copy page" checks the form. Live: the `/run` script read `/admin/settings` and found none of the seven labels ("“Memory off” line in chat" still shows) (`08-screenshots/admin-settings.png`). The worktree database after migrating: `alembic_version` 0063, no rows left for the old keys, and four `shared.memory_off.*` slots.
2. Notes drawn as `PausedNotice` title and body, picked by the flags: `lib/memory-off-note.test.ts` covers on, paused, not available (whatever the User's own switch) and a missing slot. `Memories.test.tsx` "draws the paused note's title and body from Copy…" checks the title is 15px `text-text` and the body 13px `text-soft`. `DashboardHome.test.tsx` checks the same on Home, plus an edited not-available note while the User's switch is on. `AccountSettings.test.tsx` checks the paused note with no button, and the not-available note.
3. No endpoint sends this wording outside the Copy reads: `tests/test_dashboard_home.py::test_with_memory_on_home_and_me_send_the_flags_and_no_memory_wording` (no `memory_note` or `ai_notice` on `/home` or `/me`). `tests/test_onboarding.py::test_platform_content_comes_from_seeded_settings` shows `/platform-content` is exactly the reason choices and message retention. A `git grep` of `src` and `web/src` finds none of the old keys outside migrations.
4. Untouched: the diff removes only the seven keys from `platform_settings.yaml` and `platform_settings.py`. No safety, Helpline, Telegram or crisis file is in the diff. `onboarding_reason_choices` is still a Platform Setting (onboarding test above), and the chat-wording settings tests pass.
5. Seed text and pixel test: the new slots carry the reference text where a reference draws it (Account explanations and delete description, Home footer, menu notice, Memory explanation). `test_the_design_fixture_copy_is_the_seed_copy` passes. Pixel test after the review fixes (fixture dev server, design sessions): `PASS Dashboard 0.01%`, `Dashboard--menu-folded 0.00%`, `M-Dashboard 0.01%`, `M-Menu 0.01%`, `Memories 0.02%` and all five tabs, `M-Memories 0.05%`, `Account 0.03%`, `M-Account 0.06%`, `Onboarding 0.12%`, `M-Onboarding 0.06%`, every height equal. The full run (Login and Signup skipped, since they time out waiting on Clerk's network): 24 PASS, plus 9 known drifts with the same numbers recorded in redesign issues 09–13 and 17 (ConnectTelegram's real QR code; admin references carrying builder notes).
6. Tests and checks (final): `ruff check` All checks passed!, `ruff format --check` 301 files already formatted, `mypy src` no issues in 189 source files, `pytest -n auto` 1336 passed. `pnpm lint` clean, `pnpm format:check` All matched files use Prettier code style!, `pnpm typecheck` clean, `pnpm test` 129 files, 864 passed. New: the Copy and settings tests above, the migration test `test_an_existing_install_drops_the_wording_that_moved_to_copy`, `memory-off-note.test.ts`, and the Home, Memories, Account, Onboarding, menu and page tests.
7. `/run` (worktree stack, Playwright):
   - As an Admin on the Copy page's Shared tab, set "Memory paused by the User: title" from "Memory is paused." to "Memory is resting." and saved; the row shows "Last saved … by Run check" (`admin-copy-paused-title.png`). The Settings page no longer shows the fields (`admin-settings.png`).
   - The account was made a plain User, and `/admin/copy` sent it to `/`. On Memories, the Memory switch was turned off. The notice reads "Memory is resting. Nothing is deleted…" with "Turn memory on". The title is drawn in the bright text colour rgb(234, 242, 243), which is how the design draws a notice title ("bold" here means bright at weight 400, as in `States`).
   - Home (after the review fix) shows the same notice with no button, and Account shows it beside the switch. Account shows the Memory and Photo explanations and the Delete my data description from Copy. Home's footer shows its own notice, and the menu shows "Zeph is an AI, not a therapist or crisis service."
   - Screenshots: `user-memories-1280.png`, `user-memories-390.png`, `user-home-1280.png`, `user-home-390.png`, `user-account-1280.png`. No page errors.

## Completion

- Completed: 2026-11-19
- Commit: merge `9ac9cf3` into main — "Merge Copy issue 08: website wording moves out of Platform Settings into Copy (AI notices, Memory and Photo explanations, Memory-off notes as title and body, Delete My Data description); Home and /me send the Memory flags and the web picks the note; Settings drops the fields; migration 0063 drops the old settings"
  - Branch `copy-08-website-wording`:
    - `377b6e4` Copy 08: website wording moves out of Platform Settings into Copy
    - `d346842` Copy 08: Home draws the Memory-off note as the design's notice; tests share the moved keys; review tidy-ups
    - `24f0fb3` Copy 08: evidence recorded, issue completed and archived, screenshots; CONTEXT gives the Memory explanation and Memory-off notes one home in Shared and makes the AI Notice Copy; handover note on 09
