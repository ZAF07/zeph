# 03 — Edit a Knowledge Document's text

Status: completed

## Parent

`.scratch/knowledge-editing/PRD.md`

## What to build

On a document's page, an Admin edits the text the Companion draws on and saves it. The document becomes Pending, is re-indexed from the new text in the background, and becomes Ready (or Failed with the reason). Until it is Ready it is not used in replies; once Ready, replies use the new wording and never the old. The document is marked "Edited" so Admins know it no longer matches its file word for word.

This is also how a Failed document gets rescued: an Admin can type or paste the text of a scanned PDF, and the document becomes Ready.

Retry follows one rule from now on: a document with saved text is only re-indexed (so edited text is never overwritten by re-reading the file); a document with no saved text is read and then indexed. The start-up step that finishes Pending documents follows the same rule, so an edit interrupted by a restart is finished on the next start.

Editing happens in the Knowledge text editor from issue 01, now editable — a professional editor, not a plain text box (see the PRD): formatting toolbar, find & replace, undo / redo, Edit / Preview / Split, word count, an "Unsaved changes" indicator, Ctrl/⌘+S, Discard changes, and "Review changes" (a comparison of saved and edited text) before "Save and re-index". The page warns before leaving with unsaved text changes.

## Acceptance criteria

- [x] `PUT /api/admin/knowledge-documents/{id}/text` with `{text}` saves the trimmed text, marks it edited, returns the Pending document and re-indexes in the background; 422 for blank text; 404 if missing; 403 for non-Admins
- [x] After the re-index the document is Ready and the next reply contains the new wording and not the old
- [x] Editing the text of a Failed scanned-PDF document makes it Ready
- [x] A failed re-index of edited text shows Failed with the reason; Retry re-indexes the edited text, not the original file
- [x] A document left Pending by an interrupted text edit is finished on start-up without losing the edit
- [x] The editor is editable: toolbar (Heading, Bold, Italic, Quote, lists, Undo, Redo, Find & replace) with tooltips and shortcuts, live word / character count, "Unsaved changes" / "Saved" state
- [x] Ctrl/⌘+S and "Save text" open "Review changes" (additions and removals highlighted) before "Save and re-index"; "Discard changes" asks first; leaving with unsaved changes warns
- [x] After saving, the page shows Pending then Ready and the "Edited" marker
- [x] The editing experience is checked in a browser at desktop and 390px widths and looks professional, consistent with the Zeph admin screens
- [x] Seam 1 tests cover all of the above
- [x] Seam 3 tests cover editing and saving through the editor (toolbar formatting, Unsaved indicator, Ctrl/⌘+S, Review changes, Discard), Pending → Ready, the Edited marker and a refusal reason
- [x] `make check` passes
- [x] Verified in the running app via `/run`

## Blocked by

- `.scratch/knowledge-editing/issues/01-view-knowledge-document.md`

## Comments

**2026-11-12 — started on branch `feat/ke-03-edit-text`.** Plan: `PUT /api/admin/knowledge-documents/{id}/text` saves the trimmed text as edited, makes the document Pending and indexes in the background (Index only: issue 01's `ingest` already skips Read when text is saved, which is also the Retry and start-up rule). Dashboard: the Knowledge text editor becomes editable — Markdown formatting as pure functions behind the CodeMirror adapter, toolbar with shortcuts, undo / redo, find & replace, Unsaved / Saved, Ctrl/⌘+S, Discard, Review changes (word diff with `diff`), warning before leaving.

**2026-11-12 — implemented, reviewed and verified.** Commits `25b5bf8`, `a8e76ff` on `feat/ke-03-edit-text`.

Done and verified: every acceptance criterion. `make check` green (Python 179, web 170; ruff, ruff format, mypy, eslint, prettier, tsc clean). Running stack, signed-in Admin in Chrome for Testing, on "Mindful breathing": typing showed "Unsaved changes" and a live count; Bold wrapped the selected line and showed its tooltip "Bold Ctrl/⌘ B"; Undo and Redo worked; Find & replace "Replace All" changed "test line" to "check line"; Ctrl/⌘+S opened Review changes ("6 words added · 0 words removed", the added line highlighted); Save and re-index showed the saved message, the Edited marker, then "Saved · Ready"; the database had `text_edited` true and new chunks; Discard asked first and restored the text; following "← Knowledge" with unsaved changes asked first. At 390px: no sideways scroll, the toolbar wraps, Split is hidden and the review dialog fits. A scanned PDF showed an empty editor with "No text could be read from this file. Type or paste its text…"; typed text saved it to Ready, still a PDF. An edit left Pending in the database (edited text, no chunks yet) was finished by a backend restart with the edited text kept. Desktop and phone screenshots checked: consistent with the Zeph admin screens.

Decisions: `PUT .../text` returns the pending document with its text; Index only, since saved text is never re-read from the file (issue 01's rule, also used by Retry and start-up). An indexing run whose text was replaced meanwhile stops before swapping chunks, so the newest edit always wins. Saving text is refused (409) while a document's file is still being read. Formatting is pure functions (`web/src/lib/markdown-formatting.ts`) applied through the CodeMirror adapter; shortcuts: Heading Ctrl/⌘ Alt 2, Bold Ctrl/⌘ B, Italic Ctrl/⌘ I, Quote Ctrl/⌘ Shift 9, lists Ctrl/⌘ Shift 8 / 7, Undo / Redo Ctrl/⌘ Z / Shift Z, Find & replace Ctrl/⌘ F. Review changes is a word comparison (`diff` package) with long unchanged stretches shortened. The details form and text section no longer share a React `key` (two siblings had the same key, which lost the details form's state).

Caveats:
- "The next reply contains the new wording and not the old" and "Retry after a failed re-index keeps the edited text" are shown by seam 1, not in the running app (they need a real Telegram chat and a failing embedder).
- The leave warning covers reload, closing and links, not the browser Back button.
- Saving text writes the text and the Pending status in two steps.
- "Mindful breathing" was left edited by this run; issue 04's run restores it by replacing its file with the original.
- In jsdom, typing letter by letter into CodeMirror is unreliable under load, so seam 3 tests paste text instead.

Evidence: seam 1 `tests/test_knowledge.py` (`test_editing_a_documents_text_reindexes_it_from_the_new_wording`, `test_blank_text_is_refused_and_a_missing_document_is_not_found`, `test_text_cant_be_saved_while_the_file_is_still_being_read`, `test_typing_the_text_of_a_scanned_pdf_makes_it_ready`, `test_retrying_a_failed_reindex_keeps_the_edited_text`, `test_only_admins_can_manage_knowledge`), `tests/test_knowledge_seed.py` (`test_a_text_edit_left_pending_by_a_restart_is_finished_on_the_next_start`), `tests/test_knowledge_reindex.py`; seam 3 `web/src/components/KnowledgeDocumentView.test.tsx` (editing, review, Ctrl/⌘+S, toolbar, undo / redo, discard, leave warning, refusal, Pending → Ready, Edited), `web/src/lib/markdown-formatting.test.ts`, `web/src/lib/text-changes.test.ts`.

## Completion

- Completed: 2026-11-12
- Commit: 25b5bf8 "Edit a Knowledge document's text: PUT text route, editable text editor with formatting toolbar, review changes, discard and leave warning (knowledge-editing issue 03)"; review fixes a8e76ff "Knowledge text review fixes: an older re-index never overwrites a newer edit, no text saves while the file is being read, rule-held formatting prefixes" (merged from `feat/ke-03-edit-text`)
