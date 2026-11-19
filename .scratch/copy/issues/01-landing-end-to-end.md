# 01 — Copy: Landing end to end

Status: ready-for-agent

Lane: A. The tracer: every other issue builds on it.

## Parent

`.scratch/copy/PRD.md`

## What to build

The whole Copy path, proved on one page. An Admin opens the new Copy page (`/admin/copy`), sees a Landing tab with Landing's slots in page order, edits some, and saves. A signed-out visitor reloads `/` and sees the new words, with the design unchanged.

- Copy store kept apart from Platform Settings (ADR-0019), seeded from its own seed file in prestart: new slots added, edited slots keep their text, a slot's name, tab, order, max length and placeholders always follow the seed, and slots gone from the seed are removed.
- Public read of all Copy (no sign-in), Admin read of the Copy page (tabs, slots, last changed by and when) and Admin save of one tab.
- Tab save is all or nothing and turned away, with a reason per slot, for: empty text, over max length, a required placeholder missing, an unknown placeholder, a slot from another tab. Plain Users are refused.
- One small pure helper fills `{name}` placeholders. Plain text only: no markdown, links or HTML read from Copy.
- Landing reads every word from Copy, including its browser tab title and search description. The page code holds no default text. If Copy can't be read, Landing shows the normal error state.
- The Copy page is one page with tabs (only Landing for now), built from the design's existing parts: a text field per slot with name, placeholders and a counter, and the card save bar. Field errors show on the failing slot.
- The design fixture API client serves the seed Copy, and the Landing seed text matches the reference exactly.

## Acceptance criteria

- [ ] Prestart seeds the Copy store; re-seeding keeps an Admin-edited slot's text and updates its name/max length/placeholders from the seed; a slot removed from the seed is gone.
- [ ] Signed out, the public read returns every slot's key and latest text.
- [ ] An Admin sees the Landing tab with slots in page order, each with name, text, max length, placeholders and last changed by/when.
- [ ] A tab save applies all its changes; empty, too long, missing placeholder, unknown placeholder and other-tab slot each turn away the whole save with an error on that slot.
- [ ] A plain User can't read the Copy page or save.
- [ ] Landing (including tab title and description) shows only Copy text; no default text in web code.
- [ ] Landing shows the normal error state when Copy can't be read.
- [ ] Backend HTTP tests, Dashboard tests and placeholder helper tests cover the above; all Python and web checks pass.
- [ ] The pixel test passes for the Landing refs at both widths.
- [ ] `/run`: as an Admin, change the Landing main heading, reload signed-out `/` and see it; try a save over max length and see it turned away on that slot.

## Blocked by

- All of `.scratch/redesign/` completed.
