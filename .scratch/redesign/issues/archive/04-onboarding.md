# 04 — Redesign: Onboarding

Status: completed

Lane: B. README slice: 7.

## Parent

`.scratch/redesign/PRD.md`

## What to build

Restyle Onboarding to `Onboarding` and `M-Onboarding`. The app still shows one step at a time, with the same steps and the same saving as now. In fixture mode, `?design=all-steps` renders all six steps stacked with the dashed separators, for the test. Fixture data goes in the onboarding fixture file.

Refs: `Onboarding`, `M-Onboarding`.

## Acceptance criteria

- [x] Both refs PASS.
- [x] One step at a time outside `?design=all-steps`, and the steps save as before (the existing tests still pass).

## Blocked by

- `.scratch/redesign/issues/03-shared-states.md`

## Rules for every redesign issue

- Read `web/design/README.md` in full, then every reference file named here at both widths, before coding. The README wins on look, copy and behaviour. Where it and this issue differ, stop and ask. Its "When to stop and ask" list applies.
- Build so the computed styles equal the reference's inline styles. Take copy, sizes, colours, gaps and image CSS from the reference, never from memory. Use only the tokens (arbitrary values like `gap-[22px]` where no token exists).
- Never change anything in `web/design/` (`LIMIT`, masks, baselines, references), except the one image swap and baseline rebuild in issue 01.
- Own worktree (`make worktree-setup`), own branch, own PR. Run the pixel test with `BASE_URL=http://localhost:$WEB_PORT`, `NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev`, and the two session files from issue 01's script.
- **Parallel work.** Two agents work at once. Put this issue's sample data in its own fixture file for its page area, and don't edit another area's file. Only issue 01 edits the theme, font, fixture switch and pixel-test setup. Only issue 02 edits the sidebar and menu. Only issue 08 edits the middleware. If you need a change in one of those, stop and ask.
- Use the shared state parts from issue 03 (empty, loading, error, saved, confirm) for every state this issue's pages show (from issue 04 on).
- Existing behaviour, API calls, Clerk logic and tests stay as they are. Update a test only where the markup it checks has changed.
- Before the PR: `git fetch origin && git rebase origin/main`, then re-run this issue's pixel test and checks.

## Done when (for every redesign issue)

