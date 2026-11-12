# 01 — View a Knowledge Document

Status: completed

## Parent

`.scratch/knowledge-editing/PRD.md`

## What to build

An Admin opens any Knowledge Document from the Knowledge table and sees its own page: title, source / author, tradition, type, status (with the failure reason when Failed), when it was added, and the full text the Companion draws on.

To make that possible, the text read from a document's file is now saved on the document, and indexing works from that saved text. Reading and indexing become two steps (Read, then Index) with the same failure reasons as today. Documents uploaded before this change get their text read from their stored file on start-up, without re-indexing.

The text is shown in the Knowledge text editor (see the PRD) in read-only mode: line numbers, soft wrap, Markdown highlighting, find, Edit / Preview / Split views and word count, styled to Zeph. This issue builds that editor component; issue 03 turns on editing.

The page also offers Retry (when Failed) and Delete (confirm, then back to the list), keeps checking while the document is Pending, and has loading, not-found and error states. The list endpoint stays without text.

Build order: (1) backend and seam 1 tests, which fix the API contract; (2) the Dashboard page and seam 3 tests with a mocked API client; (3) `/run` end to end.

## Acceptance criteria

- [x] Uploading a text, Markdown or PDF document saves the text read from it; chunks are made from that saved text
- [x] `GET /api/admin/knowledge-documents/{id}` returns the document's details, `text` (null if never read) and `text_edited` (false for now); 404 if missing; 403 for non-Admins
- [x] Failure reasons are unchanged (unreadable PDF, scanned PDF, not UTF-8, could not index)
- [x] On start-up, documents with no saved text whose file can be read get their text saved, without re-indexing; the starter documents are viewable
- [x] Each title in the Knowledge table links to the document's page at `/admin/knowledge/<id>`
- [x] The text is shown in the read-only Knowledge text editor (CodeMirror 6, Zeph-styled): line numbers, soft wrap, Markdown highlighting, find, Preview / Split, word and character count; usable by keyboard and screen reader; no sideways scroll at 390px; smooth on the ~42,000-character starter document
- [x] The page shows details, status pill, failure reason, Retry when Failed, and Delete with confirmation that returns to the list
- [x] The page checks again while Pending and shows not-found and load-error states
- [x] Seam 1 tests cover viewing txt/Markdown/PDF text, 404, 403 and the start-up text fill
- [x] Seam 3 tests cover the document page (including read-only editor: text shown, Preview renders Markdown, word count, no editing controls) and the link from the table
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

None - can start immediately

## Comments

**2026-11-12 — started on branch `feat/ke-01-view-document`.** Plan: migration 0008 adds `text` and `text_edited`; ingestion splits into Read (extract, save text) and Index (chunk the saved text); `ingest` skips Read when text is saved; prestart fills text for older documents; `GET /api/admin/knowledge-documents/{id}`; `/admin/knowledge/[id]` page with a CodeMirror 6 `KnowledgeTextEditor` (read-only here) and `react-markdown` Preview.

**2026-11-12 — implemented, reviewed and verified.** Commits `2f399ab`, `93f5122` on `feat/ke-01-view-document`.

Done and verified: every acceptance criterion. `make check` green (Python 168, web 150; ruff, ruff format, mypy, eslint, prettier, tsc clean). Running stack (Docker, real fastembed and pgvector): migration 0008 ran on the existing database; on start-up all 6 starter documents got their text (Meditations 42,090 characters) and the chunk IDs were identical before and after (no re-index). Signed-in browser check (Chrome for Testing, temporary Clerk test user approved by the owner, to be deleted after issue 04): titles link to `/admin/knowledge/<id>`; sidebar keeps Knowledge marked; details, Ready pill and the read-only editor show (7,638 words · 42,090 characters, typing changes nothing, `aria-readonly`); Find highlights matches with no replace field; Split and Preview render the Markdown; at 390px Split is hidden and there is no sideways scroll; a scanned PDF's page shows "Failed: Scanned PDF — no text found" and "No text yet", Retry keeps it failed, Delete asks and returns to the list; its old address then shows "This document no longer exists". Keyboard Tab reaches the editor and shows a blue focus ring.

Decisions: `ingest` skips Read when the document has saved text, so issue 03's Retry rule is already in place. Saved text is trimmed. The list response gains `text_edited`; it stays without `text`. Editor is CodeMirror 6 behind `CodeMirrorEditor` (value, onChange, readOnly, onSave); Preview uses `react-markdown` with raw HTML left out. In read-only mode the Edit view is labelled "Text". The admin sidebar link stays marked on pages under it.

Caveats:
- If Split is chosen and the window then narrows, both panes stack (no tab is shown as active).
- An unrelated working-tree change to `docker-compose.yml` (Postgres on host port 5432) was swept into the first commit by mistake, then removed from it; it is left uncommitted for the owner.

Evidence: seam 1 `tests/test_knowledge.py` (`test_a_document_shows_the_text_read_from_its_file`, `test_markdown_and_pdf_documents_show_their_text`, `test_a_document_whose_file_had_no_text_shows_no_text`, `test_viewing_a_missing_document_is_not_found`, `test_only_admins_can_manage_knowledge`), `tests/test_knowledge_seed.py` (`test_every_starter_document_has_its_text`, `test_documents_from_before_text_was_saved_get_it_on_start_without_reindexing`); seam 3 `web/src/components/KnowledgeDocumentView.test.tsx` (8), `KnowledgeTextEditor.test.tsx` (3), `KnowledgeLibrary.test.tsx` (link), `SidebarNav.test.tsx`, `web/src/lib/text-stats.test.ts`.

## Completion

- Completed: 2026-11-12
- Commit: 2f399ab "Knowledge document page: saved text, Read then Index, start-up text fill, read-only text editor (knowledge-editing issue 01)"; review fixes 93f5122 "Knowledge document page review fixes: status labels as a record, visible editor focus ring, simpler empty-text check" (merged from `feat/ke-01-view-document`)
