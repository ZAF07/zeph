# 01 — Prompts & models cards fold, with settings and prompts in their own boxes

Status: completed

## What to build

On `/admin/prompts`, each core service (Understanding, Reply Plan, Reply, Safeguard, Pattern keeping, …) becomes a folding card, the same as on the Needs and Moves pages. Today every service is an open section with no border, so the page is one long scroll and it is hard to see where one service ends.

- Each service is a `FoldingCard`. Folded, it shows the service name, its description and the "runs when" tag.
- The first card starts open. Several can be open at once. Expand all / Collapse all, as on Needs and Moves.
- Inside an open card, the parts sit in clearly split boxes:
  - **Model & settings**: model, thinking and any limits.
  - **Prompts**: the prompt and any extra prompts (grouped extra prompts stay folded groups inside).
- One save bar per card, as today.

## Decisions

- No new styles. Reuse the components and classes the Needs and Moves pages and the component references already use.
- The `AdminPrompts` design reference and its baseline image are updated to match the new layout (agreed with the user, 2026-11-24).
- First card open, the rest folded, as on Needs and Moves.

## Acceptance criteria

- [x] Each service on Prompts & models is a folding card showing name, description and "runs when" tag when folded.
- [x] The first card starts open; the others start folded; several can be open at once.
- [x] Expand all / Collapse all work as on Needs and Moves.
- [x] Inside a card, model & settings and prompts sit in their own boxes.
- [x] Saving, discarding and save errors work as before.
- [x] Only existing components and styles are used.
- [x] `AdminPrompts` reference and baseline are updated, and `node design/compare.cjs` passes for it.
- [x] Tests cover folding and the first-card-open start; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` pass.
- [x] A `/run` as an Admin shows folding, expand/collapse and a save working on the real page.

## Blocked by

None - can start immediately

## Comments

Evidence (24 Nov 2026, branch `admin-ui-01-fold-prompts`):

- Folding cards: `CoreServiceCard` is a `FoldingCard` (title, description as summary, "runs when" as a `CardTag`); `PromptsAndModels` lists them in `CardList`. Test "starts with the first service open and the others folded" checks the folded row's description and tag.
- First open, others folded, several open: tests "starts with the first service open…" and "opens a folded service when its row is clicked" (the first stays open). /run on real data: 14 cards, 1 open at start (Safeguard).
- Expand all / Collapse all: test "opens and folds every service with Expand all and Collapse all"; /run: 14 open after Expand all, 0 after Collapse all.
- Boxes: "Model & settings" group (heading over the `FieldRows` box: model, thinking, limits) and "Prompts" group (heading over the prompt editor, extra prompts and folded extra-prompt groups). Test "puts a service's model and settings and its prompts in their own groups"; /run: both groups visible in an opened card.
- Save, discard, errors: the save bar is now `CardSaveBar` (as on Moves), same note, "Saving…", "Try again" and failure text; the existing save, thinking, limit, extra-prompt, failure and refusal tests all pass unchanged. /run: switched Understanding's Thinking, "Unsaved changes" showed on its row, saved, reload showed it off; switched back and saved, reload showed it on again.
- No new styles: only `FoldingCard`, `CardList`, `CardTag`, `CardSaveBar`, `CardListLoading`, `FormSectionHeading`, `FieldRows`, `FormEditor`. The reference copies the card markup from `AdminCheckInKinds.html` (standards review confirmed).
- Reference and baseline: `AdminPrompts.html` redrawn (toolbar, Understanding open, three folded, old "About this page" note removed), baseline reshot from it. Pixel test: `PASS AdminPrompts 0.11% differs, height 1392 vs 1392`. Run with a copy of `compare.cjs` that blocks Clerk's `protect.clerk.com` probes, which never finish on this machine (inside or outside the sandbox) so `networkidle` never comes; nothing else changed. AdminPersona and AdminCheckInKinds fail on page height in the same run; their code is not in this change.
- Checks: `pnpm lint` clean, `pnpm format:check` clean, `pnpm typecheck` clean, `pnpm test` 133 files, 908 tests passed.
- /run: worktree stack, signed-in Admin, real data, 1280 and 390 (no sideways scroll), no page errors; repeated after the review fixes.
- Review: standards and spec reviews found no hard violations. Fixed: card-list loading state, `headingId` renamed `idPrefix`. Left: the Prompts group is a heading over the existing editor boxes, not one extra box around them (no new styles).

## Completion

- Completed: 2026-11-24
- Commit: 712ff7c (merge "Merge admin-ui-01-fold-prompts: Prompts & models fold into a card per service"; work in cc06764 "Fold Prompts & models into a card per service", 7dbd4f4 "Tidy Prompts & models cards after review", bac9853 "Archive admin-ui issue 01: Prompts & models fold into a card per service, verified")

