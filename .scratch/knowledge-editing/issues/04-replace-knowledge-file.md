# 04 — Replace a Knowledge Document's file

Status: ready-for-agent

## Parent

`.scratch/knowledge-editing/PRD.md`

## What to build

On a document's page, an Admin replaces the document's file with a new text, Markdown or PDF file. The document keeps its ID, details and added date, takes the new file's type, becomes Pending, and has the new file read and re-indexed in the background. Replies then use the new version and never the old. A replacement that can't be read fails with the same reasons as an upload, and the same file rules apply (type, not empty, up to 20 MB). Replacing the file clears the "Edited" marker.

## Acceptance criteria

- [ ] `PUT /api/admin/knowledge-documents/{id}/file` (multipart `file`) keeps ID, details and added date, stores the new file and type, clears `text_edited`, returns the Pending document and reads and indexes in the background; 422 for wrong type, empty or over 20 MB; 404 if missing; 403 for non-Admins
- [ ] After it is Ready, the next reply contains the new file's text and not the old
- [ ] An unreadable replacement (scanned, broken or not UTF-8) shows Failed with the usual reason
- [ ] The document page has Replace file with the same drop area and rules as upload, and shows the backend's reason when refused
- [ ] Seam 1 tests cover all of the above
- [ ] Seam 3 tests cover replacing the file and a refusal reason
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/knowledge-editing/issues/03-edit-knowledge-text.md`

## Comments

**2026-11-12 — started on branch `feat/ke-04-replace-file`.** Plan: `PUT /api/admin/knowledge-documents/{id}/file` (multipart) checks the file like upload, stores the new file and type, clears the saved text and the Edited flag, makes the document Pending and runs Read then Index in the background (clearing the text is what makes `ingest` read the new file). Dashboard: a Replace file card on the document page sharing the upload form's drop area.
