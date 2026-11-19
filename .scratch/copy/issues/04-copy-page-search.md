# 04 — Copy: search across tabs

Status: ready-for-agent

Lane: A.

## Parent

`.scratch/copy/PRD.md`

## What to build

A search box on the Copy page finds slots by their current text across every tab. Picking a result opens that slot's tab with the slot in view, ready to edit. Unsaved edits in the current tab still prompt before the tab changes.

## Acceptance criteria

- [ ] Typing part of a sentence lists the matching slots from any tab, with tab and slot name.
- [ ] Picking a result opens its tab and brings the slot into view.
- [ ] With unsaved edits, picking a result in another tab asks first.
- [ ] No matches shows the design's empty state.
- [ ] Tests cover search, jump and the prompt; all web checks pass.
- [ ] `/run`: as an Admin, from one tab, search for a sentence that lives in another tab and land on it.

## Blocked by

- `.scratch/copy/issues/01-landing-end-to-end.md`
