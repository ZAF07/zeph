# 02 — Edit a Knowledge Document's details

Status: ready-for-agent

## Parent

`.scratch/knowledge-editing/PRD.md`

## What to build

On a document's page, an Admin edits its title, source / author and tradition and saves. The change takes effect straight away, with no re-index: the list and the document page show the new details, and the next reply that draws on the document cites the new title and source. Blank values are refused with a plain message, as on upload.

## Acceptance criteria

- [ ] `PATCH /api/admin/knowledge-documents/{id}` with any of `title`, `source`, `tradition` saves them trimmed; 422 for a blank field; 404 if missing; 403 for non-Admins
- [ ] The document's status and chunks are untouched by a details edit
- [ ] The next reply that draws on the document cites the new title and source
- [ ] The document page has a details form with Save, shows a success message, and shows the backend's reason when refused
- [ ] Seam 1 tests cover saving, blank refused, 404, 403 and the reply citing the new details
- [ ] Seam 3 tests cover the details form
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/knowledge-editing/issues/01-view-knowledge-document.md`

## Comments

**2026-11-12 — started on branch `feat/ke-02-edit-details`.** Plan: `PATCH /api/admin/knowledge-documents/{id}` with optional title / source / tradition, trimmed and checked like upload, no status or chunk change; returns the document with its text so the page can show it as is. Repository gains `update_details`. Document page's Details card becomes a form with Save.
