# 07 — Copy: Check-ins and Account

Status: ready-for-agent

Lane: B.

## Parent

`.scratch/copy/PRD.md`

## What to build

The Check-ins and Account pages read every word from Copy, including empty, loading and web-side error messages, dialogs and tab titles, each with its own tab on the Copy page. Live values use placeholders, and counts use one/many slots as in issue 06 (if 06 isn't merged yet, follow its approach).

Not part of this issue:
- The Delete My Data description and the Photo Viewing explanation stay where they are until issue 08 moves them.
- Backend rule messages (e.g. Quiet Hours validation) are not Copy.

## Acceptance criteria

- [ ] Check-ins and Account show only Copy text, with placeholders filled; no default text in web code.
- [ ] Their empty, loading, error and dialog text is Copy.
- [ ] The Copy page shows Check-ins and Account tabs, slots in page order.
- [ ] Seed text matches the references; the pixel test passes for both pages at both widths.
- [ ] Tests cover the converted pages and states; all Python and web checks pass.
- [ ] `/run`: as an Admin, edit a Check-ins heading and an Account dialog line, then see both as a User.

## Blocked by

- `.scratch/copy/issues/01-landing-end-to-end.md`

## Comments

- 2026-11-19 — From issue 03: `LocationFields` and `CheckInFrequencyPicker` now take their words from the page. `ProfileForm` and `UserCheckInSettingsPanel` pass the old words in code until this issue makes them Copy. Onboarding has its own slots for the same words (`onboarding.location.*`, `onboarding.check_ins.frequency_*`); decide whether Account and Check-ins share those (one home) or get their own.
- 2026-11-19 — From issue 05: Home's Check-ins card reads the frequency names from `onboarding.check_ins.frequency_*`, their one home for now; if they move to the Check-ins tab, move Home's reads too (`lib/home.ts` `checkInFrequencyText`, and `pickCopy` in `app/page.tsx`). Home has its own slots for "until you resume", "until {day}", "Not available on your account" and "Changed in chat · {day}" (`home.check_ins.*`); the Check-ins page still writes them in code (`pauseEndText`, `notAvailableText`, `ChangedInChatCaption`'s default). Decide one home, and drop `ChangedInChatCaption`'s default once every caller passes Copy.
