# 03 — Copy: Onboarding, and the words around sign-in and sign-up

Status: completed

Lane: A.

## Parent

`.scratch/copy/PRD.md`

## What to build

Onboarding reads every word from Copy (headings, questions such as "What brings you here?", field labels, buttons, its own error messages, tab title and description), with an Onboarding tab on the Copy page. Our words around the Clerk sign-in and sign-up forms are Copy too; the text inside Clerk's forms is not.

Not part of this issue:
- The onboarding reason choices stay a Platform Setting (the Companion is told them).
- The AI notice text shown during onboarding stays where it is until issue 08 moves it.

## Acceptance criteria

- [x] Onboarding and the sign-in/sign-up surrounds show only Copy text; no default text in web code.
- [x] The reason choices still come from Platform Settings and still save on the User.
- [x] The Copy page shows an Onboarding tab (and the sign-in/sign-up slots in their tab), slots in page order.
- [x] Seed text matches the references; the pixel test passes for these pages at both widths.
- [x] Tests cover the converted pages; all Python and web checks pass.
- [x] `/run`: as an Admin, edit an onboarding question, then go through onboarding as a new User and see it.

## Blocked by

- `.scratch/copy/issues/01-landing-end-to-end.md`

## Comments

- 2026-11-19 — Done (branch `copy-03-onboarding`).
  - Seed: three tabs before Shared, slots in page order: **Sign in and sign up** (`auth.*`, 14 slots), **Onboarding** (`onboarding.*`, 54 slots) and **Connect Telegram** (`connect_telegram.card.*`, 23 slots, the link card only). Text is the code's text, which already passed the pixel test; tab titles are the references' (`Zeph — Onboarding`, `Zeph — Sign in`, `Zeph — Sign up`).
  - Web: `/onboarding`, `/sign-in` and `/sign-up` read Copy on the server (`loadCopy`), take title and description through `pageMetadata`, and show `SiteLoadFailed` when Copy can't be read. `AuthLayout` takes `copy` and `page`; `OnboardingFlow` takes `copy`. `LocationFields`, `CheckInFrequencyPicker`, `OnboardingProgress` and `OnboardingStepFrame` take their words from the page that shows them. The Terms line keeps its two links as `{terms}` and `{privacy}`, filled by the new `fillPlaceholderParts` (`lib/copy.ts`). The wordmark and its home-link label are Shared's slots.
  - The Telegram link card (`TelegramConnectionCard`) reads Copy too, because onboarding's last step shows it. Its slots sit in a Connect Telegram tab, their one home (CONTEXT: a slot has one home); issue 05 adds the rest of that page. The expiry line has one and many slots, so one minute left now reads "1 minute". `/connect-telegram` gives the card its slots and shows `CopyLoadFailed` (the couldn't-load block without its own `<main>`, inside the Dashboard frame) when Copy can't be read.
  - `pickCopy` (`lib/copy.ts`) sends a client component only the slots it shows, as issue 02 did for the header.
  - `LoadFailed` takes an optional `retryLabel`; website pages word it from Copy, admin pages keep "Try again".
- Decisions:
  - **Copy reaches onboarding as a prop, not a TanStack Query hook.** The PRD says client components get Copy through a query hook. Onboarding reads Copy on the server instead and hands the client flow its slots. Reason: the page needs Copy on the server anyway (title, description, error state), and a hook would need a hard-coded "loading Copy" state, the one place web code would hold words. The PRD now notes this.
  - **Sign-in and sign-up have their own tab.** The PRD's tab list has none for them; the issue says "the sign-in/sign-up slots in their tab".
  - The reasons group keeps the reference's screen-reader name, "What brings you here", as its own slot (`onboarding.intentions.choices_label`), apart from the heading's "What brings you here?".
  - Onboarding and sign-in/up page descriptions are new wording (the references have titles only); Admins can change them.
- Left for later:
  - `ProfileForm` (Account) and `UserCheckInSettingsPanel` (Check-ins) now pass their own words to `LocationFields` and `CheckInFrequencyPicker`; issue 07 makes those Copy. Onboarding has its own location and frequency slots; issue 07 should decide whether Account and Check-ins share them (one home) or keep their own.
  - The Connect Telegram page's heading and tab title are still in code (issue 05).
  - Environment: Docker's disk was full at the first `make restart`; removing about 40 unused untagged images freed 6 GB.

