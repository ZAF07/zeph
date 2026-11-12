# 03 — Edit a Knowledge Document's text

Status: ready-for-agent

## Parent

`.scratch/knowledge-editing/PRD.md`

## What to build

On a document's page, an Admin edits the text the Companion draws on and saves it. The document becomes Pending, is re-indexed from the new text in the background, and becomes Ready (or Failed with the reason). Until it is Ready it is not used in replies; once Ready, replies use the new wording and never the old. The document is marked "Edited" so Admins know it no longer matches its file word for word.

This is also how a Failed document gets rescued: an Admin can type or paste the text of a scanned PDF, and the document becomes Ready.

Retry follows one rule from now on: a document with saved text is only re-indexed (so edited text is never overwritten by re-reading the file); a document with no saved text is read and then indexed. The start-up step that finishes Pending documents follows the same rule, so an edit interrupted by a restart is finished on the next start.

The page warns before leaving with unsaved text changes.

## Acceptance criteria

- [ ] `PUT /api/admin/knowledge-documents/{id}/text` with `{text}` saves the trimmed text, marks it edited, returns the Pending document and re-indexes in the background; 422 for blank text; 404 if missing; 403 for non-Admins
- [ ] After the re-index the document is Ready and the next reply contains the new wording and not the old
- [ ] Editing the text of a Failed scanned-PDF document makes it Ready
- [ ] A failed re-index of edited text shows Failed with the reason; Retry re-indexes the edited text, not the original file
- [ ] A document left Pending by an interrupted text edit is finished on start-up without losing the edit
- [ ] The document page has an editable text area with Save text (saying it will re-index), shows Pending then Ready, shows the "Edited" marker, and warns before leaving with unsaved changes
- [ ] Seam 1 tests cover all of the above
- [ ] Seam 3 tests cover saving text, Pending → Ready, the Edited marker and a refusal reason
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

- `.scratch/knowledge-editing/issues/01-view-knowledge-document.md`
