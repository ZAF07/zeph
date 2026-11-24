# 01 — Prompts & models cards fold, with settings and prompts in their own boxes

Status: ready-for-agent

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

- [ ] Each service on Prompts & models is a folding card showing name, description and "runs when" tag when folded.
- [ ] The first card starts open; the others start folded; several can be open at once.
- [ ] Expand all / Collapse all work as on Needs and Moves.
- [ ] Inside a card, model & settings and prompts sit in their own boxes.
- [ ] Saving, discarding and save errors work as before.
- [ ] Only existing components and styles are used.
- [ ] `AdminPrompts` reference and baseline are updated, and `node design/compare.cjs` passes for it.
- [ ] Tests cover folding and the first-card-open start; `pnpm lint`, `pnpm format:check`, `pnpm typecheck` and `pnpm test` pass.
- [ ] A `/run` as an Admin shows folding, expand/collapse and a save working on the real page.

## Blocked by

None - can start immediately

## Comments
