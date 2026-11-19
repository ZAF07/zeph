# 06 — Copy: Memories

Status: ready-for-agent

Lane: B.

## Parent

`.scratch/copy/PRD.md`

## What to build

The Memories page (all its tabs) reads every word from Copy, including empty, loading and web-side error messages and its tab title, with a Memories tab on the Copy page. Text that changes with a number gets a "one" slot and a "many" slot (e.g. "1 Memory Item" / "{count} Memory Items"), and the page picks one by the number.

Not part of this issue: the Memory explanation, Photo Viewing explanation and the "Memory is paused" / "isn't available" notes stay where they are until issue 08 moves them.

## Acceptance criteria

- [ ] Memories shows only Copy text, with placeholders filled; no default text in web code.
- [ ] Counts pick the "one" slot for 1 and the "many" slot otherwise.
- [ ] The Copy page shows a Memories tab, slots in page order, one/many slots side by side.
- [ ] Seed text matches the references; the pixel test passes for Memories at both widths.
- [ ] Tests cover the page, its states and one/many picking; all Python and web checks pass.
- [ ] `/run`: as an Admin, edit both count slots, then see each as a User with one and with several Memory Items.

## Blocked by

- `.scratch/copy/issues/01-landing-end-to-end.md`
