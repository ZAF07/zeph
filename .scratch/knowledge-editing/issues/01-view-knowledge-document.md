# 01 — View a Knowledge Document

Status: ready-for-agent

## Parent

`.scratch/knowledge-editing/PRD.md`

## What to build

An Admin opens any Knowledge Document from the Knowledge table and sees its own page: title, source / author, tradition, type, status (with the failure reason when Failed), when it was added, and the full text the Companion draws on.

To make that possible, the text read from a document's file is now saved on the document, and indexing works from that saved text. Reading and indexing become two steps (Read, then Index) with the same failure reasons as today. Documents uploaded before this change get their text read from their stored file on start-up, without re-indexing.

The text is shown in the Knowledge text editor (see the PRD) in read-only mode: line numbers, soft wrap, Markdown highlighting, find, Edit / Preview / Split views and word count, styled to Zeph. This issue builds that editor component; issue 03 turns on editing.

The page also offers Retry (when Failed) and Delete (confirm, then back to the list), keeps checking while the document is Pending, and has loading, not-found and error states. The list endpoint stays without text.

Build order: (1) backend and seam 1 tests, which fix the API contract; (2) the Dashboard page and seam 3 tests with a mocked API client; (3) `/run` end to end.

## Acceptance criteria

- [ ] Uploading a text, Markdown or PDF document saves the text read from it; chunks are made from that saved text
- [ ] `GET /api/admin/knowledge-documents/{id}` returns the document's details, `text` (null if never read) and `text_edited` (false for now); 404 if missing; 403 for non-Admins
- [ ] Failure reasons are unchanged (unreadable PDF, scanned PDF, not UTF-8, could not index)
- [ ] On start-up, documents with no saved text whose file can be read get their text saved, without re-indexing; the starter documents are viewable
- [ ] Each title in the Knowledge table links to the document's page at `/admin/knowledge/<id>`
- [ ] The text is shown in the read-only Knowledge text editor (CodeMirror 6, Zeph-styled): line numbers, soft wrap, Markdown highlighting, find, Preview / Split, word and character count; usable by keyboard and screen reader; no sideways scroll at 390px; smooth on the ~42,000-character starter document
- [ ] The page shows details, status pill, failure reason, Retry when Failed, and Delete with confirmation that returns to the list
- [ ] The page checks again while Pending and shows not-found and load-error states
- [ ] Seam 1 tests cover viewing txt/Markdown/PDF text, 404, 403 and the start-up text fill
- [ ] Seam 3 tests cover the document page (including read-only editor: text shown, Preview renders Markdown, word count, no editing controls) and the link from the table
- [ ] `make check` passes
- [ ] Verified in the running app via `/run`

## Blocked by

None - can start immediately

## Comments

**2026-11-12 — started on branch `feat/ke-01-view-document`.** Plan: migration 0008 adds `text` and `text_edited`; ingestion splits into Read (extract, save text) and Index (chunk the saved text); `ingest` skips Read when text is saved; prestart fills text for older documents; `GET /api/admin/knowledge-documents/{id}`; `/admin/knowledge/[id]` page with a CodeMirror 6 `KnowledgeTextEditor` (read-only here) and `react-markdown` Preview.
