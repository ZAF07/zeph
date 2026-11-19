# 16 — Redesign: public Pricing page

Status: in-progress

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

- [ ] `/pricing` shows the three plans, signed out and signed in, and needs no sign-in.
- [ ] Signed in, clicking "See pricing" on How It Works opens the pricing page (checked in `/run`).
- [ ] All pricing links point to `/pricing`; tests cover the links and the public route.
- [ ] Landing, M-Landing, HowItWorks and M-HowItWorks still PASS, and every signed-in route is still protected (checked in `/run`).
- [ ] `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` pass, and `/code-review` has been run.

## Comments
