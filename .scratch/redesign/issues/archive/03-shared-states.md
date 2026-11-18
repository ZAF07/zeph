# 03 — Redesign: shared state parts

Status: completed

Lane: B. README slice: 10 (moved early so both lanes can use it).

## Parent

`.scratch/redesign/PRD.md`

## What to build

Turn every part on the `States` sheet into a reusable part: the empty, loading, error (with Try again), saved and confirm parts (confirm dialog included). Also turn the orange "To build" tag and the save bar states shown there into reusable parts. Each later issue uses these instead of making its own.

Replace the old-theme versions of these parts used by current pages where it's a straight swap. Don't re-layout those pages here.

Refs: `States` has no route, so there's no pixel test. Add a fixture-mode-only preview route that renders the sheet, and screenshot it next to `baseline/States.png`. Report the difference and the diff image. Don't add it to `routes.json`.

## Acceptance criteria

- [x] Every part on the `States` sheet exists as one reusable part, with the copy and styles from the reference.
- [x] Preview screenshot next to the baseline, with the difference reported.
- [x] Tests: Try again calls its handler; the confirm dialog's confirm and cancel do what they say and are reachable by keyboard.
- [x] The preview route is reachable only in fixture mode.

## Blocked by

- `.scratch/redesign/issues/01-foundations.md`

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

- 2026-11-18 — Implemented on branch `redesign-03-shared-states` (own worktree, ports 3020/8020). Evidence below.

**Parts** (`web/src/components/`, one per file, each with a test): `EmptyState` (dashed, title, sentence, optional action), `AttentionCard` (orange, Home before Telegram), `PausedNotice` ("Memory is off" / "Check-ins are paused"), `LoadingPanel` (`banner` and `card` shapes, `role="status"` + label), `LoadFailed` (restyled in place, same props, so every page using it swapped), `SaveFailedNote`, `SavedNote`, `ConfirmDialog` (native `<dialog>` with `showModal()`, role `alertdialog`, safe choice first, Escape = cancel; `modal={false}` draws it in place for the sheet), `PillLink` (pill link with the hidden arrow), `ToBuildTag`. The pill buttons in `button-styles.ts` (`primaryButton`, `secondaryButton`, `dangerButton`, `confirmDangerButton`) now match the sheet, including the disabled "Saving…" look.

**Save bar.** Read "the save bar states shown there" as the save states the States sheet draws: the "Saving…" button, Saved and couldn't-save notes. The full save bar (Unsaved changes tag, Discard, Save) is issue 12's ("the save bar with all its states … as reusable parts"). The spec reviewer agreed.

**Straight swaps.** 25 old dashed empty boxes became `EmptyState`. 13 old save-failed notes became `SaveFailedNote`. 3 old saved notes became `SavedNote`. Not swapped, because they are not straight swaps: loading placeholders (different shapes), the type-DELETE `DeleteConfirmation` (swapping it for the dialog would change behaviour), `OnboardingGate`'s untitled error, the two `<h1>` "not found" boxes, and boxes with no title. Removed the `bg-white` override on the secondary button in `OnboardingGate` and `CheckInsSettings`: with the new button it hid the text.

