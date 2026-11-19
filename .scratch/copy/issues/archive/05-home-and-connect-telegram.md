# 05 — Copy: Home, Connect Telegram and the Dashboard menu

Status: completed

Lane: B.

## Parent

`.scratch/copy/PRD.md`

## What to build

Home and Connect Telegram read every word from Copy, including their empty, loading and web-side error messages and tab titles, each with its own tab on the Copy page. The Dashboard menu and frame words a User sees on every User page go in the **Shared** tab. Live values (e.g. a Telegram handle) use placeholders.

Not part of this issue:
- Backend rule messages are not Copy.
- The AI notice and Memory notes stay where they are until issue 08 moves them.

## Acceptance criteria

- [x] Home, Connect Telegram and the Dashboard menu show only Copy text, with placeholders filled; no default text in web code.
- [x] Their empty, loading and web-side error messages are Copy.
- [x] The Copy page shows Home and Connect Telegram tabs and the menu slots in Shared, slots in page order.
- [x] Seed text matches the references; the pixel test passes for these pages at both widths.
- [x] Tests cover the converted pages and states; all Python and web checks pass.
- [x] `/run`: as an Admin, edit a Home heading and a menu item, then see both as a signed-in User.

## Blocked by

- `.scratch/copy/issues/01-landing-end-to-end.md`

## Comments

