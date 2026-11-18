# 06 — Redesign: sign in and sign up

Status: completed

Lane: B. README slice: 8.

## Parent

`.scratch/redesign/PRD.md`

## What to build

Rework the auth layout to `Login`, `Signup` and `M-Login`, with the `auth-archway.jpg` CSS from the README. The card is the Clerk widget, styled through the existing Clerk appearance settings to match the reference card's colours, radii, type and button, with `data-clerk-card` on its wrapper. The layout, image, header and legal lines must match exactly. Clerk stays inside the auth files.

This issue owns the public header the Landing page will reuse (issue 08), if the references share it.

Refs: `Login`, `M-Login`, `Signup`. Clerk card masked, 8% allowed.

## Acceptance criteria

- [x] All three refs PASS. — Login and M-Login PASS. **Signup FAILs (12.40%) and Zaf accepted this on 2026-11-18**; the reason is below.
- [x] Sign-in and sign-up still work end to end against real Clerk in the `/run` check.

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

- [x] `node design/compare.cjs <this issue's refs>` prints PASS for each ref (pasted below), where the issue lists refs. — Signup is the accepted FAIL.
- [x] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` all pass (output pasted).
- [x] A `/run` check on the running stack with **real** data shows the pages work, and long names or many rows fit, or any that don't are reported.
- [x] Reported: anything the agent was unsure about or chose itself, and any existing test changed and why.
- [x] `/code-review` run, and findings fixed or answered.

## Comments

- 2026-11-18 — Implemented on branch `redesign-06-sign-in` (own worktree, ports 3020/8020). The evidence is below.

**Asked and decided with Zaf.**
- **Google sign-in stays, so Signup is an accepted FAIL.** The Clerk instance has "Continue with Google" turned on. Clerk then draws the Google button and an "or" line, and the `Signup` design draws neither. That makes the sign-up card about 85px taller than drawn. The card is masked, but everything below it moves down, and with `left bottom/cover` the archway picture moves too. Login passes because there the Google rows take about the same room as the drawn password field and "Forgot password?" link. Hiding Clerk's "Development mode" badge (it never shows with live keys) only gets Signup to 9.54%, so that was not done.

**Built.**
- `AuthLayout` is rebuilt from `Login`/`Signup`/`M-Login`:
  - the `auth-archway.jpg` background CSS is copied exactly at both widths;
  - min-height is 800/920;
  - the card wrapper carries `data-clerk-card` and holds the eyebrow ("Welcome back" / "Get started") and the Clerk form;
  - the Terms/18+ line and the AI companion line sit outside the card.
- New `PublicHeader` with the Zeph wordmark, an optional `nav` and `actions`. It is the header issue 08 reuses. It keeps the reference's empty `<nav>`, because the 48px gap after the wordmark sets where the header sits.
- Clerk sits flush (`options.elevation: "flush"`, no logo) and is styled from the reference card in `clerk-appearance.ts`:
  - title 32px cream, subtitle 14px soft;
  - 46px inputs with a 10px radius and the line-strong border;
  - cream pill Continue, outlined pill Google button, 13px footer.
- Clerk's titles, subtitles and email placeholder come from the references, in the new `clerk-localization.ts`.
- `ZephLogo.tsx` was deleted, since nothing uses it any more.

**Pixel test** (production web container, after rebasing on main with issue 07):
```
PASS  Login                              0.19% differs, height 800 vs 800 (Clerk card masked)
PASS  M-Login                            1.62% differs, height 982 vs 984 (Clerk card masked)
FAIL  Signup                             12.40% differs, height 885 vs 800 (Clerk card masked)
```
- The test was run against the production build, not `NEXT_PUBLIC_DESIGN_FIXTURES=1 pnpm dev`. In `next dev`, Clerk's dev-only "catch-all route" check fetches a page and never reads the body. The page then never reaches `networkidle`, so `compare.cjs` times out.
- These signed-out pages use no fixtures. A copy of the script that waits for `load` gave the same numbers in dev.

**Checks** (after the rebase): `make check`.
- Python: ruff "All checks passed!", ruff format "487 files already formatted", mypy "no issues found in 186 source files", pytest "1319 passed".
- Web: eslint clean, Prettier "All matched files use Prettier code style!", `tsc --noEmit` clean, vitest "91 files, 582 tests passed".
- A stale `web/.next` left by the dev server gave one false tsc error. It was cleared and the web checks re-run.

**/run against real Clerk** (worktree stack, production web container):
- **Sign-in, driven by Playwright at 1280 and 390** with a Clerk test user made through the Backend API: email → password → Clerk's new-device step (`/sign-in/client-trust`, code 424242) → into the app (`/` → `/onboarding`). No sideways scroll on any step and no page errors.
- **Sign-up.** Clerk's bot protection shows Cloudflare's "Verify you are human" to automated browsers. It renders correctly inside the new card, and was not bypassed. Zaf signed up by hand in a private window (`zaf-06-test+clerk_test@example.com`, code 424242). The Clerk user was made at 15:39:40 UTC and the app's `users` row at 15:40:08.
- **Long text.**
  - An email over Clerk's 64-character limit shows Clerk's error in the danger colour, inside the card.
  - A long email on the password and code steps first ran off the card at 390. Fixed: it now wraps inside the card.
  - The six code boxes had almost no border. They now get the input border.
- All test users (Clerk and `users` rows) were deleted afterwards.
- **Seen, not fixed (not part of this change).** The first `/api/me` and `/api/platform-content` calls, about 1s after sign-up, got 401. The next load, 27s later, got 200 and made the row. This change doesn't touch tokens or redirects. Maybe worth a `/file-bug` if it shows up on the main stack.

**Chosen myself / unsure (for Zaf to confirm).**
- The phone layout switches below 900px, the same switch as the shell and Onboarding. It covers the header, section padding and alignment, card padding, min-height and the background.
- The eyebrow is AuthLayout's own markup above Clerk's header. That gives 18px from eyebrow to title, where the reference has 16px (inside the mask).
- The Continue button shows Clerk's own small arrow, not the reference's "→". Sign-in is two steps (email, then password), as Clerk does today; the reference draws both fields at once.
- Curly apostrophes are kept in "isn’t" and "can’t", as in the existing copy and in issue 04.
- The wordmark links home with the label "Zeph home", as in Onboarding.
- No existing tests changed. New tests: `AuthLayout.test.tsx`, `PublicHeader.test.tsx`.

**For issue 08.**
- `PublicHeader` only hides `nav` below 900px. The README's phone menu button and the nav panel are still to build. Pass the button in through `actions` and draw the panel under the header, or extend `PublicHeader`.

**/code-review.**
- Standards: no hard violations.
  - Fixed: the card background now uses the `bg-deep/80` token. The Clerk colours are named once (`tokenColors`). A new `outlined()` replaces the repeated `!important` border/box-shadow pair. The Clerk copy moved to `clerk-localization.ts`.
  - Answered: the background CSS strings keep their literal `#0A202C`, because the README says to copy them exactly. The empty `<nav>` stays (see above).
  - Left: `switchPrompt` and `switchLink` stay separate props.
- Spec: no missing parts apart from the accepted Signup FAIL. The points it raised are recorded above: apostrophes, 18 vs 16px, the arrow, the phone breakpoint, the issue 08 menu button.

## Completion

- Completed: 2026-11-18
- Commit: <to be filled in after merge>
