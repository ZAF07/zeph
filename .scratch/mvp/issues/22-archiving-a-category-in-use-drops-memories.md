# 22 — Archiving a category that a setting uses silently stops memories being saved

Status: needs-triage

## Parent

`.scratch/mvp/PRD.md` (found after closing out `issues/archive/07-admin-memory-categories.md`)

## Before deciding on a fix

When this issue is picked up, run `/grill-with-docs` first to decide the solution. Do not pick a fix before that. Ideas so far, none chosen:

- Warn the Admin (page and/or API) when they archive a category that a setting points at.
- Refuse the archive until the setting points at another category.

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

- [ ] Solution decided with `/grill-with-docs`, and recorded here
- [ ] Archiving a category a setting uses no longer silently loses answers
- [ ] A test covers the fixed behaviour (seam 1, plus seam 3 if the admin page changes)
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`