### Evidence per criterion

1. Only Copy text: `OnboardingFlow.test.tsx` "shows only Copy text on every step, apart from Platform Settings" (all six steps with marked Copy, the Telegram card included, screen-reader labels checked by `wordsNotFromCopy`); `AuthLayout.test.tsx` "shows only Copy text around the Clerk form on sign_in/sign_up"; `TelegramConnectionCard.test.tsx` only-Copy tests for ready, compact ready, waiting, connected (with and without username), expired, linked elsewhere and couldn't create. What is not Copy, as the issue allows: the Clerk form's text, the Platform Settings words (AI notice, reason choices, User Memory explanation) and the couldn't-load block shown when Copy itself fails.
2. Reason choices: `OnboardingFlow.test.tsx` "shows an Admin's changed question, with the reason choices still from Platform Settings"; live run: the eight choices matched `platform_settings` and the pick saved as `onboarding_reasons = ["Being more present"]` on the User.
3. Copy page tabs: `tests/test_copy.py::test_admin_sees_each_tab_with_slots_in_page_order` (every tab's keys in seed order); live: tabs read Landing, Pricing, How it works, Sign in and sign up, Onboarding, Connect Telegram, Shared.
4. Pixel test (fixture dev server, `STATE_USER` session, after the last rebase): `PASS Onboarding 0.12%, height 4302 vs 4302`, `PASS M-Onboarding 0.06%, height 4681 vs 4681`; Landing, M-Landing, HowItWorks, M-HowItWorks, Account, M-Account, CheckIns, M-CheckIns all PASS. Sign-in pages never reach `networkidle` on Clerk's dev scripts (known since the redesign, on main too), so they ran on a one-off scratch copy of `compare.cjs` that waits for `load` plus 5 s, otherwise unchanged: `PASS Login 0.18%`, `PASS M-Login 1.62%` (Clerk card masked). `Signup` gives `FAIL 12.40%, height 885 vs 800` and `ConnectTelegram` / `M-ConnectTelegram` `FAIL 2.60% / 2.15%`: the same numbers main gives (checked with main's sign-in code in place) and the FAILs accepted in the redesign (Clerk's taller dev sign-up form; builder notes in the Connect Telegram baselines).
5. Checks (after the last rebase): `ruff check` All checks passed!, `ruff format --check` 506 files already formatted, `mypy src` no issues in 188 files, `pytest -n auto` 1332 passed; `pnpm lint` clean, `pnpm format:check` all files use Prettier code style, `pnpm typecheck` clean, `pnpm test` 122 files, 779 passed; `pnpm build` compiled successfully. New tests: `auth-pages.test.tsx`, `onboarding/page.test.tsx`, `connect-telegram/page.test.tsx`, `AuthLayout`, `OnboardingFlow`, `TelegramConnectionCard`, `OnboardingStepFrame`, `lib/copy.test.ts` (`fillPlaceholderParts`, `pickCopy`).
6. /run (worktree stack, real data): as an Admin, the Onboarding tab's "What brings you here: heading" changed to "What brings you to Zeph?" and saved ("Saved. It shows on the next page load.", `03-screenshots/copy-onboarding-saved.png`). The account was then made a plain User who hadn't onboarded; `/` sent it to `/onboarding` (title "Zeph — Onboarding"), step 2 read "What brings you to Zeph?" with "Step 2 of 6" at 1280 and 390 (`onboarding-question-1280.png`, `onboarding-question-390.png`), and it finished on "Let’s meet on Telegram." with the card's words from Copy (`onboarding-telegram-1280.png`). Signed out, `/sign-in` and `/sign-up` showed their Copy titles, descriptions and Terms line (`sign-in-1280.png`, `sign-in-390.png`); `/connect-telegram` showed the card from Copy (`connect-telegram-1280.png`). An earlier edit ("What made you come today?") survived a rebuild's re-seed.

## Completion

- Completed: 2026-11-19
- Commit: <filled in after the merge>
