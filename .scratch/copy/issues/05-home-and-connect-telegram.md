# 05 — Copy: Home, Connect Telegram and the Dashboard menu

Status: ready-for-agent

Lane: B.

## Parent

`.scratch/copy/PRD.md`

## What to build

Home and Connect Telegram read every word from Copy, including their empty, loading and web-side error messages and tab titles, each with its own tab on the Copy page. The Dashboard menu and frame words a User sees on every User page go in the **Shared** tab. Live values (e.g. a Telegram handle) use placeholders.

Not part of this issue:
- Backend rule messages are not Copy.
- The AI notice and Memory notes stay where they are until issue 08 moves them.

## Acceptance criteria

- [ ] Home, Connect Telegram and the Dashboard menu show only Copy text, with placeholders filled; no default text in web code.
- [ ] Their empty, loading and web-side error messages are Copy.
- [ ] The Copy page shows Home and Connect Telegram tabs and the menu slots in Shared, slots in page order.
- [ ] Seed text matches the references; the pixel test passes for these pages at both widths.
- [ ] Tests cover the converted pages and states; all Python and web checks pass.
- [ ] `/run`: as an Admin, edit a Home heading and a menu item, then see both as a signed-in User.

## Blocked by

- `.scratch/copy/issues/01-landing-end-to-end.md`