**Pixel test.** Preview route `/design-preview/states` (`notFound()` unless `env.designFixtures`; not in `routes.json`). Screenshot with `compare.cjs`'s own logic pointed at that path (one-off copy in the scratchpad, `STATE_USER` session), after rebasing on main:
```
PASS  States                             0.05% differs, height 2176 vs 2176
```
Diff image: `web/design/.diff/States.png` (git-ignored). The first run gave `FAIL 1.88%, height 2198 vs 2176`. That traced to two causes. First, the whole app rendered in the system font. `layout.tsx` put the Outfit variable on `<body>`, but `--font-sans` is worked out at `<html>`, so it came out empty. Zaf approved moving it to `<html>` in this branch (a fix to issue 01's setup). There is a test that is red without it and green with it (`src/app/layout.test.tsx`). Second, the "Where this applies" rows are 45px in the reference (`content-box`), so they got `box-content`. `Dashboard` / `Dashboard--menu-folded` still FAIL (11.92% / 13.38%, was 12.33% / 13.79%), because Home isn't built yet.

**Phone and modal (real Chromium, fixture server).** At 390px the sheet has no sideways scroll. As a modal, the dialog is centred: 358px wide with 16px gutters at 390, 460px at 1280. Focus opens on "Keep them", Tab moves to "Delete all memories", and Escape fires `cancel` once. The backdrop is the browser default, because the design draws none.

**Preview only in fixture mode.** `page.test.tsx`: not found when off, the sheet when on. In the production web container (real data), signed in, `/design-preview/states` gave HTTP 404.

**Checks** (web, after rebase): `pnpm lint` clean, `pnpm format:check` "All matched files use Prettier code style!", `pnpm typecheck` clean, `pnpm test` 84 files / 518 tests passed.

**/run with real data** (production web container, real test Admin):
- `/memories` showed the new `EmptyState` "Zeph hasn’t remembered anything yet" with Open Telegram, in Outfit, at 1280 and 390, with no sideways scroll.
- `/admin/check-in-kinds` with its data call failing (Playwright route) showed `LoadFailed` "Couldn’t load Check-in Kinds" in the drawn style. With the backend back, Try again loaded the kinds.
- With every call failing, `OnboardingGate`'s error showed. Its Try again is now readable (text `#EAF2F3` on transparent; before, it was on white).
- `/admin/persona`: a real save showed `SavedNote` "Saved. Zeph uses it from the next message.". A failed save showed `SaveFailedNote` "Couldn’t save the Persona. Zeph keeps using the last saved version.", with the typed text still in the box.
- The run's keyboard edits landed mid-text and saved a damaged Persona in this worktree's own database. It was restored from the seed (`platform_settings.yaml`): value equal to the seed, `updated_at` back to the seed time, `updated_by` null. Main's database was not touched.
- Long text: the longest swapped sentences (Safeguard Events, Memories) wrap inside the box. Nothing overflows.

**Chosen myself / unsure.**
- `PillLink` and `primaryButton` keep their own text colour on hover. The page-wide `a:hover { color: cream }` from the reference would make cream-on-cream text vanish. This uses colours already in the part; no new value.
- The modal dialog's width on a phone is `calc(100% - 32px)`, from the README's 16px dashboard gutter. It is centred by the browser (`m-auto`).
- `confirmDangerButton` is now the outline danger button, as drawn on the dialog. So existing confirm flows lose their filled red button. `compactSecondaryButton`, `quietButton` and `deleteIconButton` are not on the sheet and still use old-theme colours (`compactSecondaryButton` is unreadable on dark, as on main since issue 01). They are left for the table and card issues.
- The "To build" empty state for admin Plans (issue 14) isn't drawn on the States sheet. Issue 14 will combine `EmptyState` with `ToBuildTag`, or ask.
- `docker compose build web` failed twice in `next/font` (`Cannot read properties of null (reading '1')` while reading the Google Fonts URLs), then passed on retry. It is a flaky Google Fonts fetch, not this change.
- Docker's disk was full, so the worktree backend couldn't start. Ran `docker builder prune` (20.5 GB of unused build cache only; no volumes, images or containers).

**Existing tests changed.** None. New jsdom shim in `vitest.setup.ts` for `HTMLDialogElement.showModal`/`close`.

**/code-review.**
- Standards: tests added for every new part, the `confirmDangerButton` alias explained, and the other smells answered (the `modal` prop is how the sheet draws the dialog; the old-theme compact, quiet and delete-icon buttons belong to later issues).
- Spec: all five decisions judged reasonable. The unused `isWorking` prop was removed. Focus-on-open was checked in Chromium, because jsdom can't. The app-wide button restyle is intended and noted above.

## Completion

- Completed: 2026-11-18
- Commit: merge `b1fd305` into main (branch `redesign-03-shared-states`: `91565f7` shared state parts, `dd51813` code-review fixes, `5dd2a4f` evidence and archive)
