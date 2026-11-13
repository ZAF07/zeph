# 22 — Archiving a category that a setting uses silently stops memories being saved

Status: completed

## Parent

`.scratch/mvp/PRD.md` (found after closing out `issues/archive/07-admin-memory-categories.md`)

## Before deciding on a fix

When this issue is picked up, run `/grill-with-docs` first to decide the solution. Do not pick a fix before that. Ideas so far, none chosen:

- Warn the Admin (page and/or API) when they archive a category that a setting points at.
- Refuse the archive until the setting points at another category.

## Decision (grill, 2026-11-13)

- Keep archiving categories (ADR 0004: it's the safe stand-in for delete). Removing it was considered and rejected.
- Refuse to archive a category that any of the three category settings names. The settings aren't Admin-editable (seed only; a rename carries them along), so "repoint first" is not possible for an Admin.
- These are called **Required Memory Categories** (see `CONTEXT.md`). A category is Required when one of `CATEGORY_NAME_SETTINGS` names it; no stored flag. Rename and edit stay allowed.
- Archiving a non-Required category is unchanged: it keeps its items, gets no new ones, and its items leave replies.
- `set_archived` refuses to archive a Required category (new error); the admin API returns 409 with a clear message, e.g. "Goals is a Required Memory Category (used by onboarding and the Home page), so it can't be archived." Restore is always allowed.
- Admin page: keep the Archive button; on 409 show the API's message. No `required` field in the list API.
- No migration for a Required category that's already archived (won't happen); the onboarding warning log stays as a safety net.
- No ADR: small, easy to reverse.

## Symptom

Three platform settings name a Memory Category:

| Setting | Seeded category | What goes there |
| --- | --- | --- |
| `onboarding_name_memory_category` | Life details | "Goes by Rin" |
| `onboarding_reasons_memory_category` | Goals | "What brings you here" answers |
| `home_goals_memory_category` | Goals | Shown on the Dashboard home as "What you're working toward" |

For the two onboarding settings, only **active** categories are looked up when saving. If an Admin archives one of them:

- **Expected:** the Admin is told it's in use, or the answers still land somewhere.
- **Actual:** the archive goes through like any other. From then on, every User who finishes onboarding (or answers again) loses those answers. They are never saved. The backend logs `No active Memory Category for an onboarding answer`, but no User or Admin sees anything.

Answers saved before the archive are kept. There is no crash.

The Home setting is different: it reads archived categories too, so the Home card keeps showing existing goals. But no new goals can reach it, because conversations never save into an archived category. The card quietly stops updating.

## Repro

Deterministic.

1. As an Admin, open `/admin/memory-categories` and archive **Goals**.
2. As a User with User Memory on, finish onboarding with some "What brings you here" answers.
3. Open the User's Memories page: only "Goes by …" is there. The reasons were not saved.

The same happens for Life details (the name is lost). With Goals archived, the Home "What you're working toward" card also stops getting new items.

## Suspected location

- `src/companion/core/user_memory.py:120-153`: `remember_onboarding` only looks among active categories, and only logs a warning on a miss.
- `src/companion/core/memory_categories.py`: `set_archived` doesn't check `CATEGORY_NAME_SETTINGS`.
- `src/companion/core/home.py:113-124`: reads the Home goals category by name, archived ones included.

## Acceptance criteria

- [x] Solution decided with `/grill-with-docs`, and recorded here
- [x] Archiving a category a setting uses no longer silently loses answers
- [x] A test covers the fixed behaviour (seam 1, plus seam 3 if the admin page changes)
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Comments

- 2026-11-13: Done. `MemoryCategoryService.set_archived` raises `RequiredMemoryCategoryError` when any category setting names the category (`PLACE_USING_CATEGORY_SETTING` is the single list; `CATEGORY_NAME_SETTINGS` is built from it). The admin API turns it into 409 with the message; the admin page shows that message. Restore, rename and edit unchanged.
- Evidence: tests `test_a_required_category_cant_be_archived_so_onboarding_answers_are_kept`, `test_a_renamed_required_category_still_cant_be_archived` (seam 1), `shows why a Required Memory Category can't be archived` (seam 3). `make check`: ruff, mypy, 466 pytest, eslint, prettier, tsc, 299 vitest all pass.
- /run (worktree stack, port 3010, Admin session): clicking Archive on Goals showed "Goals is a Required Memory Category (used by onboarding and the Home page), so it can't be archived."; on Life details "… (used by onboarding) …". Both stayed active in the DB. "What helps" still archived and restored normally. No page errors.

## Completion

- Completed: 2026-11-13
- Commit: 3d4494a (Refuse to archive a Required Memory Category), merged to main in 560066b (Merge MVP issue 22)
