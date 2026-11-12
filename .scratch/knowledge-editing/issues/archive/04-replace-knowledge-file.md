# 04 — Replace a Knowledge Document's file

Status: completed

## Parent

`.scratch/knowledge-editing/PRD.md`

## What to build

On a document's page, an Admin replaces the document's file with a new text, Markdown or PDF file. The document keeps its ID, details and added date, takes the new file's type, becomes Pending, and has the new file read and re-indexed in the background. Replies then use the new version and never the old. A replacement that can't be read fails with the same reasons as an upload, and the same file rules apply (type, not empty, up to 20 MB). Replacing the file clears the "Edited" marker.

## Acceptance criteria

- [x] `PUT /api/admin/knowledge-documents/{id}/file` (multipart `file`) keeps ID, details and added date, stores the new file and type, clears `text_edited`, returns the Pending document and reads and indexes in the background; 422 for wrong type, empty or over 20 MB; 404 if missing; 403 for non-Admins
- [x] After it is Ready, the next reply contains the new file's text and not the old
- [x] An unreadable replacement (scanned, broken or not UTF-8) shows Failed with the usual reason
- [x] The document page has Replace file with the same drop area and rules as upload, and shows the backend's reason when refused
- [x] Seam 1 tests cover all of the above
- [x] Seam 3 tests cover replacing the file and a refusal reason
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/knowledge-editing/issues/03-edit-knowledge-text.md`

## Comments

**2026-11-12 — started on branch `feat/ke-04-replace-file`.** Plan: `PUT /api/admin/knowledge-documents/{id}/file` (multipart) checks the file like upload, stores the new file and type, clears the saved text and the Edited flag, makes the document Pending and runs Read then Index in the background (clearing the text is what makes `ingest` read the new file). Dashboard: a Replace file card on the document page sharing the upload form's drop area.

**2026-11-12 — implemented, reviewed and verified.** Commits `00a1e6a`, `1a1adb9` on `feat/ke-04-replace-file`.

Done and verified: every acceptance criterion. `make check` green (Python 184, web 172; ruff, ruff format, mypy, eslint, prettier, tsc clean). Running stack, signed-in Admin in Chrome for Testing, on "Mindful breathing" (left edited by issue 03's run): Replace file asked first because the text was edited, then the document became Ready as "PDF · river.pdf" with the PDF's text, the Edited marker gone, the same title, source, tradition and added date; a broken PDF replacement showed "Failed: Couldn’t read this PDF."; a .docx was refused with "Upload a text (.txt), Markdown (.md) or PDF (.pdf) file." and an empty file with "The file is empty."; no sideways scroll at 390px. Replacing it with the original seed file restored it exactly: same ID and `created_at`, Markdown, Ready, `text_edited` false, text checksum equal to `src/companion/seed/knowledge/mindful-breathing.md`, 2 chunks.

Decisions: replacing a file clears the saved text and Edited flag (so `ingest` reads the new file) and removes the old chunks at once. Replacing is refused (409) while the last file is still being read, the same rule as saving text, so an older read can't save its text over the new file's. The Replace file card shares the upload form's drop area (`KnowledgeFileDrop`) and asks first when the text was edited. Both upload and replace build the file with `to_knowledge_file`.

Caveats:
- "The next reply contains the new file's text and not the old" is shown by seam 1 (`test_replacing_a_file_keeps_the_document_and_uses_the_new_text`), not in the running app: that needs a real Telegram chat.
- Follow-ups from review, not done: `KnowledgeUpload` could hold a `KnowledgeFile`; the flash message markup is repeated in five components.

Evidence: seam 1 `tests/test_knowledge.py` (`test_replacing_a_file_keeps_the_document_and_uses_the_new_text`, `test_an_unreadable_replacement_fails_with_the_usual_reason`, `test_a_file_cant_be_replaced_while_the_last_one_is_still_being_read`, `test_a_failed_replacement_leaves_none_of_the_old_text_behind`, `test_replacement_files_follow_the_upload_rules`, `test_only_admins_can_manage_knowledge`); seam 3 `web/src/components/KnowledgeDocumentView.test.tsx` (replacing an edited document's file, refusal reason), `KnowledgeLibrary.test.tsx` (upload still works through the shared drop area).

## Completion

- Completed: 2026-11-12
- Commit: 00a1e6a "Replace a Knowledge document's file: PUT file route, Replace file card sharing the upload drop area (knowledge-editing issue 04)"; review fixes 1a1adb9 "Replace file review fixes: no replacing while the last file is being read, old chunks removed at once, shared upload file helper" (merged from `feat/ke-04-replace-file`)
- Archive commit: 23bb53a "Knowledge editing issue 04 done: archive issue, replacing a file in glossary"
- Merge commit: ab2f560 "Merge knowledge-editing issue 04: replace a Knowledge Document's file"
