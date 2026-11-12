# 02 — Edit a Knowledge Document's details

Status: completed

## Parent

`.scratch/knowledge-editing/PRD.md`

## What to build

On a document's page, an Admin edits its title, source / author and tradition and saves. The change takes effect straight away, with no re-index: the list and the document page show the new details, and the next reply that draws on the document cites the new title and source. Blank values are refused with a plain message, as on upload.

## Acceptance criteria

- [x] `PATCH /api/admin/knowledge-documents/{id}` with any of `title`, `source`, `tradition` saves them trimmed; 422 for a blank field; 404 if missing; 403 for non-Admins
- [x] The document's status and chunks are untouched by a details edit
- [x] The next reply that draws on the document cites the new title and source
- [x] The document page has a details form with Save, shows a success message, and shows the backend's reason when refused
- [x] Seam 1 tests cover saving, blank refused, 404, 403 and the reply citing the new details
- [x] Seam 3 tests cover the details form
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/knowledge-editing/issues/01-view-knowledge-document.md`

## Comments

**2026-11-12 — started on branch `feat/ke-02-edit-details`.** Plan: `PATCH /api/admin/knowledge-documents/{id}` with optional title / source / tradition, trimmed and checked like upload, no status or chunk change; returns the document with its text so the page can show it as is. Repository gains `update_details`. Document page's Details card becomes a form with Save.

**2026-11-12 — implemented, reviewed and verified.** Commits `39a9c27`, `a670bcb` on `feat/ke-02-edit-details`.

Done and verified: every acceptance criterion. `make check` green (Python 172, web 152; ruff, ruff format, mypy, eslint, prettier, tsc clean). Running stack, signed-in Admin in Chrome for Testing: on "Self-compassion" the title (typed with spaces), source and tradition were saved; the heading, the form (trimmed) and the Knowledge list showed the new details at once; status stayed Ready and the chunk IDs were identical before and after; Save is disabled while nothing changed or a field is blank; through the API a blank source got 422 "A document needs a source or author." and a missing document 404; no sideways scroll at 390px. Details were restored afterwards.

Decisions: PATCH returns the document with its text, so the page can show it as is. A field left out or sent as null is kept. Blank checks are shared with upload (`required_detail`). The tradition list is shared with the upload form; a document whose tradition isn't in the list keeps it as a choice.

Caveats:
- "The next reply cites the new title and source" is shown by seam 1 (`test_the_next_reply_cites_a_documents_new_details`), not in the running app: that needs a real Telegram chat.
- As on upload, a blank title or source disables Save rather than showing a message.

Evidence: seam 1 `tests/test_knowledge.py` (`test_an_admin_edits_a_documents_details_without_reindexing`, `test_editing_only_some_details_keeps_the_others`, `test_blank_details_are_refused_and_a_missing_document_is_not_found`, `test_the_next_reply_cites_a_documents_new_details`, `test_only_admins_can_manage_knowledge`); seam 3 `web/src/components/KnowledgeDocumentView.test.tsx` (details shown, saved, blank and refusal).

## Completion

- Completed: 2026-11-12
- Commit: 39a9c27 "Edit a Knowledge document's details: PATCH route, details form on the document page (knowledge-editing issue 02)"; review fixes a670bcb "Knowledge details review fixes: form shows the saved document, fixed details as a list, simpler update" (merged from `feat/ke-02-edit-details`)
- Archive commit: 2415fc2 "Knowledge editing issue 02 done: archive issue, editable details in glossary"
- Merge commit: 5a2c468 "Merge knowledge-editing issue 02: edit a Knowledge Document's details"