- 2026-11-19 — From issue 03: the Telegram link card (`TelegramConnectionCard`) already reads Copy, because onboarding shows it. Its slots are `connect_telegram.card.*` in the Connect Telegram tab; add the page's own slots (heading, lead, tab title) before them. `/connect-telegram` reads Copy on the server and shows `CopyLoadFailed` when it can't. Onboarding passes Copy as a prop rather than through a query hook (see issue 03's decisions); choose one way for the Dashboard pages.
- 2026-11-19 — Done (branch `copy-05-home-and-connect-telegram`).
  - Seed: a **Home** tab (`home.*`, between Onboarding and Connect Telegram, slots in page order: tab title and description, loading and couldn't-load, greeting, last talked, the not-connected card, Telegram, Check-ins, Memory on, Working toward, Recently remembered, Plan, the streaks line); the Connect Telegram page's own slots (`connect_telegram.page_title`, `page_description`, `eyebrow`, `heading`, `lead`, `lead_computer`, `lead_phone`) before the card's; the Dashboard menu and frame in **Shared** (`shared.dashboard.*`: menu items, fold and phone-menu buttons, the folded "Z", the menu's screen-reader name, loading the account, Sign out, and the frame's loading and couldn't-load words). The wordmark reuses `shared.wordmark`. Text is the code's text, which passed the pixel test; the not-connected body takes the references' wording ("Connect once and Zeph will say hello."). Tab titles are the references' (`Zeph — Home`, `Zeph — Connect Telegram`).
  - Web: `DashboardFrame` reads Copy on the server and gives the shell and `OnboardingGate` only the frame's slots (`shared.dashboard.*`, `shared.wordmark`), passed down as props to the sidebar, rail, phone bar and phone menu. `/` reads Copy first: signed in it takes Home's title from Copy and gives `DashboardHome` its slots; `/connect-telegram` takes its title and header from Copy. `lib/home.ts` wording helpers take Copy; new `fillCopy` (read and fill one slot, `lib/copy.ts`) and `formatLongDay` (`lib/dates.ts`, shared with the Check-ins page's `pauseEndText`). `userMenuItems` name their label's slot (`labelCopyKey`).
- Decisions:
  - **Copy reaches the Dashboard as props read on the server**, as onboarding does (issue 03): the frame and pages need Copy on the server anyway for titles and the error state, and a query hook would need hard-coded "loading" words.
  - **When Copy can't be read, the frame shows the public couldn't-load page** (`SiteLoadFailed`) in place of frame and page, admin pages included: the menu has no words without Copy. The Copy read comes from the same backend the admin pages need, so when it fails they would fail too. The code review flagged this; kept on purpose.
  - **Check-in frequency names have one home: Onboarding's** `onboarding.check_ins.frequency_*`; Home's card reads them there (CONTEXT: a slot has one home). Issue 07 can move them to Check-ins with all their readers.
  - Not Copy, as the PRD allows: the admin menu section and the account row's "Admin" (admin words), the orange "To build" tag (the design's builder marker, `web/design/README.md`), and the AI notice and Memory-off note (Platform Settings until issue 08).
- Left for later:
  - `ChangedInChatCaption` takes an optional `text`; Home passes Copy, while Check-ins, Account and Memories still use its default words in code (issues 06/07: pass Copy and drop the default).
  - Home has its own Copy for "until you resume", "until {day}", "Not available on your account" and "Changed in chat · {day}"; the Check-ins page still has these in code (`pauseEndText`, `notAvailableText`). Issue 07 decides whether they share one home.
  - Environment: one Docker web build and one fixture dev-server start failed to download the Outfit font from Google Fonts (`next/font`); each passed on a retry. With the fallback font every page fails the pixel test, so check the dev log for "Failed to download `Outfit`" before reading a pixel FAIL.

### Evidence per criterion

1. Only Copy text: `DashboardHome.test.tsx` "shows only Copy text with …" for Telegram connected with Check-ins on; not connected, nothing remembered, Check-ins paused; Check-ins off; Check-ins not available with no Telegram username; and "while loading and when Home can't load" (marked Copy, `wordsNotFromCopy`; allowed: the User's own data, the Platform Settings AI notice and "To build"). `DashboardShell.test.tsx` "shows a User only Copy text in the sidebar / the folded rail / the open phone menu". `OnboardingGate.test.tsx` "words its loading and couldn't-load states from Copy only". `connect-telegram/page.test.tsx` "shows only Copy text". Placeholders filled: "words the page from an Admin's Copy, with live values filled in" (`{name}`, `{username}`, `{day}`) and `lib/home.test.ts` "words every line from an Admin's Copy". A grep of the converted components finds no words left besides the admin group's "Admin".
2. Empty, loading and error messages: Home's goal and memory empty states, its loading panels and couldn't-load block, and the frame's loading and couldn't-load are Copy (tests above). The only error words not from Copy are in the couldn't-load block shown when Copy itself can't be read (`CopyLoadFailed`), as issue 03 settled.
3. Copy page tabs: `tests/test_copy.py::test_admin_sees_each_tab_with_slots_in_page_order` (tabs Landing, Pricing, How it works, Sign in and sign up, Onboarding, Home, Connect Telegram, Shared; every tab's keys in seed order) and `test_home_connect_telegram_and_dashboard_menu_slots_carry_their_seed_text` (the page's slots before the card's; menu slots in Shared). Live: the Home, Shared and Onboarding tabs opened and saved on `/admin/copy`.
4. Pixel test (fixture dev server, design sessions, after the rebase on `ca8c00a`): `PASS Dashboard 0.01%`, `PASS Dashboard--menu-folded 0.00%`, `PASS M-Dashboard 0.01%`, `PASS M-Menu 0.01%`; Landing, M-Landing, Onboarding, M-Onboarding, Memories (all tabs), M-Memories, CheckIns, M-CheckIns, Account, M-Account all PASS. `ConnectTelegram FAIL 2.60%, height 800 vs 856` and `M-ConnectTelegram FAIL 2.15%, height 844 vs 1205`: the same numbers issue 03 recorded on main, the FAILs accepted in the redesign (builder notes in the baselines), unchanged by this work.
5. Checks (after the rebase): `ruff check` All checks passed!, `ruff format --check` 506 files already formatted, `mypy src` no issues in 188 files, `pytest -n auto` 1333 passed; `pnpm lint` clean, `pnpm format:check` all files use Prettier code style, `pnpm typecheck` clean, `pnpm test` 124 files, 811 passed; `pnpm build` compiled successfully. New tests: `DashboardFrame.test.tsx`; new cases in `DashboardHome`, `DashboardShell`, `OnboardingGate`, `app/page`, `connect-telegram/page`, `lib/home`, `lib/copy` (`fillCopy`), `tests/test_copy.py`.
6. /run (worktree stack): as an Admin on `/admin/copy`, the Home tab's "Greeting after 6 PM" without `{name}` was turned away with "Keep {name} in the text." (`05-screenshots/copy-home-missing-placeholder.png`); then "Welcome back, {name}. Good to see you." saved (`copy-home-saved.png`), and Shared's "Dashboard menu: Memories link" changed to "What Zeph knows" (`copy-shared-saved.png`). The account was made a plain User: `/` had title "Zeph — Home", heading "Welcome back, Run check. Good to see you." and menu Home, What Zeph knows, Check-ins, Account & privacy, Plan, with no Admin group, at 1280 and 390 with the phone menu open (`home-1280.png`, `home-390.png`, `home-390-menu.png`); `/connect-telegram` had title "Zeph — Connect Telegram" and the changed menu item (`connect-telegram-1280.png`). After the review fixes and a rebuild (edits survived the re-seed), the Onboarding tab's second how-often choice was changed to "Every few days" and Home's Check-ins card showed "How often · Every few days" (`home-check-ins-frequency.png`). No page errors.

## Completion

- Completed: 2026-11-19
- Commit: <filled in after merge>

