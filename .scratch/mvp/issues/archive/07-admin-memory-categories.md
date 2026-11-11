# 07 — Admin Memory Categories

Status: completed

## Parent

`.scratch/mvp/PRD.md`

## What to build

Admins manage Memory Categories in the admin area: add, rename, edit description, toggle "always include", archive and restore. Categories can never be deleted. Archived categories keep their existing Memory Items but are not offered for new items or category picking. Post-conversation processing and memory retrieval always read the current list.

## Design

- `docs/design/zeph-admin.html`: Memory Categories

Build order inside this issue: (1) backend API and seam 1 tests — this fixes the API contract; (2) Dashboard pages from the screens above, seam 3 tests with a mocked API client; (3) `/run` end to end. Ignore anything tagged "Later" in the design.

## Acceptance criteria

- [x] Admins can add, rename, edit description, toggle "always include", archive and restore Memory Categories; there is no delete
- [x] An archived category's existing Memory Items remain visible to the User
- [x] Post-conversation processing never assigns new items to an archived category
- [x] A newly added category is used on the next post-conversation processing and retrieval, with no restart
- [x] Seam 1 and seam 2 tests cover archive behaviour and new-category pickup
- [x] Seam 3 tests cover the admin Memory Categories page
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/04-admin-area-foundation.md`
- `.scratch/mvp/issues/06-user-memory.md`

## Comments

**2026-11-11 — implemented on branch `feat/07-admin-memory-categories`.**

Decisions:
- Admin API: `GET /api/admin/memory-categories` (in order, with `item_count` across all Users), `POST` (add, goes last, active), `PUT /{id}` (name, description, always include), `POST /{id}/archive`, `POST /{id}/restore`. There is no DELETE route; a DELETE gets 405. Missing ID → 404. Admin role checked on the router.
- Names and descriptions are trimmed and must not be blank. Names must be unique ignoring case, because the chat models name categories that way (422 with a plain message).
- Renaming a category also renames `onboarding_name_memory_category` / `onboarding_reasons_memory_category` when they named it, so onboarding answers keep being remembered. The keys now live once in `core/memory_categories.py`.
- Archived categories: not offered to post-conversation processing (adds naming them are skipped, and an update naming one keeps the item where it is), not offered to retrieval, and their items — "always include" ones too — stay out of replies. Users still see and can delete those items. This settles the issue 06 follow-up on archived "always include" categories.
- No caching: processing and retrieval read the category list on every call, so changes apply with no restart.
- Dashboard: `/admin/memory-categories` (sidebar, after Safeguard Events). The design has no rename control, so each active row has an Edit button that opens the same form as Add category. Archived rows only have Restore.

Caveats / follow-ups:
- A rename saves the category and the onboarding settings in two writes, not one transaction. If the second fails, onboarding answers for that category are skipped (logged) until fixed.
- Archiving the category an onboarding setting points at is allowed with no warning; onboarding answers for it are then skipped. Real model behaviour seen in `/run`: DeepSeek may still try an archived name (it sees old items labelled with it), and that fact is dropped.
- The always-include switch sends the row's name and description as loaded; another Admin's edit made in between would be overwritten.
- Review judgement calls not acted on: the row-action / flash markup is copied from `HelplinesManager` instead of shared.

Evidence:
- Add, rename, describe, always include, archive, restore, no delete: `tests/test_admin_memory_categories.py` (seam 1, 12 tests) and the browser run below.
- Archived items stay visible to the User: `test_an_archived_category_keeps_its_items_but_gets_no_new_ones`, `test_an_archived_always_include_category_leaves_every_reply`.
- Processing never assigns to an archived category: the same test (add skipped, category not offered) and `test_an_item_is_never_moved_into_an_archived_category` (update path).
- New category used next time with no restart: `test_a_new_category_is_used_by_the_next_processing_and_retrieval` (seam 2 tick + seam 1 webhook).
- Seam 3: `web/src/components/MemoryCategoriesManager.test.tsx` (10: lists, nothing archived, add, 422 detail, rename, switch, archive/restore, failure, empty, load error/retry); `SidebarNav.test.tsx` updated.
- `make check`: Python 140 passed; web 121 passed; ruff, ruff format, mypy, eslint, prettier, tsc clean.
- `/run` (Docker Compose, real Postgres, DeepSeek and Clerk, temporary Clerk Admin): API listed 7 seeded categories with counts; added "Work" (201); "work" refused (422); DELETE 405; non-Admin 403. A driver inside the backend container ran the real app (only Telegram and the clock swapped): with no restart, processing offered "Work", saved "Works as a product designer at a bank." into it, and the next message's retrieval offered and picked Work and the reply used it. Archiving Goals: its onboarding items stayed on the User's list; processing no longer offered Goals, DeepSeek still tried to add a marathon goal to it, and it was skipped. Browser (Chrome for Testing): add, duplicate refused in the form, rename + description, always-include switch, archive, reload, restore, no Delete button, User's Memories page, and no sideways scroll at 390px. Temporary User, checkpoints, test categories and the Clerk account were deleted afterwards.

## Completion

- Completed: 2026-11-11
- Commit: 3934b7e, review fixes 14f9d85 (merged from `feat/07-admin-memory-categories` in 4841ee3)
