# 06 — Copy: Memories

Status: completed

Lane: B.

## Parent

`.scratch/copy/PRD.md`

## What to build

The Memories page (all its tabs) reads every word from Copy, including empty, loading and web-side error messages and its tab title, with a Memories tab on the Copy page. Text that changes with a number gets a "one" slot and a "many" slot (e.g. "1 Memory Item" / "{count} Memory Items"), and the page picks one by the number.

Not part of this issue: the Memory explanation, Photo Viewing explanation and the "Memory is paused" / "isn't available" notes stay where they are until issue 08 moves them.

## Acceptance criteria

- [x] Memories shows only Copy text, with placeholders filled; no default text in web code.
- [x] Counts pick the "one" slot for 1 and the "many" slot otherwise.
- [x] The Copy page shows a Memories tab, slots in page order, one/many slots side by side.
- [x] Seed text matches the references; the pixel test passes for Memories at both widths.
- [x] Tests cover the page, its states and one/many picking; all Python and web checks pass.
- [x] `/run`: as an Admin, edit both count slots, then see each as a User with one and with several Memory Items.

## Blocked by

- `.scratch/copy/issues/01-landing-end-to-end.md`

## Comments

- 2026-11-19 — From issue 05: `ChangedInChatCaption` takes an optional `text` (with a `{day}` placeholder); `Memories` still uses its default words in code. Pass a Memories slot and, once 07 has done the same, drop the default. The Dashboard menu's "Memories" item is Shared's `shared.dashboard.memories`; Copy reaches Dashboard pages as props read on the server (`DashboardFrame`, `/`).
- 2026-11-19 — Done (branch `copy-06-memories`).
  - Seed: a **Memories** tab (`memories.*`, 80 slots) after Home and before Connect Telegram, slots in page order: tab title and description, hero, Memory switch (on, paused, not available, screen-reader name, changed in chat, couldn't change), "Turn memory on", "forget that" line, the six tab names, loading and couldn't-load, one "couldn't delete" for every tab, then each tab's heading, lead, labels, delete names (with `{memory}`, `{story}`, `{help}`, `{day}`), dated lines (`{day}`) and empty state. Text is the code's text, which already passed the pixel test.
  - Web: `/memories` reads Copy on the server (`loadCopy`), takes its title and description through `pageMetadata` and shows `CopyLoadFailed` when Copy can't be read; only `memories.*` slots go to the browser (`pickCopy`). `Memories` and its six tab lists take `copy`; `MemoriesTabs` names tabs from `memories.tabs.<tab>`; `MemoryOffNotice` takes `turnOnLabel`; `SharedPhotoPicture` takes its box words; `ChangedInChatCaption` gets the Memories slot.
  - One/many: `countSlotKey` (`lib/copy.ts`) names the `_one` slot for 1 and the `_many` slot otherwise; the Telegram card's expiry now uses it too. On the Copy page `copySlotRows` puts a `_one` slot and the `_many` slot after it in one row, side by side when there's room and stacked on a phone (wrapping, no breakpoint).
  - After rebasing on Copy 05: Memories fills slots with 05's `fillCopy`.
- Decisions:
  - **Where the count goes.** The Memories page had no text that changes with a number. The "Delete all memories?" dialog is worded for one memory or several: the "many" slot keeps `States.html`'s text exactly ("Zeph will forget every memory it holds about you…"), the "one" slot is new ("Zeph will forget the one memory it holds about you…"), and neither takes `{count}`. Chosen by the user after the standards review found the dialog drawn in `States.html` (the reference wins on copy). An earlier version put `{count}` in both slots.
  - The Memory switch's "Not available on your account" is the Memories tab's own slot (`memories.switch.not_available`); Account, Check-ins and Home still use `notAvailableText` in code. Issue 07 should decide whether they share one home.
- Left for later:
  - `ChangedInChatCaption` keeps its default `text` for Account (`ProfileForm`); issue 07 should pass a slot and drop the default.
  - The Memory notes (`memory_note`), Memory and Photo Viewing explanations stay Platform Settings until issue 08.
  - Environment: the first two `make restart` builds failed in `next/font` (Google Fonts download inside Docker); the third built. Not a code problem: `pnpm build` passes locally.

### Evidence per criterion

1. Only Copy text: `Memories.test.tsx` "reads every word from Copy" runs `wordsNotFromCopy` (page text, icons aside, plus every `aria-label`) with marked Copy and marked data on all six tabs with things remembered and with nothing, while Memory is paused (note and button), when an Admin has Memory off, while loading, when the memories couldn't load, when a change and a delete fail with the delete-all dialog open, and in a photo's box when it can't be shown. Bare days ("12 Nov") are values, not words. `grep` finds no literal words left in the Memories components. What isn't Copy, as the issue allows: the backend's `memory_note`.
2. Counts: `lib/copy.test.ts` `countSlotKey` names the one slot for 1 and the many slot for 0, 2 and 37; `Memories.test.tsx` "words the delete all dialog for one memory with one Memory Item" and "…for several memories with more than one". `copy-slot-rows.test.ts` pairs only a `_one` slot with its own `_many` slot right after it.
3. Copy page: `tests/test_copy.py::test_admin_sees_each_tab_with_slots_in_page_order` (Landing, Pricing, How it works, Sign in and sign up, Onboarding, Home, Memories, Connect Telegram, Shared; each tab's keys in seed order); `CopyEditor.test.tsx` "shows a one slot and its many slot side by side, in one row". Live: tabs read in that order; the pair side by side at 1280 and stacked at 390 (`06-screenshots/copy-memories-pair-1280.png`, `copy-memories-pair-390.png`).
4. Seed text: the spec review compared all 80 slots against the removed web strings and the Memories references character for character (straight and curly apostrophes as before); `test_the_design_fixture_copy_is_the_seed_copy` keeps `seed-copy.json` equal to the seed. Pixel test (fixture dev server, `STATE_USER` session, after rebasing on Copy 05): `PASS Memories 0.02%, height 1060 vs 1060`, `PASS Memories--tab-about 0.01%`, `PASS Memories--tab-threads 0.01%, 858 vs 858`, `PASS Memories--tab-helps 0.01%`, `PASS Memories--tab-summaries 0.01%`, `PASS Memories--tab-photos 0.01%`, `PASS M-Memories 0.05%, 1436 vs 1436`; neighbours `PASS Dashboard`, `PASS M-Dashboard`, `PASS Account`.
5. Tests and checks (after rebasing on Copy 05): `ruff check` All checks passed!, `ruff format --check` 506 files already formatted, `mypy src` no issues in 188 source files, `pytest -n auto` 1333 passed; `pnpm lint` clean, `pnpm format:check` All matched files use Prettier code style!, `pnpm typecheck` clean, `pnpm test` 126 files, 832 passed; `pnpm build` compiled successfully. New: `app/(dashboard)/(user)/memories/page.test.tsx` (only its slots, title and description from Copy, couldn't-load block), the Memories only-Copy and one/many tests, `copy-slot-rows.test.ts`, `countSlotKey` tests, the Copy page pair test.
6. `/run` (worktree stack, rebased code, Playwright): as an Admin, on the Copy page's Memories tab, set "Delete all memories, asking first: one memory" to "Zeph forgets the single memory it holds. No undo." and "…: several memories" to "Zeph forgets every one of your memories. No undo." and saved (both rows show "Last saved … by Run check"). The account was then made a plain User. With 1 Memory Item, `/memories` (title "Zeph — Memories") → Delete all memories opened "Delete all memories? | Zeph forgets the single memory it holds. No undo. | Keep them | Delete all memories" at 1280 and 390 (`user-one-memory-1280.png`, `user-one-memory-390.png`). With 3, it read "Zeph forgets every one of your memories. No undo." (`user-several-memories-1280.png`, `user-several-memories-390.png`). No page errors. The page itself: `memories-user-1280.png`, `memories-photos-390.png`.

## Completion

- Completed: 2026-11-19
- Commit: <to be filled in after the merge>
