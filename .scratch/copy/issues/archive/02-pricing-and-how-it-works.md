# 02 — Copy: Pricing and How it works, and the marketing header and footer

Status: completed

Lane: A.

## Parent

`.scratch/copy/PRD.md`

## What to build

Pricing and How it works read every word from Copy, including their tab titles and descriptions, each with its own tab on the Copy page. The header and footer shared by the marketing pages read from Copy too, in a **Shared** tab.

This is the first time the Copy page has more than one tab, so it also gets the unsaved-changes prompt: switching tabs or leaving the page with unsaved edits asks first (reuse the existing unsaved-changes warning).

## Acceptance criteria

- [x] Pricing, How it works and the marketing header/footer show only Copy text; no default text in web code.
- [x] The Copy page shows Pricing, How it works and Shared tabs, slots in page order.
- [x] Switching tabs or leaving with unsaved edits asks first; saved or no edits doesn't.
- [x] Seed text matches the references; the pixel test passes for these pages at both widths (Landing still passes).
- [x] Tests cover the new pages and the unsaved-changes prompt; all Python and web checks pass.
- [x] `/run`: as an Admin, edit a Pricing slot and a footer slot, reload signed out and see both; switch tabs with an unsaved edit and get asked.

## Blocked by

- `.scratch/copy/issues/01-landing-end-to-end.md`

## Comments

- 2026-11-19 — Done (branch `copy-02-pricing-how-it-works`).
  - Seed: new tabs Pricing, How it works and Shared, after Landing. Landing's plan slots moved to the Pricing tab (`landing.pricing.*` → `pricing.*`) so prices have one home; Landing's pricing section and `/pricing` both read them. Pricing tab starts with its browser tab title and search description.
  - Web: `HowItWorks` and `/how-it-works` read Copy (error state when it can't be read). `/pricing` and `/how-it-works` get title and description through `pageMetadata` (`lib/copy.ts`), which `/` now uses too. `SiteFooter` takes `copy`; `SiteHeader` (a client component) takes only its words, from `siteHeaderWords(copy)` in `site-links.ts`, so the whole Copy isn't sent to the browser. `PublicHeader` takes the wordmark and home-link label.
  - Copy page: switching tabs with unsaved edits asks ("Switch tabs and lose your changes?"); leaving by a link asks through the existing `useUnsavedChangesWarning`, and the browser asks on reload or close.
  - Screen-reader labels (home link, open/close menu, menu name) are Shared slots too.
  - Left for later: `AuthLayout` (sign-in/up) passes literal "Zeph" / "Zeph home" to `PublicHeader` until issue 03 makes those pages read Copy. The footer's AI notice (`shared.footer.ai_notice`) is its own slot; issue 08 should check it doesn't add a second slot for the same notice.
  - Environment note: Docker's disk was full during `/run` (Postgres "No space left on device", so the Admin sign-in failed). Clearing the unused Docker build cache (6.3 GB) fixed it. The Login pixel run on a fixture dev server timed out waiting for Clerk's network to go quiet; the sign-in header markup is unchanged.

### Evidence per criterion

1. Only Copy text: `wordsNotFromCopy` (page text, icons aside, plus every `aria-label`) is empty for `Pricing.test.tsx`, `HowItWorks.test.tsx`, `Landing.test.tsx` (whole page now, header and footer included) and `SiteHeader.test.tsx` (menu closed and open). `grep` finds no literal words left in `Pricing`, `HowItWorks`, `HowItWorksStep`, `SiteHeader`, `SiteFooter`, `site-links`.
2. Tabs in page order: `tests/test_copy.py::test_admin_sees_each_tab_with_slots_in_page_order` (Landing, Pricing, How it works, Shared; each tab's keys equal the seed's order). Live: Copy page tabs in `02-screenshots/switch-prompt.png`, `copy-shared-390.png`.
3. Unsaved-changes prompt: `CopyEditor.test.tsx` "asks before switching tabs with unsaved edits, and keeps them on Keep editing", "switches tabs and drops the edits once the Admin says to", "switches tabs without asking once the edits are saved", "asks before following a link away with unsaved edits".
4. Seed text matches the references (the spec review compared every Pricing, How it works and Shared text against `Landing.html` / `HowItWorks.html`). Pixel test, fixture mode (`BASE_URL=http://localhost:3120`), after the review fixes: `PASS Landing 0.03% differs, height 4228 vs 4228`, `PASS M-Landing 0.04%, 6099 vs 6099`, `PASS HowItWorks 0.03%, 2293 vs 2293`, `PASS M-HowItWorks 0.02%, 3770 vs 3770`. `test_the_design_fixture_copy_is_the_seed_copy` keeps `seed-copy.json` equal to the seed.
5. Tests and checks: new `app/how-it-works/page.test.tsx` (Copy, metadata, error state), Pricing metadata test, `pageMetadata` tests, header/footer/How it works tests, Copy page prompt tests, `test_the_shared_tab_saves_on_its_own_and_turns_away_a_pricing_slot`. Python at `b0bea7d` (no Python changed since): `ruff check` All checks passed!, `ruff format --check` 505 files already formatted, `mypy` no issues in 189 source files, `pytest` 1330 passed. Web at `a6cb9d2`: `pnpm lint` clean, `pnpm format:check` All matched files use Prettier code style!, `pnpm typecheck` clean, `pnpm test` 119 files, 748 passed.
6. `/run` (worktree stack, signed-in Admin, Playwright): on the Pricing tab set "Plus plan: button" to "Try Plus" and saved; on Shared set "Footer: copyright" to "© 2027 Zeph" and saved (switching tabs after a save didn't ask). A signed-out browser on `/pricing` at 1280 and 390 showed the "Try Plus" button and "© 2027 Zeph" in the footer, title "Zeph — Pricing" (`signed-out-pricing-1280.png`, `signed-out-pricing-390.png`); `/how-it-works` showed the new footer, title "Zeph — How it works". With an unsaved edit on "Footer: AI notice", choosing How it works opened "Switch tabs and lose your changes?" (`switch-prompt.png`); Keep editing stayed on Shared with the edit kept; clicking Platform settings in the menu opened "Leave and lose your changes?" (`leave-prompt.png`); after Discard, switching didn't ask. Rechecked live after the review fixes: titles and both edits still showing.

## Completion

- Completed: 2026-11-19
- Commit: merge `b9af277` into main — "Merge Copy issue 02: Pricing, How it works and the marketing header and footer read every word from Copy (Pricing, How it works and Shared tabs; plans have one home in Pricing); Copy page asks before switching tabs or leaving with unsaved edits"
  - Branch `copy-02-pricing-how-it-works`:
    - `b0bea7d` Copy 02: Pricing, How it works and the marketing header and footer read every word from Copy
    - `a6cb9d2` Copy 02: one pageMetadata helper for page titles; steps listed by slot key (review)
    - `e825a40` Copy 02: evidence recorded, issue completed and archived, screenshots; CONTEXT says a Copy slot has one home
