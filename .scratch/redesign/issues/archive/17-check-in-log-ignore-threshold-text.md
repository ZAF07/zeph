# 17 — Check-in Log: the paused reason uses the Ignore Threshold

Status: completed

## Parent

`.scratch/redesign/PRD.md` (follow-up to `.scratch/redesign/issues/archive/10-admin-users-and-check-in-log.md`)

## What to build

Issue 10 shows paused rows with the drawn words "Three in a row went unanswered". The number is the Ignore Threshold, an Admin setting (`check_in_ignore_threshold`, 3 now), so the words go wrong when it changes. Zaf (2026-11-19): read the number from the setting, so the text says "Five in a row went unanswered" when it is 5. This needs one extra settings call on the Check-in Log page.

## Acceptance criteria

- [x] Paused rows say "<N> in a row went unanswered", with N from the Ignore Threshold setting. — `pausedReasonText` (words up to ten, digits above); running stack showed "Three…" at 3 and "Five…" at 5.
- [x] The log still shows when the settings can't load (paused rows then say something true without a number). — "Paused by ignore rule" (the totals tile's own words); tested in `CheckInLog.test.tsx`.
- [x] AdminCheckInLog and M-AdminCheckInLog still match by parts as in issue 10 ("Three" with the fixture at 3). — same numbers as issue 10 (see Evidence).
- [x] Checks pass, and a `/run` with the setting changed shows the new number.

## Blocked by

None.

## Comments

- 2026-11-19 — Evidence.

**Checks** (web): `pnpm lint` clean; `pnpm format:check` "All matched files use Prettier code style!"; `pnpm typecheck` clean; `pnpm test` 104 files, 651 tests passed.

**/run with real data** (worktree stack, real Admin session, one paused Check-in seeded): the paused row read "Three in a row went unanswered" with `check_in_ignore_threshold` = 3; after setting it to 5 in `platform_settings` and reloading, "Five in a row went unanswered". No page errors.

**Pixel test** (fixture mode, threshold 3 in the fixture), same as issue 10:
```
FAIL  AdminCheckInLog                    0.11% differs, height 837 vs 1470
FAIL  M-AdminCheckInLog                  6.32% differs, height 2238 vs 3216
FAIL  AdminPersona                       1.10% differs, height 800 vs 1672
```
Above the builder notes: AdminCheckInLog 0.08%, M-AdminCheckInLog 6.34% (the missing pill's row shifts the phone page, as in issue 10). AdminPersona unchanged at issue 12's 1.10%.

**Chosen myself.**
- The table shows the loading rows until both the log and the settings have loaded, so the reason never flips from one wording to another. If the settings fail, the log shows with "Paused by ignore rule".
- Numbers up to ten are words ("Three"), above ten digits ("12 in a row went unanswered").
- The text uses today's threshold, not the one in force when the User was paused.
- `design-fixtures/admin-forms.ts` (issue 12's file, now finished) gets `check_in_ignore_threshold: 3`, so the fixture Platform settings form shows 3 in Ignore threshold instead of blank.

**Code review** (standards and spec sub-agents): no hard violations; loading and error states each show exactly one thing. Fixed: a test that the table waits for the settings; the test helper moved below the mocks. Not changed: the setting key is written in two places (`CheckInLog.tsx` and `PlatformSettingsForm.tsx`); a shared constant would touch issue 12's form, so it is left for later.

## Completion

- Completed: 2026-11-19
- Commit: <to be filled in after merge>
