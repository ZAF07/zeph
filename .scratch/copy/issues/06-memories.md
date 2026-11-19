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

## Comments

- 2026-11-19 — From issue 05: `ChangedInChatCaption` takes an optional `text` (with a `{day}` placeholder); `Memories` still uses its default words in code. Pass a Memories slot and, once 07 has done the same, drop the default. The Dashboard menu's "Memories" item is Shared's `shared.dashboard.memories`; Copy reaches Dashboard pages as props read on the server (`DashboardFrame`, `/`).
- 2026-11-19 — Started on branch `copy-06-memories` (worktree `ai-chat-companion-copy-06`).
  - The Memories page has no text that changes with a number today. The count goes in the "Delete all memories?" dialog body ("Zeph will forget the 1 memory…" / "…all {count} memories…"); the dialog is not in the references, so the pixel test is unaffected.
  - One/many slots sit side by side on the Copy page when their keys end `_one` and `_many` with the same start (web only; the Telegram link card's expiry pair gets it too).
