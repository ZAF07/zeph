# 16 — Redesign: public Pricing page

Status: completed

Lane: B. Follow-up to issue 08.

## Parent

`.scratch/redesign/PRD.md` (follow-up to `.scratch/redesign/issues/archive/08-public-pages.md`)

## Problem

Pricing links point to `/#pricing`. A signed-in User at `/` always gets Home, and the server never sees the `#pricing` part. So a signed-in User who clicks "See pricing" on How It Works, or Pricing in the public header or footer, lands on Home, which has no pricing section.

## What to build

Decided with Zaf on 2026-11-19: a public `/pricing` page that everyone can reach.

- **Page.** `/pricing` shows the site header, Landing's pricing section exactly as drawn (intro and three plans), and the site footer. There is no reference file for this page, so it reuses the Landing parts unchanged.
- **Links.** Every pricing link goes to `/pricing` for everyone: the public header nav, the phone menu, the footer's Product column and How It Works' "See pricing".
- **Routing.** `/pricing` is public in the middleware.

Landing keeps its drawn pricing section at `/#pricing`.

## Acceptance criteria

- [x] `/pricing` shows the three plans, signed out and signed in, and needs no sign-in.
- [x] Signed in, clicking "See pricing" on How It Works opens the pricing page (checked in `/run`).
- [x] All pricing links point to `/pricing`; tests cover the links and the public route.
- [x] Landing, M-Landing, HowItWorks and M-HowItWorks still PASS, and every signed-in route is still protected (checked in `/run`).
- [x] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` pass, and `/code-review` has been run.

## Comments

- 2026-11-19: implemented on branch `redesign-16-pricing-page` in its own worktree (ports 3020/8020/5452). The evidence is below.

**Built.**
- `app/pricing/page.tsx` renders the new `Pricing` component: `SiteHeader`, `LandingPricing` unchanged, then `SiteFooter`.
- The Pricing entry in `siteNavLinks` is now `/pricing`. That one list feeds the header nav, the phone menu and the footer's Product column.
- How It Works' "See pricing" now links to `/pricing`.
- `/pricing` is added to `lib/auth/public-routes.ts`.
- Landing still renders its pricing section with `id="pricing"`.
- Tests:
  - new: `Pricing.test.tsx` (three plans, sign-up links, header, footer link);
  - updated: `public-routes.test.ts` (`/pricing` public), `SiteHeader.test.tsx` and `HowItWorks.test.tsx` (the pricing href is now `/pricing`). These were changed because the link they check changed.

**Checks.**
- eslint clean, Prettier "All matched files use Prettier code style!", `tsc --noEmit` clean, vitest "97 files, 613 tests passed".
- No Python changed.

**Pixel test** (production web container): the link changes left the drawn pages as they were.
```
PASS  Landing       0.03% differs, height 4228 vs 4228
PASS  M-Landing     0.04% differs, height 6099 vs 6099
PASS  HowItWorks    0.03% differs, height 2293 vs 2293
PASS  M-HowItWorks  0.02% differs, height 3770 vs 3770
```
`/pricing` has no reference file, so it has no pixel ref. It reuses the Landing parts unchanged, as decided with Zaf.

**/run** on the worktree stack, production web container, real Clerk User via `design-sessions.sh`:
- **Signed out and signed in, at 1280 and 390:**
  - "See pricing" on How It Works → `/pricing`, showing Free, Plus and Pro.
  - The header nav Pricing link (1280) → `/pricing`.
  - The footer Pricing link (1280) → `/pricing`.
  - The phone-menu Pricing link (390) → `/pricing`, and the menu closes.
  - No sideways scroll and no page errors.
- **By eye:** at 1280 and 390, the header, then the pricing section as on Landing, then the footer.
- **Signed out:** `/memories`, `/check-ins`, `/account`, `/connect-telegram`, `/onboarding`, `/admin`, `/admin/users` and `/admin/persona` all → `/sign-in`.
- **Signed in:** `/` still shows Home ("Good morning, Run check.").

**/code-review.**
- **Standards:** no hard violations.
  - Answered: `SiteHeader` sits straight on the page instead of in a hero. That's the agreed layout, checked by eye.
  - Left: the repeated test selector line in `Pricing.test.tsx` and `Landing.test.tsx`. Each test covers its own page.
- **Spec:** nothing missing.
  - Fixed: the `SiteFooter` TSDoc now says "the public pages".
  - Noted, outside this issue: Conversations (`/#conversations`) and FAQ (`/#faq`) have the same signed-in problem. A signed-in User who clicks them lands on Home.

## Completion

- Completed: 2026-11-19
- Commit: merge `e61ab0f` into main (branch `redesign-16-pricing-page`: `e1d4b93` public /pricing page and links, `d84ec46` code-review fix, `a4e9f51` evidence and archive)