- [x] `node design/compare.cjs <this issue's refs>` prints PASS for each ref (pasted below), where the issue lists refs.
- [x] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` all pass (output pasted).
- [x] A `/run` check on the running stack with **real** data shows the pages work, and long names or many rows fit, or any that don't are reported.
- [x] Reported: anything the agent was unsure about or chose itself, and any existing test changed and why.
- [x] `/code-review` run, and findings fixed or answered.

## Comments

- 2026-11-18 — From issue 02: the `getPlatformContent` fixture lives in `web/src/lib/design-fixtures/shell.ts`. Only `ai_notice_short` (the sidebar line) and `message_retention_days: 30` are filled in. If this page shows the other fields, fill them from its reference there; it is the shared shell fixture, so mention it in the issue.

- 2026-11-18 — Implemented on branch `redesign-04-onboarding` (own worktree, ports 3020/8020). Evidence below.

**Asked and decided with Zaf.**
- Check-ins step follows the design: quiet hours are a sentence only ("Never in your quiet hours, in your time zone: 10:00 PM to 7:30 AM"), with no From/Until boxes. Onboarding still saves the backend's default quiet hours. Users change them on the Check-ins page.
- Hello step keeps today's rule: Continue stays greyed out until the name and tick are done, and the hint shows. Only the `?design=all-steps` sheet draws Continue cream, with no hint and buttons that do nothing.
- Telegram step: `TelegramConnectionCard compact` draws the loading (`LoadingPanel`) and ready states as the small card. The other states (waiting, connected, expired…) keep the old look for issue 09.
- `fixture-client.ts` (issue 01's file) now applies `shellFixtures` first, so an area file can replace `getMe`. `onboardingFixtures(queryString)` returns calls only on `?design=all-steps`: a new Alex (no name, two reasons, SG), Check-ins on, the platform wording and a Telegram link expiring in 14 minutes. Every other page still gets the shell's Alex.

**Built.** `OnboardingStepFrame` (wordmark, 560px column, dashed line between frames on the sheet), `OnboardingProgress` and `OnboardingFlow` restyled from the reference. The page reads `?design=all-steps` on the server through `hasDesignFlag`, so it works only in fixture mode. Shared state parts are used for loading (`LoadingPanel`), a failed load (`LoadFailed`) and a failed save (`SaveFailedNote`).

**Shared parts restyled from the references, so the Account and Check-ins pages change too (issues 05 and 09 should know).**
- `Switch`: 44px button, 40×22 track, 16px knob.
- `LocationFields`: native `<select>` drawn as the reference box with chevron, 13px label, 12px caption.
- `CheckInFrequencyPicker`: the Onboarding look (flex `1 1 auto`, wraps). The Check-ins page draws four equal segments, which is issue 05's job.
- The frequency label "Once a week" is now "Weekly" app-wide: every reference that shows the picker says "Weekly". The Home line, Admin schedule and Platform Settings label change with it.

**Handover from issue 02.** The `getPlatformContent` fixture in `shell.ts` was left as it is. The onboarding wording lives in `onboarding.ts` and applies only on the all-steps address, so it never leaks onto Memories or other pages. Its `ai_notice_short` matches the shell's drawn sidebar line.

**Pixel test** (after rebasing on main, fixture dev server, `STATE_USER` session):
```
PASS  Onboarding                         0.12% differs, height 4302 vs 4302
PASS  M-Onboarding                       0.06% differs, height 4681 vs 4681
```
What is left over:
- The real QR code where the reference draws a placeholder box. It is 102px in the 126px cream box, with a 12px margin as the old card had.
- The time zone option text: "Singapore (GMT+8)" against the reference's "Asia/Singapore".
- Curly apostrophes where the reference has straight ones.
- The arrow glyph.

After the rebase, `Dashboard--menu-folded` and `M-Menu` give the same 13.05% and 15.83% that issue 02 recorded, so the shell is unchanged.

**Checks** (web, after the rebase):
- `pnpm lint`: clean.
- `pnpm format:check`: "All matched files use Prettier code style!"
- `pnpm typecheck`: clean.
- `pnpm test`: 88 files, 554 tests passed.

**/run with real data** (production web container, real User session with onboarding cleared):
- At 1280 and 390, all six steps walked through. A 54-character name, all 8 reasons, a 390-character note, Check-ins on and Weekly were entered.
- Nothing scrolled sideways at either width. There were no page errors.
- The real AI notice wraps in its panel.
- The database row afterwards held the name, 8 reasons, check-ins on, `weekly`, quiet hours 22:00–07:30 (defaults), and onboarding completed.
- At 390 the QR code is hidden and the frequency picker wraps (3 + 1) as in `M-Onboarding`.
- Continue is disabled at the start, with the hint.
- With `/api/me` failing, `LoadFailed` "We couldn’t load this" showed, and Try again loaded the Hello step.
- With `PUT /api/onboarding` failing, `SaveFailedNote` showed and the flow stayed on the Memory step.
- `/onboarding?design=all-steps` on the production container shows one step (flag ignored outside fixture mode).
- The flow was re-run after the rebase on the rebuilt stack, with the same result.

**Chosen myself / unsure (for Zaf to confirm).**
- The time zone label is kept as "Singapore (GMT+8)" (existing behaviour, shared with Account), though both references show the IANA name.
- Curly apostrophes are kept ("I’m", "Let’s"), as in the existing copy and tests.
- The wordmark stays a link home ("Zeph home"), as before. The reference draws plain text.
- The Telegram step has no Back button, as drawn. Before, Back was offered after saving.
- The checkbox keeps the browser's default margin (`3px 3px 3px 4px`), as the reference does.
- The 32px → 20px side padding switches below 900px, the README's phone switch.

**Existing tests changed.**
- `OnboardingFlow.test.tsx`: the quiet-hours test now checks the sentence instead of From/Until. New tests cover one step at a time and the all-steps sheet.
- "Once a week" → "Weekly" in `CheckInsSettings`, `UserCheckInSettingsPanel`, `CheckInSchedule` and `PlatformSettingsForm` tests.
- `choose-api-client.test.ts`: a new-User-on-all-steps test, kept next to issue 02's AI notice test.

**/code-review.**
- Standards: no hard violations. Fixed: the checkbox's `aria-describedby` now points only at a hint that is shown; clearer names (`isDesignSheet`, `queryString`, `locationLabel`/`textFieldLabel` instead of names that shadowed `form-styles`); a new `OnboardingStepFrame` test. Left: the shared panel class string and the time formatters repeat once across different parts, which isn't worth a new module yet.
- Spec: nothing missing or wrong. Scope notes (no Back on Telegram, "Weekly" in Admin, shared-part restyles) are recorded above. The sheet's buttons now do nothing.

## Completion

- Completed: 2026-11-18
- Commit: merge `ec25858` into main (branch `redesign-04-onboarding`: `d07d613` Onboarding in the new look, `b5c0492` code-review fixes, `23d0846` evidence and archive)
