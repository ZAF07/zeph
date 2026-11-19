# 02 — Copy: Pricing and How it works, and the marketing header and footer

Status: ready-for-agent

Lane: A.

## Parent

`.scratch/copy/PRD.md`

## What to build

Pricing and How it works read every word from Copy, including their tab titles and descriptions, each with its own tab on the Copy page. The header and footer shared by the marketing pages read from Copy too, in a **Shared** tab.

This is the first time the Copy page has more than one tab, so it also gets the unsaved-changes prompt: switching tabs or leaving the page with unsaved edits asks first (reuse the existing unsaved-changes warning).

## Acceptance criteria

- [ ] Pricing, How it works and the marketing header/footer show only Copy text; no default text in web code.
- [ ] The Copy page shows Pricing, How it works and Shared tabs, slots in page order.
- [ ] Switching tabs or leaving with unsaved edits asks first; saved or no edits doesn't.
- [ ] Seed text matches the references; the pixel test passes for these pages at both widths (Landing still passes).
- [ ] Tests cover the new pages and the unsaved-changes prompt; all Python and web checks pass.
- [ ] `/run`: as an Admin, edit a Pricing slot and a footer slot, reload signed out and see both; switch tabs with an unsaved edit and get asked.

## Blocked by

- `.scratch/copy/issues/01-landing-end-to-end.md`
