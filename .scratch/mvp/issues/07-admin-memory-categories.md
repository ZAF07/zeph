# 07 — Admin Memory Categories

Status: ready-for-agent

## Parent

`.scratch/mvp/PRD.md`

## What to build

Admins manage Memory Categories in the admin area: add, rename, edit description, toggle "always include", archive and restore. Categories can never be deleted. Archived categories keep their existing Memory Items but are not offered for new items or category picking. Post-conversation processing and memory retrieval always read the current list.

## Acceptance criteria

- [ ] Admins can add, rename, edit description, toggle "always include", archive and restore Memory Categories; there is no delete
- [ ] An archived category's existing Memory Items remain visible to the User
- [ ] Post-conversation processing never assigns new items to an archived category
- [ ] A newly added category is used on the next post-conversation processing and retrieval, with no restart
- [ ] Seam 1 and seam 2 tests cover archive behaviour and new-category pickup
- [ ] Seam 3 tests cover the admin Memory Categories page
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/mvp/issues/04-admin-area-foundation.md`
- `.scratch/mvp/issues/06-user-memory.md`
